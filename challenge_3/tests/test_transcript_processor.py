"""
Tests for TranscriptProcessor - the main orchestration class.
"""

import unittest
import os
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from transcript_processor import (
    TranscriptProcessor, ProcessingConfig, ProcessingMode, 
    ProcessingResult, ValidationLevel
)


class TestTranscriptProcessor(unittest.TestCase):
    """Test cases for TranscriptProcessor."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use test config directory
        config_dir = Path(__file__).parent.parent / "config"
        
        # Basic configuration for testing
        self.config = ProcessingConfig(
            mode=ProcessingMode.FAST,  # No LLM for basic tests
            confidence_threshold=0.7,
            use_llm=False,  # Disable LLM for most tests
            validation_level=ValidationLevel.BASIC
        )
        
        self.processor = TranscriptProcessor(
            config=self.config,
            config_dir=str(config_dir)
        )
    
    def test_basic_transcript_processing(self):
        """Test basic transcript processing functionality."""
        raw_transcript = """
        John: Hello, how are you today?
        Mary: I'm doing well, thank you for asking.
        John: That's great to hear.
        """
        
        result = self.processor.process_transcript(raw_transcript)
        
        self.assertTrue(result.success)
        self.assertIsInstance(result.formatted_transcript, str)
        self.assertGreater(len(result.formatted_transcript), 0)
        self.assertGreater(len(result.speakers), 0)
        self.assertIn("John", result.speakers)
        self.assertIn("Mary", result.speakers)
    
    def test_numbered_speakers(self):
        """Test processing with numbered speakers."""
        raw_transcript = """
        Speaker 1: This is the first speaker.
        Speaker 2: This is the second speaker.
        Speaker 1: First speaker again.
        """
        
        result = self.processor.process_transcript(raw_transcript)
        
        self.assertTrue(result.success)
        self.assertIn("Speaker 1", result.speakers)
        self.assertIn("Speaker 2", result.speakers)
    
    def test_mixed_speaker_formats(self):
        """Test processing with mixed speaker formats."""
        raw_transcript = """
        John: Hello there.
        Speaker 2: How are you?
        Dr. Smith: This is interesting.
        [Mary]: I agree.
        """
        
        result = self.processor.process_transcript(raw_transcript)
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.speakers), 2)
    
    def test_empty_transcript(self):
        """Test handling of empty transcript."""
        result = self.processor.process_transcript("")
        
        # Should handle gracefully
        self.assertIsInstance(result, ProcessingResult)
        self.assertEqual(len(result.speakers), 0)
    
    def test_no_speakers_transcript(self):
        """Test transcript with no identifiable speakers."""
        raw_transcript = "This is just regular text without any speaker indicators."
        
        result = self.processor.process_transcript(raw_transcript)
        
        self.assertIsInstance(result, ProcessingResult)
        # May succeed or fail depending on implementation
    
    def test_processing_statistics(self):
        """Test processing statistics generation."""
        raw_transcript = """
        John: Hello there.
        Mary: How are you?
        John: I'm doing well.
        """
        
        result = self.processor.process_transcript(raw_transcript)
        
        self.assertIsInstance(result.processing_stats, dict)
        self.assertIn('input_length', result.processing_stats)
        self.assertIn('output_length', result.processing_stats)
        self.assertIn('unique_speakers', result.processing_stats)
        self.assertIn('processing_mode', result.processing_stats)
    
    def test_different_processing_modes(self):
        """Test different processing modes."""
        raw_transcript = """
        John: Hello there.
        Mary: How are you?
        """
        
        # Test FAST mode
        fast_config = ProcessingConfig(mode=ProcessingMode.FAST, use_llm=False)
        fast_processor = TranscriptProcessor(config=fast_config)
        fast_result = fast_processor.process_transcript(raw_transcript)
        
        # Test BALANCED mode (without LLM)
        balanced_config = ProcessingConfig(mode=ProcessingMode.BALANCED, use_llm=False)
        balanced_processor = TranscriptProcessor(config=balanced_config)
        balanced_result = balanced_processor.process_transcript(raw_transcript)
        
        self.assertTrue(fast_result.success)
        self.assertTrue(balanced_result.success)
        self.assertEqual(fast_result.processing_stats['processing_mode'], 'fast')
        self.assertEqual(balanced_result.processing_stats['processing_mode'], 'balanced')
    
    def test_validation_levels(self):
        """Test different validation levels."""
        raw_transcript = """
        John: Hello there.
        Mary: How are you?
        """
        
        # Test BASIC validation
        basic_config = ProcessingConfig(validation_level=ValidationLevel.BASIC)
        basic_processor = TranscriptProcessor(config=basic_config)
        basic_result = basic_processor.process_transcript(raw_transcript)
        
        # Test STRICT validation
        strict_config = ProcessingConfig(validation_level=ValidationLevel.STRICT)
        strict_processor = TranscriptProcessor(config=strict_config)
        strict_result = strict_processor.process_transcript(raw_transcript)
        
        self.assertTrue(basic_result.success)
        self.assertTrue(strict_result.success)
    
    def test_speaker_normalization_toggle(self):
        """Test enabling/disabling speaker normalization."""
        raw_transcript = """
        john: Hello there.
        JOHN: How are you?
        John: I'm doing well.
        """
        
        # With normalization enabled
        norm_config = ProcessingConfig(enable_speaker_normalization=True)
        norm_processor = TranscriptProcessor(config=norm_config)
        norm_result = norm_processor.process_transcript(raw_transcript)
        
        # With normalization disabled
        no_norm_config = ProcessingConfig(enable_speaker_normalization=False)
        no_norm_processor = TranscriptProcessor(config=no_norm_config)
        no_norm_result = no_norm_processor.process_transcript(raw_transcript)
        
        self.assertTrue(norm_result.success)
        self.assertTrue(no_norm_result.success)
        
        # With normalization, should have fewer unique speakers
        if norm_result.success and no_norm_result.success:
            self.assertLessEqual(len(norm_result.speakers), len(no_norm_result.speakers))
    
    def test_numbered_speaker_output(self):
        """Test numbered speaker output option."""
        raw_transcript = """
        John: Hello there.
        Mary: How are you?
        """
        
        # Enable numbered speaker output
        config = ProcessingConfig(output_numbered_speakers=True)
        processor = TranscriptProcessor(config=config)
        result = processor.process_transcript(raw_transcript)
        
        if result.success:
            # Should contain numbered speakers in output
            self.assertTrue(
                any(speaker.startswith("Speaker ") for speaker in result.speakers)
            )
    
    def test_file_processing(self):
        """Test file-based processing."""
        raw_transcript = """
        John: Hello there.
        Mary: How are you?
        John: I'm doing well.
        """
        
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(raw_transcript)
            input_file = f.name
        
        try:
            # Process file
            result = self.processor.process_file(input_file)
            
            self.assertTrue(result.success)
            self.assertGreater(len(result.formatted_transcript), 0)
            
            # Test with output file
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                output_file = f.name
            
            result_with_output = self.processor.process_file(input_file, output_file)
            
            self.assertTrue(result_with_output.success)
            
            # Check output file was created
            self.assertTrue(os.path.exists(output_file))
            
            # Clean up output file
            os.unlink(output_file)
        
        finally:
            # Clean up input file
            os.unlink(input_file)
    
    def test_batch_processing(self):
        """Test batch processing of multiple files."""
        transcripts = [
            "John: Hello there.\nMary: How are you?",
            "Alice: Good morning.\nBob: Good morning to you too.",
            "Speaker 1: This is a test.\nSpeaker 2: Indeed it is."
        ]
        
        input_files = []
        
        # Create temporary input files
        for i, transcript in enumerate(transcripts):
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'_{i}.txt', delete=False) as f:
                f.write(transcript)
                input_files.append(f.name)
        
        try:
            # Process batch
            results = self.processor.batch_process(input_files)
            
            self.assertEqual(len(results), len(transcripts))
            
            # All should succeed
            for result in results:
                self.assertTrue(result.success)
            
            # Test batch summary
            summary = self.processor.get_processing_summary(results)
            
            self.assertIsInstance(summary, dict)
            self.assertEqual(summary['total_files'], len(transcripts))
            self.assertEqual(summary['successful'], len(transcripts))
            self.assertEqual(summary['failed'], 0)
            self.assertEqual(summary['success_rate'], 1.0)
        
        finally:
            # Clean up input files
            for file_path in input_files:
                os.unlink(file_path)
    
    def test_config_updates(self):
        """Test configuration updates."""
        original_mode = self.processor.config.mode
        
        # Update configuration
        self.processor.update_config(mode=ProcessingMode.THOROUGH)
        
        self.assertEqual(self.processor.config.mode, ProcessingMode.THOROUGH)
        self.assertNotEqual(self.processor.config.mode, original_mode)
    
    def test_component_testing(self):
        """Test component testing functionality."""
        test_results = self.processor.test_components()
        
        self.assertIsInstance(test_results, dict)
        self.assertIn('pattern_matcher', test_results)
        self.assertIn('speaker_normalizer', test_results)
        self.assertIn('format_enforcer', test_results)
        self.assertIn('llm_resolver', test_results)
        
        # Pattern matcher and format enforcer should work
        self.assertTrue(test_results['pattern_matcher'])
        self.assertTrue(test_results['format_enforcer'])
    
    def test_error_handling(self):
        """Test error handling for various edge cases."""
        # Test with malformed input
        malformed_transcript = "This is not a proper transcript format at all."
        
        result = self.processor.process_transcript(malformed_transcript)
        
        # Should handle gracefully without crashing
        self.assertIsInstance(result, ProcessingResult)
    
    def test_unicode_support(self):
        """Test unicode character support."""
        unicode_transcript = """
        José: Hola, ¿cómo estás?
        François: Bonjour, ça va bien.
        李明: 你好，我很好。
        """
        
        result = self.processor.process_transcript(unicode_transcript)
        
        self.assertTrue(result.success)
        self.assertIn("José", result.speakers)
        self.assertIn("François", result.speakers)
        self.assertIn("李明", result.speakers)
    
    def test_long_transcript(self):
        """Test processing of long transcripts."""
        # Generate a long transcript
        long_transcript = ""
        for i in range(100):
            long_transcript += f"Speaker {i % 5 + 1}: This is statement number {i}.\n"
        
        result = self.processor.process_transcript(long_transcript)
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.formatted_transcript), 0)
        self.assertGreater(result.processing_stats['input_length'], 1000)
    
    def test_special_characters_in_statements(self):
        """Test handling of special characters in statements."""
        special_transcript = """
        John: Hello! How are you? I'm doing well... thanks for asking.
        Mary: That's great! I'm happy to hear that. :)
        John: Yes, it's been a good day (so far).
        """
        
        result = self.processor.process_transcript(special_transcript)
        
        self.assertTrue(result.success)
        self.assertIn("John", result.speakers)
        self.assertIn("Mary", result.speakers)


class TestProcessingConfig(unittest.TestCase):
    """Test ProcessingConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ProcessingConfig()
        
        self.assertEqual(config.mode, ProcessingMode.BALANCED)
        self.assertEqual(config.confidence_threshold, 0.8)
        self.assertTrue(config.use_llm)
        self.assertEqual(config.max_speakers, 30)
        self.assertEqual(config.validation_level, ValidationLevel.STRICT)
        self.assertTrue(config.enable_speaker_normalization)
        self.assertTrue(config.enable_format_enforcement)
        self.assertFalse(config.output_numbered_speakers)
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = ProcessingConfig(
            mode=ProcessingMode.FAST,
            confidence_threshold=0.6,
            use_llm=False,
            max_speakers=10,
            validation_level=ValidationLevel.BASIC,
            enable_speaker_normalization=False,
            enable_format_enforcement=False,
            output_numbered_speakers=True
        )
        
        self.assertEqual(config.mode, ProcessingMode.FAST)
        self.assertEqual(config.confidence_threshold, 0.6)
        self.assertFalse(config.use_llm)
        self.assertEqual(config.max_speakers, 10)
        self.assertEqual(config.validation_level, ValidationLevel.BASIC)
        self.assertFalse(config.enable_speaker_normalization)
        self.assertFalse(config.enable_format_enforcement)
        self.assertTrue(config.output_numbered_speakers)


class TestProcessingResult(unittest.TestCase):
    """Test ProcessingResult class."""
    
    def test_processing_result_creation(self):
        """Test ProcessingResult object creation."""
        result = ProcessingResult(
            success=True,
            formatted_transcript="John: Hello\nMary: Hi",
            speakers=["John", "Mary"],
            processing_stats={"input_length": 100},
            validation_result={"is_valid": True},
            errors=[],
            warnings=["Minor warning"]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.formatted_transcript, "John: Hello\nMary: Hi")
        self.assertEqual(result.speakers, ["John", "Mary"])
        self.assertEqual(result.processing_stats["input_length"], 100)
        self.assertTrue(result.validation_result["is_valid"])
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, ["Minor warning"])


if __name__ == '__main__':
    unittest.main()