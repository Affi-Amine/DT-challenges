"""
Smart Speaker Detection Module

This module provides intelligent speaker detection that properly handles
the complex test case format and avoids false positives.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SpeakerMatch:
    speaker: str
    statement: str
    confidence: float
    line_number: int
    original_line: str


class SmartSpeakerDetector:
    """
    Intelligent speaker detection that handles various transcript formats
    and avoids common false positives.
    """
    
    def __init__(self):
        # Define patterns in order of priority (highest confidence first)
        self.patterns = [
            # Timestamped speakers: [14:30] John Smith (CEO): Statement
            {
                'name': 'timestamped_with_role',
                'pattern': r'^\[\d{2}:\d{2}\]\s*([A-Za-z][A-Za-z\s\-\.]+?)\s*\([^)]+\):\s*(.+)$',
                'confidence': 0.95
            },
            # Timestamped speakers: [14:30] John Smith: Statement
            {
                'name': 'timestamped_simple',
                'pattern': r'^\[\d{2}:\d{2}\]\s*([A-Za-z][A-Za-z\s\-\.]+?):\s*(.+)$',
                'confidence': 0.9
            },
            # Prefixed speakers: >> Interviewer: Statement or - Mary Johnson: Statement
            {
                'name': 'prefixed',
                'pattern': r'^(?:>>?\s*|[-\*]\s*)([A-Za-z][A-Za-z\s\-\.]+?):\s*(.+)$',
                'confidence': 0.85
            },
            # Doctor titles: Dr. Elizabeth Wilson-Brown III: Statement
            {
                'name': 'doctor_title',
                'pattern': r'^(Dr\.?\s+[A-Za-z][A-Za-z\s\-\.]+?):\s*(.+)$',
                'confidence': 0.9
            },
            # Full names: John Smith: Statement (at least two words, both capitalized)
            {
                'name': 'full_name',
                'pattern': r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):\s*(.+)$',
                'confidence': 0.85
            },
            # Single names: John: Statement (capitalized, at least 3 letters)
            {
                'name': 'single_name',
                'pattern': r'^([A-Z][a-z]{2,}):\s*(.+)$',
                'confidence': 0.8
            },
            # Single letter abbreviations: J: Statement or M: Statement
            {
                'name': 'single_letter',
                'pattern': r'^([A-Z]):\s*(.+)$',
                'confidence': 0.75
            }
        ]
        
        # Common words that should never be considered speakers
        self.non_speakers = {
            'welcome', 'thank', 'before', 'of', 'that', 'we', 'expenses', 'and', 'the', 'a', 'an',
            'is', 'are', 'was', 'were', 'have', 'has', 'had', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'must', 'shall', 'do', 'does', 'did', 'get', 'got', 'go', 'went',
            'come', 'came', 'see', 'saw', 'know', 'knew', 'think', 'thought', 'say', 'said', 'tell',
            'told', 'ask', 'asked', 'give', 'gave', 'take', 'took', 'make', 'made', 'let', 'put',
            'set', 'run', 'ran', 'walk', 'walked', 'talk', 'talked', 'work', 'worked', 'play',
            'played', 'look', 'looked', 'find', 'found', 'help', 'helped', 'try', 'tried', 'use',
            'used', 'want', 'wanted', 'need', 'needed', 'like', 'liked', 'love', 'loved', 'hate',
            'hated', 'feel', 'felt', 'seem', 'seemed', 'become', 'became', 'leave', 'left', 'turn',
            'turned', 'start', 'started', 'stop', 'stopped', 'keep', 'kept', 'hold', 'held', 'bring',
            'brought', 'show', 'showed', 'follow', 'followed', 'call', 'called', 'move', 'moved'
        }
    
    def detect_speakers(self, text: str) -> List[SpeakerMatch]:
        """
        Detect speakers in the given text using intelligent pattern matching.
        
        Args:
            text: The transcript text to analyze
            
        Returns:
            List of SpeakerMatch objects with detected speakers and statements
        """
        matches = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Skip obvious noise lines
            if self._is_noise_line(line):
                continue
            
            # Try each pattern in order of confidence
            for pattern_info in self.patterns:
                pattern = re.compile(pattern_info['pattern'])
                match = pattern.match(line)
                
                if match:
                    speaker = match.group(1).strip()
                    statement = match.group(2).strip() if len(match.groups()) > 1 else ""
                    
                    # Validate the speaker
                    if self._is_valid_speaker(speaker):
                        confidence = self._calculate_confidence(
                            speaker, statement, pattern_info['confidence'], line
                        )
                        
                        matches.append(SpeakerMatch(
                            speaker=speaker,
                            statement=statement,
                            confidence=confidence,
                            line_number=line_num + 1,
                            original_line=line
                        ))
                        break  # Only take the first match per line
        
        return matches
    
    def _is_noise_line(self, line: str) -> bool:
        """Check if a line is noise (background sounds, etc.)"""
        noise_patterns = [
            r'^\(.*\)$',  # (Background noise)
            r'^\*.*\*$',  # *phone rings*
            r'^\[.*\]$',  # [sound effect] (but not timestamps)
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, line):
                # Exception for timestamps
                if re.match(r'^\[\d{2}:\d{2}\]', line):
                    return False
                return True
        
        return False
    
    def _is_valid_speaker(self, speaker: str) -> bool:
        """Validate if a detected speaker is actually a valid speaker name"""
        # Check against non-speaker words
        if speaker.lower() in self.non_speakers:
            return False
        
        # Must be at least 1 character
        if len(speaker) < 1:
            return False
        
        # Single letters must be uppercase
        if len(speaker) == 1 and not speaker.isupper():
            return False
        
        # Names should start with a capital letter
        if not speaker[0].isupper():
            return False
        
        # Check for obvious sentence fragments
        if speaker.endswith('.') or speaker.endswith(','):
            return False
        
        return True
    
    def _calculate_confidence(self, speaker: str, statement: str, base_confidence: float, line: str) -> float:
        """Calculate adjusted confidence based on context"""
        confidence = base_confidence
        
        # Boost confidence for known good patterns
        if len(speaker.split()) > 1:  # Multi-word names
            confidence += 0.05
        
        if speaker.startswith('Dr.'):  # Doctor titles
            confidence += 0.05
        
        if re.match(r'^[A-Z][a-z]+$', speaker):  # Proper capitalization
            confidence += 0.02
        
        # Reduce confidence for suspicious patterns
        if len(speaker) < 3 and not speaker.isupper():  # Short non-uppercase
            confidence -= 0.1
        
        if speaker.lower() in ['that', 'this', 'what', 'when', 'where', 'why', 'how']:
            confidence -= 0.3
        
        return min(1.0, max(0.0, confidence))
    
    def format_output(self, matches: List[SpeakerMatch]) -> str:
        """Format the detected speakers into the required output format"""
        if not matches:
            return ""
        
        formatted_lines = []
        for match in matches:
            formatted_lines.append(f"{match.speaker}:")
            formatted_lines.append(match.statement)
        
        return '\n'.join(formatted_lines)