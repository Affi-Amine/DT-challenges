"""
LLM Resolver Module
Handles ambiguous cases and validation using Large Language Model API.
Supports both OpenAI and Google Gemini APIs.
"""

import os
import yaml
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None
    OpenAI = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class ResolutionType(Enum):
    """Types of resolution tasks."""
    SPEAKER_IDENTIFICATION = "speaker_identification"
    BOUNDARY_DETECTION = "boundary_detection"
    AMBIGUITY_RESOLUTION = "ambiguity_resolution"
    VALIDATION = "validation"


@dataclass
class LLMRequest:
    """Represents a request to the LLM."""
    task_type: ResolutionType
    context: str
    question: str
    options: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """Represents a response from the LLM."""
    success: bool
    result: str
    confidence: float
    reasoning: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMResolver:
    """
    LLM-based resolver for ambiguous transcript cases.
    
    Supports both OpenAI and Google Gemini APIs for resolving complex speaker identification,
    boundary detection, and validation tasks that regex cannot handle.
    """
    
    def __init__(self, config_path: Optional[str] = None, api_key: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize the LLM resolver.
        
        Args:
            config_path: Path to prompts configuration file
            api_key: API key (if not provided, will use environment variable)
            provider: LLM provider ('openai' or 'gemini', defaults to env LLM_PROVIDER)
        """
        self.config_path = config_path or self._get_default_config_path()
        self.prompts = {}
        self.client = None
        self.provider = provider or os.getenv('LLM_PROVIDER', 'openai')
        
        # Initialize the appropriate client
        self._initialize_client(api_key)
        
        # Load prompt templates
        self._load_prompts()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent / "config" / "prompts.yaml")
    
    def _initialize_client(self, api_key: Optional[str] = None):
        """Initialize the appropriate LLM client based on provider."""
        if self.provider == 'gemini':
            self._initialize_gemini_client(api_key)
        elif self.provider == 'openai':
            self._initialize_openai_client(api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _initialize_openai_client(self, api_key: Optional[str] = None):
        """Initialize OpenAI client."""
        if not openai or not OpenAI:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        
        # Get API key from parameter, environment, or .env file
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            # Try to load from .env file
            env_path = Path(__file__).parent.parent / '.env'
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.startswith('OPENAI_API_KEY='):
                            api_key = line.split('=', 1)[1].strip().strip('"\'')
                            break
        
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or provide api_key parameter.")
        
        self.client = OpenAI(api_key=api_key)
    
    def _initialize_gemini_client(self, api_key: Optional[str] = None):
        """Initialize Gemini client."""
        if not genai:
            raise ImportError("Google Generative AI library not installed. Run: pip install google-generativeai")
        
        # Get API key from parameter, environment, or .env file
        if not api_key:
            api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            # Try to load from .env file
            env_path = Path(__file__).parent.parent / '.env'
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.startswith('GEMINI_API_KEY='):
                            api_key = line.split('=', 1)[1].strip().strip('"\'')
                            break
        
        if not api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable or provide api_key parameter.")
        
        genai.configure(api_key=api_key)
        model_name = os.getenv('GEMINI_MODEL', 'gemini-pro')
        self.client = genai.GenerativeModel(model_name)
    
    def _load_prompts(self):
        """Load prompt templates from configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.prompts = config.get('prompts', {})
            
        except FileNotFoundError:
            # Use default prompts if config not found
            self._set_default_prompts()
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in prompts configuration: {e}")
    
    def _set_default_prompts(self):
        """Set default prompt templates."""
        self.prompts = {
            'speaker_identification': {
                'system': "You are an expert at analyzing meeting transcripts and identifying speakers.",
                'user': "Analyze this transcript segment and identify who is speaking:\n\n{context}\n\nQuestion: {question}\n\nProvide your answer in JSON format with 'speaker', 'confidence' (0-1), and 'reasoning' fields."
            },
            'boundary_detection': {
                'system': "You are an expert at detecting speaker boundaries in transcripts.",
                'user': "Analyze this transcript segment and determine where one speaker ends and another begins:\n\n{context}\n\nQuestion: {question}\n\nProvide your answer in JSON format with 'boundaries', 'confidence' (0-1), and 'reasoning' fields."
            },
            'validation': {
                'system': "You are an expert at validating transcript formatting and speaker identification.",
                'user': "Validate this transcript segment for accuracy and formatting:\n\n{context}\n\nQuestion: {question}\n\nProvide your answer in JSON format with 'is_valid', 'issues', 'confidence' (0-1), and 'reasoning' fields."
            }
        }
    
    async def resolve_speaker_identification(self, context: str, ambiguous_text: str, 
                                           possible_speakers: Optional[List[str]] = None) -> LLMResponse:
        """
        Resolve ambiguous speaker identification.
        
        Args:
            context: Surrounding context text
            ambiguous_text: The ambiguous text segment
            possible_speakers: List of possible speaker names
            
        Returns:
            LLM response with speaker identification
        """
        question = f"Who is speaking in this text: '{ambiguous_text}'"
        if possible_speakers:
            question += f"\n\nPossible speakers: {', '.join(possible_speakers)}"
        
        request = LLMRequest(
            task_type=ResolutionType.SPEAKER_IDENTIFICATION,
            context=context,
            question=question,
            options=possible_speakers
        )
        
        return await self._make_llm_request(request)
    
    async def resolve_boundary_detection(self, context: str, mixed_text: str) -> LLMResponse:
        """
        Detect speaker boundaries in mixed text.
        
        Args:
            context: Surrounding context
            mixed_text: Text with multiple speakers
            
        Returns:
            LLM response with boundary detection
        """
        question = f"Where do speaker changes occur in this text: '{mixed_text}'"
        
        request = LLMRequest(
            task_type=ResolutionType.BOUNDARY_DETECTION,
            context=context,
            question=question
        )
        
        return await self._make_llm_request(request)
    
    async def validate_transcript_segment(self, transcript_segment: str, 
                                        expected_format: str = "Speaker: Statement") -> LLMResponse:
        """
        Validate a transcript segment for accuracy and formatting.
        
        Args:
            transcript_segment: Segment to validate
            expected_format: Expected format description
            
        Returns:
            LLM response with validation results
        """
        question = f"Is this transcript segment properly formatted according to '{expected_format}' format? Identify any issues."
        
        request = LLMRequest(
            task_type=ResolutionType.VALIDATION,
            context=transcript_segment,
            question=question
        )
        
        return await self._make_llm_request(request)
    
    async def resolve_ambiguous_cases(self, cases: List[Dict[str, Any]]) -> List[LLMResponse]:
        """
        Resolve multiple ambiguous cases in batch.
        
        Args:
            cases: List of cases, each with 'context', 'question', and 'type'
            
        Returns:
            List of LLM responses
        """
        tasks = []
        
        for case in cases:
            request = LLMRequest(
                task_type=ResolutionType(case.get('type', 'ambiguity_resolution')),
                context=case['context'],
                question=case['question'],
                options=case.get('options'),
                metadata=case.get('metadata')
            )
            tasks.append(self._make_llm_request(request))
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _make_llm_request(self, request: LLMRequest) -> LLMResponse:
        """
        Make a request to the LLM API.
        
        Args:
            request: LLM request object
            
        Returns:
            LLM response object
        """
        try:
            # Get appropriate prompt template
            prompt_key = request.task_type.value
            if prompt_key not in self.prompts:
                prompt_key = 'speaker_identification'  # Fallback
            
            prompt_template = self.prompts[prompt_key]
            
            # Format the prompt
            system_message = prompt_template['system']
            user_message = prompt_template['user'].format(
                context=request.context,
                question=request.question
            )
            
            if self.provider == 'openai':
                return await self._make_openai_request(system_message, user_message)
            elif self.provider == 'gemini':
                return await self._make_gemini_request(system_message, user_message)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        
        except Exception as e:
            return LLMResponse(
                success=False,
                result="",
                confidence=0.0,
                reasoning="",
                error=str(e)
            )
    
    async def _make_openai_request(self, system_message: str, user_message: str) -> LLMResponse:
        """Make a request to OpenAI API."""
        # Make API call
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '500'))
        )
        
        # Parse response
        content = response.choices[0].message.content
        return self._parse_llm_response(content)
    
    async def _make_gemini_request(self, system_message: str, user_message: str) -> LLMResponse:
        """Make a request to Gemini API."""
        # Combine system and user messages for Gemini
        combined_prompt = f"{system_message}\n\n{user_message}"
        
        # Make API call
        response = await asyncio.to_thread(
            self.client.generate_content,
            combined_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=float(os.getenv('GEMINI_TEMPERATURE', '0.1')),
                max_output_tokens=int(os.getenv('GEMINI_MAX_TOKENS', '500'))
            )
        )
        
        # Parse response
        content = response.text
        return self._parse_llm_response(content)
    
    def _parse_llm_response(self, content: str) -> LLMResponse:
        """Parse LLM response content into structured format."""
        # Try to parse as JSON
        try:
            parsed_response = json.loads(content)
            return LLMResponse(
                success=True,
                result=parsed_response.get('speaker', parsed_response.get('result', content)),
                confidence=float(parsed_response.get('confidence', 0.8)),
                reasoning=parsed_response.get('reasoning', ''),
                metadata=parsed_response
            )
        except json.JSONDecodeError:
            # Fallback to plain text response
            return LLMResponse(
                success=True,
                result=content,
                confidence=0.7,  # Lower confidence for non-JSON responses
                reasoning="Plain text response",
                metadata={'raw_response': content}
            )
    
    def resolve_speaker_identification_sync(self, context: str, ambiguous_text: str, 
                                          possible_speakers: Optional[List[str]] = None) -> LLMResponse:
        """Synchronous version of resolve_speaker_identification."""
        return asyncio.run(self.resolve_speaker_identification(context, ambiguous_text, possible_speakers))
    
    def resolve_boundary_detection_sync(self, context: str, mixed_text: str) -> LLMResponse:
        """Synchronous version of resolve_boundary_detection."""
        return asyncio.run(self.resolve_boundary_detection(context, mixed_text))
    
    def validate_transcript_segment_sync(self, transcript_segment: str, 
                                       expected_format: str = "Speaker: Statement") -> LLMResponse:
        """Synchronous version of validate_transcript_segment."""
        return asyncio.run(self.validate_transcript_segment(transcript_segment, expected_format))
    
    def enhance_speaker_identification(self, text: str, regex_matches: List[Dict[str, Any]], 
                                     confidence_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Enhance regex-based speaker identification with LLM analysis.
        
        Args:
            text: Full text context
            regex_matches: List of regex matches with low confidence
            confidence_threshold: Threshold for requiring LLM enhancement
            
        Returns:
            Enhanced matches with improved confidence and accuracy
        """
        enhanced_matches = []
        
        for match in regex_matches:
            if match.get('confidence', 0) < confidence_threshold:
                # Use LLM to enhance this match
                context_start = max(0, match.get('start_pos', 0) - 200)
                context_end = min(len(text), match.get('end_pos', 0) + 200)
                context = text[context_start:context_end]
                
                ambiguous_text = match.get('text', '')
                possible_speakers = match.get('possible_speakers', [])
                
                llm_response = self.resolve_speaker_identification_sync(
                    context, ambiguous_text, possible_speakers
                )
                
                if llm_response.success:
                    # Update match with LLM results
                    enhanced_match = match.copy()
                    enhanced_match['speaker'] = llm_response.result
                    enhanced_match['confidence'] = llm_response.confidence
                    enhanced_match['llm_enhanced'] = True
                    enhanced_match['llm_reasoning'] = llm_response.reasoning
                    enhanced_matches.append(enhanced_match)
                else:
                    # Keep original match if LLM fails
                    enhanced_matches.append(match)
            else:
                # Keep high-confidence matches as-is
                enhanced_matches.append(match)
        
        return enhanced_matches
    
    def validate_final_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Validate the final formatted transcript using LLM.
        
        Args:
            transcript: Final formatted transcript
            
        Returns:
            Validation results with suggestions
        """
        # Split transcript into manageable chunks
        lines = transcript.strip().split('\n')
        chunk_size = 20  # Lines per chunk
        chunks = [lines[i:i+chunk_size] for i in range(0, len(lines), chunk_size)]
        
        validation_results = []
        
        for i, chunk in enumerate(chunks):
            chunk_text = '\n'.join(chunk)
            
            llm_response = self.validate_transcript_segment_sync(chunk_text)
            
            validation_results.append({
                'chunk_index': i,
                'is_valid': llm_response.success and 'valid' in llm_response.result.lower(),
                'confidence': llm_response.confidence,
                'issues': llm_response.metadata.get('issues', []) if llm_response.metadata else [],
                'reasoning': llm_response.reasoning
            })
        
        # Aggregate results
        overall_valid = all(result['is_valid'] for result in validation_results)
        avg_confidence = sum(result['confidence'] for result in validation_results) / len(validation_results)
        all_issues = []
        for result in validation_results:
            all_issues.extend(result['issues'])
        
        return {
            'overall_valid': overall_valid,
            'average_confidence': avg_confidence,
            'chunk_results': validation_results,
            'all_issues': all_issues,
            'total_chunks': len(chunks)
        }
    
    def get_speaker_suggestions(self, text: str, current_speakers: List[str]) -> List[str]:
        """
        Get LLM suggestions for additional speakers that might be present.
        
        Args:
            text: Full transcript text
            current_speakers: Currently identified speakers
            
        Returns:
            List of suggested additional speakers
        """
        question = f"Are there any additional speakers in this transcript that are not in this list: {', '.join(current_speakers)}? List any missing speakers."
        
        # Use a sample of the text if it's too long
        sample_text = text[:2000] + "..." if len(text) > 2000 else text
        
        llm_response = self.resolve_speaker_identification_sync(
            sample_text, question
        )
        
        if llm_response.success:
            # Try to extract speaker names from the response
            response_text = llm_response.result.lower()
            
            # Simple extraction - look for patterns like "speaker x" or names
            suggested_speakers = []
            
            # Look for "Speaker N" patterns
            import re
            speaker_matches = re.findall(r'speaker\s+(\d+)', response_text)
            for num in speaker_matches:
                speaker_name = f"Speaker {num}"
                if speaker_name not in current_speakers:
                    suggested_speakers.append(speaker_name)
            
            return suggested_speakers
        
        return []
    
    def test_connection(self) -> bool:
        """
        Test connection to the LLM API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.provider == 'openai':
                return self._test_openai_connection()
            elif self.provider == 'gemini':
                return self._test_gemini_connection()
            else:
                return False
        except Exception:
            return False
    
    def _test_openai_connection(self) -> bool:
        """Test OpenAI API connection."""
        try:
            response = self.client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return bool(response.choices[0].message.content)
        except Exception:
            return False
    
    def _test_gemini_connection(self) -> bool:
        """Test Gemini API connection."""
        try:
            response = self.client.generate_content(
                "Hello",
                generation_config=genai.types.GenerationConfig(max_output_tokens=5)
            )
            return bool(response.text)
        except Exception:
            return False