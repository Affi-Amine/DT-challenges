"""
Tests for PatternMatcher component.
"""

import unittest
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pattern_matcher import PatternMatcher, PatternMatch


class TestPatternMatcher(unittest.TestCase):
    """Test cases for PatternMatcher."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use test config directory
        config_dir = Path(__file__).parent.parent / "config"
        config_path = config_dir / "patterns.yaml"
        
        self.pattern_matcher = PatternMatcher(str(config_path))
    
    def test_basic_speaker_patterns(self):
        """Test basic speaker pattern recognition."""
        test_cases = [
            "Speaker 1: Hello world",
            "John: How are you?",
            "Dr. Smith: This is important",
            "INTERVIEWER: What do you think?",
            "participant_2: I agree"
        ]
        
        for text in test_cases:
            matches = self.pattern_matcher.find_speaker_patterns(text)
            self.assertGreater(len(matches), 0, f"No matches found for: {text}")
            self.assertIsInstance(matches[0], PatternMatch)
            self.assertGreater(matches[0].confidence, 0.5)
    
    def test_colon_patterns(self):
        """Test colon-based speaker patterns."""
        text = """
        John: Hello there.
        Mary: How are you doing?
        Dr. Johnson: This is very interesting.
        """
        
        matches = self.pattern_matcher.find_speaker_patterns(text)
        
        # Should find 3 speakers
        self.assertEqual(len(matches), 3)
        
        # Check speaker names
        speakers = [match.speaker for match in matches]
        self.assertIn("John", speakers)
        self.assertIn("Mary", speakers)
        self.assertIn("Dr. Johnson", speakers)
    
    def test_dash_patterns(self):
        """Test dash-based speaker patterns."""
        text = """
        - John: Hello there.
        - Mary: How are you?
        """
        
        matches = self.pattern_matcher.find_speaker_patterns(text)
        self.assertGreater(len(matches), 0)
    
    def test_bracket_patterns(self):
        """Test bracket-based speaker patterns."""
        text = """
        [John]: Hello there.
        [Mary Smith]: How are you?
        """
        
        matches = self.pattern_matcher.find_speaker_patterns(text)
        self.assertGreater(len(matches), 0)
    
    def test_numbered_speakers(self):
        """Test numbered speaker patterns."""
        text = """
        Speaker 1: First statement.
        Speaker 2: Second statement.
        Participant 3: Third statement.
        """
        
        matches = self.pattern_matcher.find_speaker_patterns(text)
        self.assertEqual(len(matches), 3)
        
        speakers = [match.speaker for match in matches]
        self.assertIn("Speaker 1", speakers)
        self.assertIn("Speaker 2", speakers)
        self.assertIn("Participant 3", speakers)
    
    def test_edge_cases(self):
        """Test edge case patterns."""
        text = """
        >> John speaking here
        John continues: with more text
        (John interrupting): Wait a minute
        """
        
        matches = self.pattern_matcher.find_edge_cases(text)
        self.assertGreater(len(matches), 0)
    
    def test_confidence_scoring(self):
        """Test confidence scoring for different patterns."""
        high_confidence_text = "John: This is a clear statement."
        low_confidence_text = "maybe john said something here"
        
        high_matches = self.pattern_matcher.find_speaker_patterns(high_confidence_text)
        low_matches = self.pattern_matcher.find_edge_cases(low_confidence_text)
        
        if high_matches and low_matches:
            self.assertGreater(high_matches[0].confidence, low_matches[0].confidence)
    
    def test_text_cleaning(self):
        """Test text cleaning functionality."""
        dirty_text = "  John:   Hello    world!  \n\n  Mary:  How are you?  "
        cleaned = self.pattern_matcher.clean_text(dirty_text)
        
        # Should remove extra whitespace
        self.assertNotIn("    ", cleaned)
        self.assertNotIn("\n\n", cleaned)
    
    def test_noise_filtering(self):
        """Test noise pattern filtering."""
        noisy_text = """
        John: Hello there.
        [Background noise]
        Mary: How are you?
        (Coughing)
        Dr. Smith: This is important.
        """
        
        # Clean text should remove noise
        cleaned = self.pattern_matcher.clean_text(noisy_text)
        self.assertNotIn("[Background noise]", cleaned)
        self.assertNotIn("(Coughing)", cleaned)
    
    def test_high_confidence_filtering(self):
        """Test high confidence match filtering."""
        text = """
        John: Very clear statement.
        maybe someone said something
        Mary: Another clear statement.
        """
        
        all_matches = (self.pattern_matcher.find_speaker_patterns(text) + 
                      self.pattern_matcher.find_edge_cases(text))
        
        high_confidence = self.pattern_matcher.get_high_confidence_matches(all_matches, 0.8)
        ambiguous = self.pattern_matcher.get_ambiguous_matches(all_matches, 0.8)
        
        # Should separate high and low confidence matches
        self.assertGreater(len(high_confidence), 0)
        
        # High confidence matches should have higher confidence
        if high_confidence:
            self.assertGreaterEqual(min(m.confidence for m in high_confidence), 0.8)
    
    def test_pattern_statistics(self):
        """Test pattern usage statistics."""
        text = """
        John: Statement one.
        Mary: Statement two.
        Dr. Smith: Statement three.
        """
        
        matches = self.pattern_matcher.find_speaker_patterns(text)
        stats = self.pattern_matcher.get_pattern_statistics(matches)
        
        self.assertIsInstance(stats, dict)
        self.assertGreater(len(stats), 0)
    
    def test_empty_input(self):
        """Test handling of empty input."""
        matches = self.pattern_matcher.find_speaker_patterns("")
        self.assertEqual(len(matches), 0)
    
    def test_no_speakers(self):
        """Test text with no speaker patterns."""
        text = "This is just regular text without any speaker indicators."
        matches = self.pattern_matcher.find_speaker_patterns(text)
        self.assertEqual(len(matches), 0)
    
    def test_malformed_patterns(self):
        """Test handling of malformed speaker patterns."""
        text = """
        John:: Double colon issue
        : Missing speaker name
        John How are you (missing colon)
        """
        
        # Should handle gracefully without crashing
        matches = self.pattern_matcher.find_speaker_patterns(text)
        # May or may not find matches, but shouldn't crash
        self.assertIsInstance(matches, list)
    
    def test_unicode_handling(self):
        """Test handling of unicode characters in speaker names."""
        text = """
        José: Hola mundo.
        François: Bonjour le monde.
        李明: 你好世界.
        """
        
        matches = self.pattern_matcher.find_speaker_patterns(text)
        self.assertGreater(len(matches), 0)
        
        speakers = [match.speaker for match in matches]
        self.assertIn("José", speakers)
        self.assertIn("François", speakers)
        self.assertIn("李明", speakers)
    
    def test_long_speaker_names(self):
        """Test handling of long speaker names."""
        text = """
        Dr. Elizabeth Johnson-Smith III: This is a long name.
        Professor of Computer Science at MIT: Another long title.
        """
        
        matches = self.pattern_matcher.find_speaker_patterns(text)
        self.assertGreater(len(matches), 0)
    
    def test_case_sensitivity(self):
        """Test case sensitivity in pattern matching."""
        text = """
        john: lowercase name
        JOHN: uppercase name
        John: proper case name
        """
        
        matches = self.pattern_matcher.find_speaker_patterns(text)
        self.assertEqual(len(matches), 3)
        
        # All should be detected as separate speakers initially
        speakers = [match.speaker for match in matches]
        self.assertEqual(len(set(speakers)), 3)  # All different due to case


class TestPatternMatchClass(unittest.TestCase):
    """Test the PatternMatch data class."""
    
    def test_pattern_match_creation(self):
        """Test PatternMatch object creation."""
        match = PatternMatch(
            speaker="John",
            statement="Hello world",
            confidence=0.9,
            pattern_name="colon_pattern",
            start_pos=0,
            end_pos=17
        )
        
        self.assertEqual(match.speaker, "John")
        self.assertEqual(match.statement, "Hello world")
        self.assertEqual(match.confidence, 0.9)
        self.assertEqual(match.pattern_name, "colon_pattern")
        self.assertEqual(match.start_pos, 0)
        self.assertEqual(match.end_pos, 17)
    
    def test_pattern_match_string_representation(self):
        """Test string representation of PatternMatch."""
        match = PatternMatch(
            speaker="John",
            statement="Hello world",
            confidence=0.9,
            pattern_name="colon_pattern",
            start_pos=0,
            end_pos=17
        )
        
        str_repr = str(match)
        self.assertIn("John", str_repr)
        self.assertIn("Hello world", str_repr)
        self.assertIn("0.9", str_repr)


if __name__ == '__main__':
    unittest.main()