"""
Format Enforcer Module
Ensures exact compliance with the required transcript output format.
"""

import re
from typing import List, Dict, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum


class FormatError(Exception):
    """Custom exception for format validation errors."""
    pass


class ValidationLevel(Enum):
    """Validation strictness levels."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


@dataclass
class FormattedStatement:
    """Represents a properly formatted speaker statement."""
    speaker: str
    statement: str
    line_number: int
    original_text: str = ""


@dataclass
class FormatValidationResult:
    """Result of format validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    line_count: int
    speaker_count: int


class FormatEnforcer:
    """
    Format enforcement engine for transcript output.
    
    Ensures exact compliance with the required format:
    - Speaker Name: Statement text
    - Proper capitalization and punctuation
    - Consistent speaker naming
    - Line-by-line validation
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STRICT):
        """
        Initialize the format enforcer.
        
        Args:
            validation_level: How strict the validation should be
        """
        self.validation_level = validation_level
        self.required_format_pattern = re.compile(
            r'^([A-Za-z0-9\s\-\'\.()[\]]+):\s*(.+)$'
        )
        self.speaker_statement_separator = ": "
        
    def format_transcript(self, statements: List[Tuple[str, str]]) -> str:
        """
        Format a list of (speaker, statement) tuples into the required format.
        
        Args:
            statements: List of (speaker_name, statement_text) tuples
            
        Returns:
            Properly formatted transcript string
        """
        if not statements:
            return ""
        
        formatted_lines = []
        
        for speaker, statement in statements:
            formatted_line = self._format_single_statement(speaker, statement)
            formatted_lines.append(formatted_line)
        
        return '\n'.join(formatted_lines)
    
    def _format_single_statement(self, speaker: str, statement: str) -> str:
        """
        Format a single speaker statement according to Challenge 3 specification.
        
        Format:
        SPEAKER:
        Statement.
        
        Args:
            speaker: Speaker name
            statement: Statement text
            
        Returns:
            Formatted lines (speaker line + statement line)
        """
        # Clean and validate speaker name
        clean_speaker = self._clean_speaker_name(speaker)
        
        # Clean and validate statement
        clean_statement = self._clean_statement_text(statement)
        
        # Format according to Challenge 3 specification:
        # SPEAKER:
        # Statement.
        return f"{clean_speaker}:\n{clean_statement}"
    
    def _clean_speaker_name(self, speaker: str) -> str:
        """Clean and format speaker name."""
        if not speaker:
            return "Unknown Speaker"
        
        # Remove leading/trailing whitespace
        clean = speaker.strip()
        
        # Remove any existing colons or separators
        clean = re.sub(r':\s*$', '', clean)
        
        # Ensure proper capitalization
        if not clean.isupper() and not re.match(r'^Speaker\s*\d+$', clean, re.IGNORECASE):
            # Apply title case for regular names
            clean = clean.title()
        elif re.match(r'^Speaker\s*\d+$', clean, re.IGNORECASE):
            # Standardize speaker number format
            match = re.match(r'^Speaker\s*(\d+)$', clean, re.IGNORECASE)
            if match:
                clean = f"Speaker {match.group(1)}"
        
        return clean
    
    def _clean_statement_text(self, statement: str) -> str:
        """Clean and format statement text."""
        if not statement:
            return ""
        
        # Remove leading/trailing whitespace
        clean = statement.strip()
        
        # Remove any leading speaker separators that might have been included
        clean = re.sub(r'^:\s*', '', clean)
        
        # Ensure the statement ends with proper punctuation
        if clean and not clean[-1] in '.!?':
            # Add period if no punctuation exists
            clean += '.'
        
        # Fix spacing around punctuation
        clean = re.sub(r'\s+([.!?])', r'\1', clean)  # Remove space before punctuation
        clean = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', clean)  # Add space after punctuation
        
        # Fix multiple spaces
        clean = re.sub(r'\s+', ' ', clean)
        
        return clean
    
    def validate_format(self, transcript: str) -> FormatValidationResult:
        """
        Validate that a transcript follows the required format.
        
        Args:
            transcript: Transcript text to validate
            
        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []
        
        if not transcript or not transcript.strip():
            return FormatValidationResult(
                is_valid=False,
                errors=["Transcript is empty"],
                warnings=[],
                line_count=0,
                speaker_count=0
            )
        
        lines = transcript.strip().split('\n')
        speakers = set()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line:
                if self.validation_level == ValidationLevel.STRICT:
                    errors.append(f"Line {line_num}: Empty line not allowed in strict mode")
                continue
            
            # Check format pattern
            match = self.required_format_pattern.match(line)
            if not match:
                errors.append(f"Line {line_num}: Does not match required format 'Speaker: Statement'")
                continue
            
            speaker = match.group(1).strip()
            statement = match.group(2).strip()
            
            # Validate speaker name
            speaker_errors = self._validate_speaker_name(speaker, line_num)
            errors.extend(speaker_errors)
            
            # Validate statement
            statement_errors, statement_warnings = self._validate_statement(statement, line_num)
            errors.extend(statement_errors)
            warnings.extend(statement_warnings)
            
            speakers.add(speaker)
        
        # Additional validations
        if len(speakers) > 30:
            warnings.append(f"High number of speakers ({len(speakers)}). Consider consolidating similar names.")
        
        if len(speakers) == 0:
            errors.append("No valid speakers found in transcript")
        
        is_valid = len(errors) == 0
        
        return FormatValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            line_count=len([l for l in lines if l.strip()]),
            speaker_count=len(speakers)
        )
    
    def _validate_speaker_name(self, speaker: str, line_num: int) -> List[str]:
        """Validate a speaker name."""
        errors = []
        
        if not speaker:
            errors.append(f"Line {line_num}: Speaker name is empty")
            return errors
        
        # Length validation
        if len(speaker) > 50:
            errors.append(f"Line {line_num}: Speaker name too long (max 50 characters)")
        
        if len(speaker) < 1:
            errors.append(f"Line {line_num}: Speaker name too short")
        
        # Character validation
        if not re.match(r'^[A-Za-z0-9\s\-\'\.()[\]]+$', speaker):
            if self.validation_level in [ValidationLevel.STRICT, ValidationLevel.MODERATE]:
                errors.append(f"Line {line_num}: Speaker name contains invalid characters")
        
        # Format-specific validations
        if self.validation_level == ValidationLevel.STRICT:
            # Check capitalization
            if not (speaker.istitle() or speaker.isupper() or 
                   re.match(r'^Speaker\s*\d+$', speaker)):
                errors.append(f"Line {line_num}: Speaker name should be properly capitalized")
        
        return errors
    
    def _validate_statement(self, statement: str, line_num: int) -> Tuple[List[str], List[str]]:
        """Validate a statement."""
        errors = []
        warnings = []
        
        if not statement:
            errors.append(f"Line {line_num}: Statement is empty")
            return errors, warnings
        
        # Length validation
        if len(statement) < 1:
            errors.append(f"Line {line_num}: Statement is too short")
        
        if len(statement) > 1000:
            warnings.append(f"Line {line_num}: Very long statement (consider splitting)")
        
        # Punctuation validation
        if self.validation_level == ValidationLevel.STRICT:
            if not statement[-1] in '.!?':
                errors.append(f"Line {line_num}: Statement should end with proper punctuation")
        
        # Check for common formatting issues
        if statement.startswith(':'):
            errors.append(f"Line {line_num}: Statement should not start with colon")
        
        if re.search(r'\s{2,}', statement):
            warnings.append(f"Line {line_num}: Multiple consecutive spaces found")
        
        return errors, warnings
    
    def fix_common_format_issues(self, transcript: str) -> str:
        """
        Automatically fix common format issues.
        
        Args:
            transcript: Raw transcript text
            
        Returns:
            Corrected transcript
        """
        if not transcript:
            return ""
        
        lines = transcript.split('\n')
        fixed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to fix common issues
            fixed_line = self._fix_line_format(line)
            if fixed_line:
                fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines)
    
    def _fix_line_format(self, line: str) -> Optional[str]:
        """Fix format issues in a single line."""
        # Remove extra whitespace
        line = re.sub(r'\s+', ' ', line.strip())
        
        # Try different separator patterns
        separators = [': ', ':', ' - ', ' – ', ' — ', ' | ']
        
        for sep in separators:
            if sep in line:
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    speaker = parts[0].strip()
                    statement = parts[1].strip()
                    
                    if speaker and statement:
                        return self._format_single_statement(speaker, statement)
        
        # Try to detect speaker at the beginning
        # Pattern: "SPEAKER_NAME some statement text"
        match = re.match(r'^([A-Za-z0-9\s\-\'\.()[\]]{1,50}?)\s+(.{10,})$', line)
        if match:
            potential_speaker = match.group(1).strip()
            potential_statement = match.group(2).strip()
            
            # Heuristics to determine if first part is likely a speaker name
            if (len(potential_speaker.split()) <= 3 and  # Not too many words
                not potential_speaker.lower().startswith(('the', 'and', 'but', 'so')) and  # Not starting with common words
                len(potential_statement) > len(potential_speaker)):  # Statement longer than speaker
                
                return self._format_single_statement(potential_speaker, potential_statement)
        
        return None
    
    def extract_speakers(self, transcript: str) -> List[str]:
        """
        Extract all unique speakers from a formatted transcript.
        
        Args:
            transcript: Formatted transcript
            
        Returns:
            List of unique speaker names
        """
        speakers = set()
        
        for line in transcript.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check for single-line format: "Speaker: Statement"
            match = self.required_format_pattern.match(line)
            if match:
                speaker = match.group(1).strip()
                speakers.add(speaker)
            # Check for multi-line format: "Speaker:" (speaker on its own line)
            elif line.endswith(':'):
                potential_speaker = line[:-1].strip()
                # Validate that this looks like a speaker name
                if (potential_speaker and 
                    re.match(r'^[A-Za-z0-9\s\-\'\.()[\]]+$', potential_speaker) and
                    len(potential_speaker) <= 50):
                    speakers.add(potential_speaker)
        
        return sorted(list(speakers))
    
    def get_format_statistics(self, transcript: str) -> Dict[str, any]:
        """
        Get statistics about the transcript format.
        
        Args:
            transcript: Transcript to analyze
            
        Returns:
            Dictionary with format statistics
        """
        validation_result = self.validate_format(transcript)
        speakers = self.extract_speakers(transcript)
        
        lines = [line.strip() for line in transcript.split('\n') if line.strip()]
        
        # Calculate average statement length
        statement_lengths = []
        for line in lines:
            match = self.required_format_pattern.match(line)
            if match:
                statement = match.group(2).strip()
                statement_lengths.append(len(statement))
        
        avg_statement_length = sum(statement_lengths) / len(statement_lengths) if statement_lengths else 0
        
        return {
            'is_valid': validation_result.is_valid,
            'total_lines': len(lines),
            'total_speakers': len(speakers),
            'speakers': speakers,
            'average_statement_length': avg_statement_length,
            'validation_errors': len(validation_result.errors),
            'validation_warnings': len(validation_result.warnings),
            'format_compliance': len(statement_lengths) / len(lines) if lines else 0
        }
    
    def convert_to_numbered_speakers(self, transcript: str) -> str:
        """
        Convert speaker names to numbered format (Speaker 1, Speaker 2, etc.).
        
        Args:
            transcript: Formatted transcript
            
        Returns:
            Transcript with numbered speakers
        """
        speakers = self.extract_speakers(transcript)
        speaker_mapping = {speaker: f"Speaker {i+1}" for i, speaker in enumerate(speakers)}
        
        lines = []
        for line in transcript.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            match = self.required_format_pattern.match(line)
            if match:
                original_speaker = match.group(1).strip()
                statement = match.group(2).strip()
                
                new_speaker = speaker_mapping.get(original_speaker, original_speaker)
                lines.append(f"{new_speaker}: {statement}")
            else:
                lines.append(line)  # Keep malformed lines as-is
        
        return '\n'.join(lines)
    
    def split_long_statements(self, transcript: str, max_length: int = 200) -> str:
        """
        Split long statements into multiple lines while preserving format.
        
        Args:
            transcript: Formatted transcript
            max_length: Maximum statement length
            
        Returns:
            Transcript with split statements
        """
        lines = []
        
        for line in transcript.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            match = self.required_format_pattern.match(line)
            if match:
                speaker = match.group(1).strip()
                statement = match.group(2).strip()
                
                if len(statement) <= max_length:
                    lines.append(line)
                else:
                    # Split statement at sentence boundaries
                    sentences = re.split(r'([.!?])\s+', statement)
                    
                    current_chunk = ""
                    for i in range(0, len(sentences), 2):
                        sentence = sentences[i]
                        punctuation = sentences[i+1] if i+1 < len(sentences) else ""
                        
                        full_sentence = sentence + punctuation
                        
                        if len(current_chunk + full_sentence) <= max_length:
                            current_chunk += full_sentence + " "
                        else:
                            if current_chunk:
                                lines.append(f"{speaker}: {current_chunk.strip()}")
                            current_chunk = full_sentence + " "
                    
                    if current_chunk:
                        lines.append(f"{speaker}: {current_chunk.strip()}")
            else:
                lines.append(line)
        
        return '\n'.join(lines)