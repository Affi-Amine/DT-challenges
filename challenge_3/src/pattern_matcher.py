"""
Pattern Matcher Module
Regex-based speaker identification and pattern recognition engine.
"""

import re
import yaml
from typing import Dict, List, Optional, Tuple, NamedTuple
from pathlib import Path


class PatternMatch(NamedTuple):
    """Represents a pattern match result."""
    speaker: str
    statement: str
    confidence: float
    pattern_name: str
    start_pos: int
    end_pos: int


class PatternMatcher:
    """
    Regex-based pattern recognition engine for speaker identification.
    
    Uses configurable regex patterns to identify speakers and their statements
    in transcript text with confidence scoring.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the pattern matcher with configuration.
        
        Args:
            config_path: Path to patterns configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.patterns = {}
        self.edge_patterns = {}
        self.noise_patterns = []
        self.normalization_rules = {}
        
        self._load_patterns()
        self._compile_patterns()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent / "config" / "patterns.yaml")
    
    def _load_patterns(self):
        """Load patterns from configuration file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.patterns = config.get('speaker_patterns', {})
            self.edge_patterns = config.get('edge_cases', {})
            self.noise_patterns = config.get('noise_patterns', [])
            self.normalization_rules = config.get('normalization', {})
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Pattern configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance."""
        # Compile speaker patterns
        for name, pattern_config in self.patterns.items():
            pattern_config['compiled'] = re.compile(
                pattern_config['pattern'], 
                re.MULTILINE | re.IGNORECASE
            )
        
        # Compile edge case patterns
        for name, pattern_config in self.edge_patterns.items():
            pattern_config['compiled'] = re.compile(
                pattern_config['pattern'], 
                re.MULTILINE | re.IGNORECASE
            )
        
        # Compile noise patterns
        self.compiled_noise_patterns = [
            re.compile(pattern, re.MULTILINE | re.IGNORECASE) 
            for pattern in self.noise_patterns
        ]
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing noise patterns.
        
        Args:
            text: Raw transcript text
            
        Returns:
            Cleaned text with noise removed
        """
        cleaned_lines = []
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check against noise patterns
            is_noise = False
            for noise_pattern in self.compiled_noise_patterns:
                if noise_pattern.match(line):
                    is_noise = True
                    break
            
            if not is_noise:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def find_speaker_patterns(self, text: str) -> List[PatternMatch]:
        """
        Find all speaker patterns in the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of pattern matches with confidence scores
        """
        matches = []
        
        # First, try to split text that has multiple speakers on the same line
        processed_lines = self._preprocess_text_for_speakers(text)
        
        for line_num, line in enumerate(processed_lines):
            line = line.strip()
            if not line:
                continue
                
            # Try each pattern type on this line
            for pattern_name, pattern_config in self.patterns.items():
                compiled_pattern = pattern_config['compiled']
                confidence = pattern_config['confidence']
                
                match = compiled_pattern.match(line)  # Use match() instead of finditer()
                if match:
                    speaker = match.group(1).strip()
                    statement = match.group(2).strip() if len(match.groups()) > 1 else ""
                    
                    # Skip if speaker is too short or looks like a word fragment
                    if len(speaker) < 2 and not speaker.isupper():
                        continue
                    
                    # Skip obvious non-speakers (common words that might have colons)
                    non_speakers = {'of', 'that', 'we', 'expenses', 'and', 'the', 'a', 'an', 'is', 'are', 'was', 'were'}
                    if speaker.lower() in non_speakers:
                        continue
                    
                    # Calculate adjusted confidence
                    adjusted_confidence = self._calculate_confidence(
                        speaker, statement, confidence, text, line_num * 100
                    )
                    
                    matches.append(PatternMatch(
                        speaker=speaker,
                        statement=statement,
                        confidence=adjusted_confidence,
                        pattern_name=pattern_name,
                        start_pos=line_num * 100,  # Approximate position for sorting
                        end_pos=line_num * 100 + len(line)
                    ))
                    
                    # Only take the first match per line to avoid duplicates
                    break
        
        # Sort by position in text
        matches.sort(key=lambda x: x.start_pos)
        return matches
    
    def _preprocess_text_for_speakers(self, text: str) -> List[str]:
        """
        Preprocess text to split lines that contain multiple speaker statements.
        
        Args:
            text: Raw text to preprocess
            
        Returns:
            List of lines with speakers properly separated
        """
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for multiple speaker patterns in the same line
            # Use a simple regex to find potential speaker boundaries
            speaker_boundary_pattern = r'(?<=[.!?])\s+([A-Z][a-z]+(?:\s+\d+)?|SPEAKER\s*\d+|[A-Z]):\s*'
            
            # Split on speaker boundaries but keep the speaker part
            parts = re.split(speaker_boundary_pattern, line)
            
            if len(parts) > 1:
                # Reconstruct the split parts
                current_line = parts[0].strip()
                if current_line:
                    processed_lines.append(current_line)
                
                # Process the remaining parts in pairs (speaker, statement)
                for i in range(1, len(parts), 2):
                    if i + 1 < len(parts):
                        speaker = parts[i]
                        statement = parts[i + 1]
                        new_line = f"{speaker}: {statement}".strip()
                        if new_line:
                            processed_lines.append(new_line)
            else:
                # No multiple speakers found, add as is
                processed_lines.append(line)
        
        return processed_lines
    
    def find_edge_cases(self, text: str) -> List[PatternMatch]:
        """
        Find edge case patterns that require special handling.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of edge case matches
        """
        edge_matches = []
        
        for pattern_name, pattern_config in self.edge_patterns.items():
            compiled_pattern = pattern_config['compiled']
            confidence = pattern_config['confidence']
            
            for match in compiled_pattern.finditer(text):
                # Handle different edge case types
                if pattern_name == 'multiple_speakers':
                    speaker1 = match.group(1).strip()
                    speaker2 = match.group(2).strip()
                    statement = match.group(3).strip()
                    speaker = f"{speaker1} and {speaker2}"
                elif pattern_name == 'action_description':
                    action = match.group(1).strip()
                    statement = match.group(2).strip()
                    speaker = f"*{action}*"
                else:
                    speaker = match.group(1).strip() if len(match.groups()) > 0 else "UNKNOWN"
                    statement = match.group(-1).strip()  # Last group is usually the statement
                
                edge_matches.append(PatternMatch(
                    speaker=speaker,
                    statement=statement,
                    confidence=confidence,
                    pattern_name=pattern_name,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return edge_matches
    
    def _calculate_confidence(self, speaker: str, statement: str, base_confidence: float, 
                            full_text: str, position: int) -> float:
        """
        Calculate adjusted confidence score based on multiple factors.
        
        Args:
            speaker: Speaker name
            statement: Speaker's statement
            base_confidence: Base confidence from pattern
            full_text: Full text context
            position: Position in text
            
        Returns:
            Adjusted confidence score (0.0 to 1.0)
        """
        confidence = base_confidence
        
        # Boost for proper capitalization
        if speaker and speaker[0].isupper():
            confidence += 0.05
        
        # Boost for title case
        if speaker and speaker.istitle():
            confidence += 0.05
        
        # Penalty for very short statements
        if len(statement) < 10:
            confidence -= 0.1
        
        # Penalty for very long speaker names (likely not a name)
        if len(speaker) > 50:
            confidence -= 0.2
        
        # Boost for common speaker patterns
        if re.match(r'^SPEAKER\s*\d+$', speaker, re.IGNORECASE):
            confidence += 0.1
        
        # Penalty for numbers in speaker names (unless it's SPEAKER1 format)
        if re.search(r'\d', speaker) and not re.match(r'^SPEAKER\s*\d+$', speaker, re.IGNORECASE):
            confidence -= 0.15
        
        # Boost for statements ending with proper punctuation
        if statement and statement[-1] in '.!?':
            confidence += 0.05
        
        # Ensure confidence stays within bounds
        return max(0.0, min(1.0, confidence))
    
    def get_high_confidence_matches(self, matches: List[PatternMatch], 
                                  threshold: float = 0.8) -> List[PatternMatch]:
        """
        Filter matches by confidence threshold.
        
        Args:
            matches: List of pattern matches
            threshold: Minimum confidence threshold
            
        Returns:
            High confidence matches
        """
        return [match for match in matches if match.confidence >= threshold]
    
    def get_ambiguous_matches(self, matches: List[PatternMatch], 
                            threshold: float = 0.8) -> List[PatternMatch]:
        """
        Get matches that fall below confidence threshold (need LLM resolution).
        
        Args:
            matches: List of pattern matches
            threshold: Confidence threshold
            
        Returns:
            Low confidence matches requiring further analysis
        """
        return [match for match in matches if match.confidence < threshold]
    
    def extract_text_segments(self, text: str, matches: List[PatternMatch]) -> List[str]:
        """
        Extract text segments between matches for context analysis.
        
        Args:
            text: Full text
            matches: Pattern matches
            
        Returns:
            List of text segments
        """
        if not matches:
            return [text]
        
        segments = []
        last_end = 0
        
        for match in matches:
            # Add text before this match
            if match.start_pos > last_end:
                segment = text[last_end:match.start_pos].strip()
                if segment:
                    segments.append(segment)
            
            # Add the match itself
            match_text = text[match.start_pos:match.end_pos]
            segments.append(match_text)
            
            last_end = match.end_pos
        
        # Add remaining text
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                segments.append(remaining)
        
        return segments
    
    def get_pattern_statistics(self, matches: List[PatternMatch]) -> Dict[str, int]:
        """
        Get statistics about pattern usage.
        
        Args:
            matches: List of pattern matches
            
        Returns:
            Dictionary with pattern usage counts
        """
        stats = {}
        for match in matches:
            pattern_name = match.pattern_name
            stats[pattern_name] = stats.get(pattern_name, 0) + 1
        
        return stats
    
    def validate_patterns(self) -> Dict[str, bool]:
        """
        Validate that all patterns compile correctly.
        
        Returns:
            Dictionary with pattern validation results
        """
        results = {}
        
        # Test speaker patterns
        for name, config in self.patterns.items():
            try:
                re.compile(config['pattern'])
                results[f"speaker_{name}"] = True
            except re.error:
                results[f"speaker_{name}"] = False
        
        # Test edge case patterns
        for name, config in self.edge_patterns.items():
            try:
                re.compile(config['pattern'])
                results[f"edge_{name}"] = True
            except re.error:
                results[f"edge_{name}"] = False
        
        # Test noise patterns
        for i, pattern in enumerate(self.noise_patterns):
            try:
                re.compile(pattern)
                results[f"noise_{i}"] = True
            except re.error:
                results[f"noise_{i}"] = False
        
        return results