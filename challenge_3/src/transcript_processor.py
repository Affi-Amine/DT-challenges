"""
Transcript Processor Module
Main orchestration class that coordinates all components for transcript processing.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    from .pattern_matcher import PatternMatcher, PatternMatch
    from .speaker_normalizer import SpeakerNormalizer
    from .format_enforcer import FormatEnforcer, ValidationLevel
    from .llm_resolver import LLMResolver, LLMResponse
except ImportError:
    from pattern_matcher import PatternMatcher, PatternMatch
    from speaker_normalizer import SpeakerNormalizer
    from format_enforcer import FormatEnforcer, ValidationLevel
    from llm_resolver import LLMResolver, LLMResponse


class ProcessingMode(Enum):
    """Processing modes for different use cases."""
    FAST = "fast"  # Regex only, no LLM
    BALANCED = "balanced"  # Regex + LLM for ambiguous cases
    THOROUGH = "thorough"  # Full LLM validation and enhancement


@dataclass
class ProcessingConfig:
    """Configuration for transcript processing."""
    mode: ProcessingMode = ProcessingMode.BALANCED
    confidence_threshold: float = 0.8
    use_llm: bool = True
    max_speakers: int = 30
    validation_level: ValidationLevel = ValidationLevel.STRICT
    enable_speaker_normalization: bool = True
    enable_format_enforcement: bool = True
    output_numbered_speakers: bool = False


@dataclass
class ProcessingResult:
    """Result of transcript processing."""
    success: bool
    formatted_transcript: str
    speakers: List[str]
    processing_stats: Dict[str, Any]
    validation_result: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    warnings: List[str] = None


class TranscriptProcessor:
    """
    Main transcript processing orchestrator.
    
    Coordinates pattern matching, speaker normalization, format enforcement,
    and LLM resolution to convert unformatted transcripts into the required format.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None, 
                 config_dir: Optional[str] = None,
                 api_key: Optional[str] = None):
        """
        Initialize the transcript processor.
        
        Args:
            config: Processing configuration
            config_dir: Directory containing configuration files
            api_key: OpenAI API key for LLM resolver
        """
        self.config = config or ProcessingConfig()
        self.config_dir = config_dir or self._get_default_config_dir()
        
        # Initialize components
        self.pattern_matcher = PatternMatcher(
            config_path=os.path.join(self.config_dir, "patterns.yaml")
        )
        
        self.speaker_normalizer = SpeakerNormalizer(
            config_path=os.path.join(self.config_dir, "patterns.yaml")
        )
        
        self.format_enforcer = FormatEnforcer(
            validation_level=self.config.validation_level
        )
        
        self.llm_resolver = None
        if self.config.use_llm:
            try:
                self.llm_resolver = LLMResolver(
                    config_path=os.path.join(self.config_dir, "prompts.yaml"),
                    api_key=api_key
                )
            except Exception as e:
                print(f"Warning: Failed to initialize LLM resolver: {e}")
                self.llm_resolver = None
        
        # Setup logging
        self._setup_logging()
    
    def _get_default_config_dir(self) -> str:
        """Get default configuration directory."""
        return str(Path(__file__).parent.parent / "config")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def process_transcript(self, raw_transcript: str) -> ProcessingResult:
        """
        Process a raw transcript into the required format.
        
        Args:
            raw_transcript: Unformatted transcript text
            
        Returns:
            Processing result with formatted transcript and metadata
        """
        self.logger.info("Starting transcript processing")
        
        try:
            # Phase 1: Text Cleaning and Preprocessing
            cleaned_text = self._preprocess_text(raw_transcript)
            
            # Phase 2: Pattern-based Speaker Detection
            pattern_matches = self._detect_speakers(cleaned_text)
            
            # Phase 3: Speaker Normalization and Mapping
            normalized_matches = self._normalize_speakers(pattern_matches)
            
            # Phase 4: LLM Enhancement (if enabled and needed)
            enhanced_matches = self._enhance_with_llm(cleaned_text, normalized_matches)
            
            # Phase 5: Format Enforcement
            formatted_transcript = self._enforce_format(enhanced_matches)
            
            # Phase 6: Final Validation
            validation_result = self._validate_result(formatted_transcript)
            
            # Compile results
            speakers = self.format_enforcer.extract_speakers(formatted_transcript)
            
            # Apply speaker numbering if requested
            if self.config.output_numbered_speakers:
                formatted_transcript = self.format_enforcer.convert_to_numbered_speakers(formatted_transcript)
                speakers = self.format_enforcer.extract_speakers(formatted_transcript)
            
            processing_stats = self._compile_statistics(
                raw_transcript, formatted_transcript, pattern_matches, enhanced_matches
            )
            
            return ProcessingResult(
                success=True,
                formatted_transcript=formatted_transcript,
                speakers=speakers,
                processing_stats=processing_stats,
                validation_result=validation_result,
                errors=[],
                warnings=[]
            )
        
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            return ProcessingResult(
                success=False,
                formatted_transcript="",
                speakers=[],
                processing_stats={},
                errors=[str(e)]
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess and clean the raw transcript text."""
        self.logger.info("Preprocessing text")
        
        # Basic cleaning
        cleaned = text.strip()
        
        # Remove excessive whitespace
        import re
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)  # Remove empty lines
        cleaned = re.sub(r' +', ' ', cleaned)  # Remove multiple spaces
        
        # Use pattern matcher's cleaning functionality
        cleaned = self.pattern_matcher.clean_text(cleaned)
        
        return cleaned
    
    def _detect_speakers(self, text: str) -> List[PatternMatch]:
        """Detect speakers using pattern matching."""
        self.logger.info("Detecting speakers with pattern matching")
        
        # Use the pattern matcher that we fixed
        pattern_matches = self.pattern_matcher.find_speaker_patterns(text)
        
        self.logger.info(f"Found {len(pattern_matches)} potential speaker matches")
        
        return pattern_matches
    
    def _normalize_speakers(self, matches: List[PatternMatch]) -> List[PatternMatch]:
        """Normalize speaker names in the matches."""
        if not self.config.enable_speaker_normalization:
            return matches
        
        self.logger.info("Normalizing speaker names")
        
        # Extract all speaker names
        speakers = [match.speaker for match in matches]
        
        # Build speaker mapping
        speaker_mapping = self.speaker_normalizer.build_speaker_mapping(speakers)
        
        # Apply normalization to matches
        normalized_matches = []
        for match in matches:
            normalized_speaker = speaker_mapping.get(match.speaker, match.speaker)
            
            # Create new match with normalized speaker
            normalized_match = PatternMatch(
                speaker=normalized_speaker,
                statement=match.statement,
                confidence=match.confidence,
                pattern_name=match.pattern_name,
                start_pos=match.start_pos,
                end_pos=match.end_pos
            )
            normalized_matches.append(normalized_match)
        
        return normalized_matches
    
    def _enhance_with_llm(self, text: str, matches: List[PatternMatch]) -> List[PatternMatch]:
        """Enhance matches using LLM for ambiguous cases."""
        if not self.config.use_llm or not self.llm_resolver:
            return matches
        
        if self.config.mode == ProcessingMode.FAST:
            return matches
        
        self.logger.info("Enhancing with LLM analysis")
        
        # Separate high and low confidence matches
        high_confidence = self.pattern_matcher.get_high_confidence_matches(
            matches, self.config.confidence_threshold
        )
        low_confidence = self.pattern_matcher.get_ambiguous_matches(
            matches, self.config.confidence_threshold
        )
        
        if not low_confidence:
            return matches
        
        # Enhance low confidence matches with LLM
        enhanced_low_confidence = []
        
        for match in low_confidence:
            # Get context around the match
            context_start = max(0, match.start_pos - 200)
            context_end = min(len(text), match.end_pos + 200)
            context = text[context_start:context_end]
            
            # Get possible speakers from high confidence matches
            possible_speakers = list(set(m.speaker for m in high_confidence))
            
            # Use LLM to resolve
            llm_response = self.llm_resolver.resolve_speaker_identification_sync(
                context, match.statement, possible_speakers
            )
            
            if llm_response.success and llm_response.confidence > 0.5:
                # Create enhanced match
                enhanced_match = PatternMatch(
                    speaker=llm_response.result,
                    statement=match.statement,
                    confidence=llm_response.confidence,
                    pattern_name=f"llm_enhanced_{match.pattern_name}",
                    start_pos=match.start_pos,
                    end_pos=match.end_pos
                )
                enhanced_low_confidence.append(enhanced_match)
            else:
                # Keep original if LLM fails
                enhanced_low_confidence.append(match)
        
        # Combine high confidence and enhanced low confidence matches
        all_enhanced = high_confidence + enhanced_low_confidence
        all_enhanced.sort(key=lambda x: x.start_pos)
        
        return all_enhanced
    
    def _enforce_format(self, matches: List[PatternMatch]) -> str:
        """Enforce the required output format."""
        if not self.config.enable_format_enforcement:
            # Simple formatting without enforcement
            statements = [(match.speaker, match.statement) for match in matches]
            return '\n'.join(f"{speaker}: {statement}" for speaker, statement in statements)
        
        self.logger.info("Enforcing output format")
        
        # Convert matches to (speaker, statement) tuples
        statements = [(match.speaker, match.statement) for match in matches]
        
        # Use format enforcer to create properly formatted output
        formatted_transcript = self.format_enforcer.format_transcript(statements)
        
        return formatted_transcript
    
    def _validate_result(self, formatted_transcript: str) -> Optional[Dict[str, Any]]:
        """Validate the final result."""
        self.logger.info("Validating final result")
        
        # Basic format validation
        validation_result = self.format_enforcer.validate_format(formatted_transcript)
        
        result = {
            'format_validation': {
                'is_valid': validation_result.is_valid,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'line_count': validation_result.line_count,
                'speaker_count': validation_result.speaker_count
            }
        }
        
        # LLM validation for thorough mode
        if (self.config.mode == ProcessingMode.THOROUGH and 
            self.config.use_llm and self.llm_resolver):
            
            llm_validation = self.llm_resolver.validate_final_transcript(formatted_transcript)
            result['llm_validation'] = llm_validation
        
        return result
    
    def _compile_statistics(self, raw_text: str, formatted_text: str, 
                          original_matches: List[PatternMatch], 
                          final_matches: List[PatternMatch]) -> Dict[str, Any]:
        """Compile processing statistics."""
        return {
            'input_length': len(raw_text),
            'output_length': len(formatted_text),
            'input_lines': len(raw_text.split('\n')),
            'output_lines': len([line for line in formatted_text.split('\n') if line.strip()]),
            'original_matches': len(original_matches),
            'final_matches': len(final_matches),
            'unique_speakers': len(set(match.speaker for match in final_matches)),
            'average_confidence': sum(match.confidence for match in final_matches) / len(final_matches) if final_matches else 0,
            'pattern_usage': self.pattern_matcher.get_pattern_statistics(original_matches),
            'processing_mode': self.config.mode.value,
            'llm_used': self.config.use_llm and self.llm_resolver is not None
        }
    
    def process_file(self, input_file: str, output_file: Optional[str] = None) -> ProcessingResult:
        """
        Process a transcript file.
        
        Args:
            input_file: Path to input transcript file
            output_file: Path to output file (optional)
            
        Returns:
            Processing result
        """
        self.logger.info(f"Processing file: {input_file}")
        
        try:
            # Read input file
            with open(input_file, 'r', encoding='utf-8') as f:
                raw_transcript = f.read()
            
            # Process transcript
            result = self.process_transcript(raw_transcript)
            
            # Write output file if specified
            if output_file and result.success:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.formatted_transcript)
                self.logger.info(f"Output written to: {output_file}")
            
            return result
        
        except Exception as e:
            self.logger.error(f"File processing failed: {e}")
            return ProcessingResult(
                success=False,
                formatted_transcript="",
                speakers=[],
                processing_stats={},
                errors=[str(e)]
            )
    
    def batch_process(self, input_files: List[str], 
                     output_dir: Optional[str] = None) -> List[ProcessingResult]:
        """
        Process multiple transcript files.
        
        Args:
            input_files: List of input file paths
            output_dir: Directory for output files
            
        Returns:
            List of processing results
        """
        results = []
        
        for input_file in input_files:
            output_file = None
            if output_dir:
                input_path = Path(input_file)
                output_file = os.path.join(output_dir, f"{input_path.stem}_formatted.txt")
            
            result = self.process_file(input_file, output_file)
            results.append(result)
        
        return results
    
    def get_processing_summary(self, results: List[ProcessingResult]) -> Dict[str, Any]:
        """
        Get summary statistics for batch processing.
        
        Args:
            results: List of processing results
            
        Returns:
            Summary statistics
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        if successful:
            avg_speakers = sum(len(r.speakers) for r in successful) / len(successful)
            avg_confidence = sum(r.processing_stats.get('average_confidence', 0) for r in successful) / len(successful)
        else:
            avg_speakers = 0
            avg_confidence = 0
        
        return {
            'total_files': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(results) if results else 0,
            'average_speakers_per_file': avg_speakers,
            'average_confidence': avg_confidence,
            'total_speakers': sum(len(r.speakers) for r in successful),
            'processing_mode': self.config.mode.value
        }
    
    def update_config(self, **kwargs):
        """Update processing configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Reinitialize components if needed
        if 'validation_level' in kwargs:
            self.format_enforcer = FormatEnforcer(validation_level=self.config.validation_level)
    
    def test_components(self) -> Dict[str, bool]:
        """Test all components for proper initialization."""
        results = {}
        
        # Test pattern matcher
        try:
            test_text = "Speaker 1: Hello world"
            matches = self.pattern_matcher.find_speaker_patterns(test_text)
            results['pattern_matcher'] = True
        except Exception:
            results['pattern_matcher'] = False
        
        # Test speaker normalizer
        try:
            test_speaker = "Speaker 1"
            normalized = self.speaker_normalizer.normalize_speaker_name(test_speaker)
            results['speaker_normalizer'] = True
        except Exception:
            results['speaker_normalizer'] = False
        
        # Test format enforcer
        try:
            test_statements = [("Speaker 1", "Hello world")]
            formatted = self.format_enforcer.format_transcript(test_statements)
            results['format_enforcer'] = True
        except Exception:
            results['format_enforcer'] = False
        
        # Test LLM resolver
        if self.llm_resolver:
            try:
                connection_result = self.llm_resolver.test_connection()
                results['llm_resolver'] = connection_result
            except Exception:
                results['llm_resolver'] = False
        else:
            print("No LLM resolver available")
            results['llm_resolver'] = False
        
        return results