"""
Speaker Normalizer Module
Handles speaker name normalization, mapping, and consistency management.
"""

import re
import yaml
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from collections import defaultdict, Counter
from difflib import SequenceMatcher


class SpeakerNormalizer:
    """
    Speaker name normalization and mapping system.
    
    Handles variations in speaker names, creates consistent mappings,
    and manages speaker identity resolution across the transcript.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the speaker normalizer.
        
        Args:
            config_path: Path to patterns configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.normalization_rules = {}
        self.speaker_mappings = {}
        self.speaker_variations = defaultdict(set)
        self.speaker_counter = Counter()
        
        self._load_normalization_rules()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent / "config" / "patterns.yaml")
    
    def _load_normalization_rules(self):
        """Load normalization rules from configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            self.normalization_rules = config.get('normalization', {})
            
        except FileNotFoundError:
            # Use default rules if config not found
            self._set_default_rules()
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
    
    def _set_default_rules(self):
        """Set default normalization rules."""
        self.normalization_rules = {
            'title_case': True,
            'remove_extra_spaces': True,
            'remove_punctuation': True,
            'handle_common_variations': True,
            'max_speaker_name_length': 50,
            'min_speaker_name_length': 1
        }
    
    def normalize_speaker_name(self, speaker: str) -> str:
        """
        Normalize a single speaker name.
        
        Args:
            speaker: Raw speaker name
            
        Returns:
            Normalized speaker name
        """
        if not speaker:
            return "UNKNOWN"
        
        normalized = speaker.strip()
        
        # Remove extra whitespace
        if self.normalization_rules.get('remove_extra_spaces', True):
            normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove trailing punctuation (but keep internal punctuation)
        if self.normalization_rules.get('remove_punctuation', True):
            normalized = re.sub(r'[^\w\s\-\'\.]+$', '', normalized)
            normalized = re.sub(r'^[^\w\s\-\'\.]+', '', normalized)
        
        # Handle common variations
        if self.normalization_rules.get('handle_common_variations', True):
            normalized = self._handle_common_variations(normalized)
        
        # Apply title case
        if self.normalization_rules.get('title_case', True):
            normalized = self._apply_title_case(normalized)
        
        # Length validation
        max_len = self.normalization_rules.get('max_speaker_name_length', 50)
        min_len = self.normalization_rules.get('min_speaker_name_length', 1)
        
        if len(normalized) > max_len:
            normalized = normalized[:max_len].strip()
        
        if len(normalized) < min_len:
            return "UNKNOWN"
        
        return normalized
    
    def _handle_common_variations(self, speaker: str) -> str:
        """Handle common speaker name variations."""
        # Common patterns to normalize
        variations = {
            # Speaker number formats
            r'SPEAKER\s*(\d+)': r'Speaker \1',
            r'Speaker\s*(\d+)': r'Speaker \1',
            r'speaker\s*(\d+)': r'Speaker \1',
            
            # Remove common prefixes/suffixes
            r'^(Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?)\s*': '',
            r'\s*(Jr\.?|Sr\.?|III|II|IV)$': '',
            
            # Handle parenthetical information
            r'\s*\([^)]*\)\s*': ' ',
            
            # Handle brackets
            r'\s*\[[^\]]*\]\s*': ' ',
            
            # Handle common typos
            r'Spekaer': 'Speaker',
            r'Speker': 'Speaker',
        }
        
        normalized = speaker
        for pattern, replacement in variations.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        return normalized.strip()
    
    def _apply_title_case(self, speaker: str) -> str:
        """Apply proper title case to speaker names."""
        # Don't title case if it's already in a specific format
        if re.match(r'^SPEAKER\s*\d+$', speaker, re.IGNORECASE):
            return speaker.upper()
        
        # Handle special cases
        special_words = {
            'and': 'and',
            'the': 'the',
            'of': 'of',
            'in': 'in',
            'on': 'on',
            'at': 'at',
            'to': 'to',
            'for': 'for',
            'with': 'with',
            'by': 'by'
        }
        
        words = speaker.split()
        titled_words = []
        
        for i, word in enumerate(words):
            if i == 0 or word.lower() not in special_words:
                titled_words.append(word.capitalize())
            else:
                titled_words.append(special_words[word.lower()])
        
        return ' '.join(titled_words)
    
    def find_similar_speakers(self, speaker: str, existing_speakers: List[str], 
                            threshold: float = 0.8) -> List[Tuple[str, float]]:
        """
        Find similar speaker names in existing list.
        
        Args:
            speaker: Speaker name to match
            existing_speakers: List of existing speaker names
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of (speaker_name, similarity_score) tuples
        """
        similarities = []
        
        for existing in existing_speakers:
            similarity = self._calculate_similarity(speaker, existing)
            if similarity >= threshold:
                similarities.append((existing, similarity))
        
        # Sort by similarity score (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two speaker names.
        
        Args:
            name1: First speaker name
            name2: Second speaker name
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Normalize both names for comparison
        norm1 = self.normalize_speaker_name(name1).lower()
        norm2 = self.normalize_speaker_name(name2).lower()
        
        # Exact match
        if norm1 == norm2:
            return 1.0
        
        # Use sequence matcher for fuzzy matching
        base_similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Boost for common patterns
        boosts = 0.0
        
        # Both are speaker numbers
        if (re.match(r'speaker\s*\d+', norm1) and re.match(r'speaker\s*\d+', norm2)):
            # Extract numbers
            num1 = re.search(r'\d+', norm1)
            num2 = re.search(r'\d+', norm2)
            if num1 and num2 and num1.group() == num2.group():
                boosts += 0.3
        
        # Similar initials
        if self._have_similar_initials(norm1, norm2):
            boosts += 0.1
        
        # Common word overlap
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        if words1 & words2:  # Intersection
            overlap_ratio = len(words1 & words2) / max(len(words1), len(words2))
            boosts += overlap_ratio * 0.2
        
        return min(1.0, base_similarity + boosts)
    
    def _have_similar_initials(self, name1: str, name2: str) -> bool:
        """Check if two names have similar initials."""
        def get_initials(name):
            return ''.join([word[0] for word in name.split() if word])
        
        initials1 = get_initials(name1)
        initials2 = get_initials(name2)
        
        if len(initials1) != len(initials2):
            return False
        
        return initials1 == initials2
    
    def build_speaker_mapping(self, speakers: List[str]) -> Dict[str, str]:
        """
        Build a mapping from raw speaker names to normalized canonical names.
        
        Args:
            speakers: List of raw speaker names
            
        Returns:
            Dictionary mapping raw names to canonical names
        """
        # Normalize all speakers
        normalized_speakers = [self.normalize_speaker_name(s) for s in speakers]
        
        # Group similar speakers
        speaker_groups = self._group_similar_speakers(normalized_speakers)
        
        # Create canonical mapping
        mapping = {}
        for group in speaker_groups:
            canonical = self._choose_canonical_name(group)
            for speaker in group:
                # Find original raw names that map to this normalized name
                for i, norm in enumerate(normalized_speakers):
                    if norm == speaker:
                        mapping[speakers[i]] = canonical
        
        return mapping
    
    def _group_similar_speakers(self, speakers: List[str]) -> List[List[str]]:
        """Group similar speaker names together."""
        groups = []
        used = set()
        
        for speaker in speakers:
            if speaker in used:
                continue
            
            # Start a new group
            group = [speaker]
            used.add(speaker)
            
            # Find similar speakers
            for other in speakers:
                if other in used:
                    continue
                
                if self._calculate_similarity(speaker, other) >= 0.8:
                    group.append(other)
                    used.add(other)
            
            groups.append(group)
        
        return groups
    
    def _choose_canonical_name(self, group: List[str]) -> str:
        """Choose the best canonical name from a group of similar names."""
        if len(group) == 1:
            return group[0]
        
        # Scoring criteria
        scores = {}
        
        for name in group:
            score = 0
            
            # Prefer proper capitalization
            if name.istitle():
                score += 10
            
            # Prefer shorter names (less likely to have extra info)
            score += max(0, 20 - len(name))
            
            # Prefer names without numbers (unless it's SPEAKER format)
            if not re.search(r'\d', name) or re.match(r'Speaker\s*\d+', name):
                score += 5
            
            # Prefer names without special characters
            if re.match(r'^[A-Za-z\s\-\'\.]+$', name):
                score += 5
            
            # Prefer SPEAKER format if multiple exist
            if re.match(r'Speaker\s*\d+', name):
                score += 15
            
            scores[name] = score
        
        # Return the highest scoring name
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def assign_speaker_numbers(self, speakers: List[str], 
                             start_number: int = 1) -> Dict[str, str]:
        """
        Assign sequential numbers to speakers.
        
        Args:
            speakers: List of speaker names
            start_number: Starting number for assignment
            
        Returns:
            Dictionary mapping original names to numbered format
        """
        unique_speakers = list(dict.fromkeys(speakers))  # Preserve order, remove duplicates
        
        mapping = {}
        current_number = start_number
        
        for speaker in unique_speakers:
            if speaker and speaker != "UNKNOWN":
                mapping[speaker] = f"Speaker {current_number}"
                current_number += 1
            else:
                mapping[speaker] = "Unknown Speaker"
        
        return mapping
    
    def validate_speaker_names(self, speakers: List[str]) -> Dict[str, List[str]]:
        """
        Validate speaker names and categorize issues.
        
        Args:
            speakers: List of speaker names to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': [],
            'too_long': [],
            'too_short': [],
            'invalid_characters': [],
            'likely_noise': []
        }
        
        max_len = self.normalization_rules.get('max_speaker_name_length', 50)
        min_len = self.normalization_rules.get('min_speaker_name_length', 1)
        
        for speaker in speakers:
            if not speaker or len(speaker.strip()) < min_len:
                results['too_short'].append(speaker)
            elif len(speaker) > max_len:
                results['too_long'].append(speaker)
            elif not re.match(r'^[A-Za-z0-9\s\-\'\.()[\]]+$', speaker):
                results['invalid_characters'].append(speaker)
            elif self._is_likely_noise(speaker):
                results['likely_noise'].append(speaker)
            else:
                results['valid'].append(speaker)
        
        return results
    
    def _is_likely_noise(self, speaker: str) -> bool:
        """Check if a speaker name is likely noise/invalid."""
        noise_patterns = [
            r'^\d+$',  # Just numbers
            r'^[^\w\s]+$',  # Just punctuation
            r'(transcript|recording|audio|video|meeting)',  # Common noise words
            r'(page|line|time|minute|second)',  # Time/location references
            r'^.{0,2}$',  # Very short (1-2 characters)
        ]
        
        for pattern in noise_patterns:
            if re.search(pattern, speaker, re.IGNORECASE):
                return True
        
        return False
    
    def get_speaker_statistics(self, speakers: List[str]) -> Dict[str, any]:
        """
        Get statistics about speaker names.
        
        Args:
            speakers: List of speaker names
            
        Returns:
            Dictionary with statistics
        """
        normalized = [self.normalize_speaker_name(s) for s in speakers]
        unique_speakers = set(normalized)
        
        return {
            'total_speakers': len(speakers),
            'unique_speakers': len(unique_speakers),
            'most_common': Counter(normalized).most_common(5),
            'average_name_length': sum(len(s) for s in normalized) / len(normalized) if normalized else 0,
            'validation_results': self.validate_speaker_names(speakers)
        }