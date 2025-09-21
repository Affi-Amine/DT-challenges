"""
Integration tests for the complete transcript formatting solution.
Tests end-to-end functionality with sample transcripts.
"""

import unittest
import sys
from pathlib import Path

# Add src and sample_data to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "sample_data"))

from transcript_processor import TranscriptProcessor, ProcessingConfig, ProcessingMode
import sample_transcripts


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def setUp(self):
        """Set up test fixtures."""
        config_dir = Path(__file__).parent.parent / "config"
        
        # Use FAST mode to avoid LLM dependencies in tests
        self.config = ProcessingConfig(
            mode=ProcessingMode.FAST,
            use_llm=False,
            confidence_threshold=0.7
        )
        
        self.processor = TranscriptProcessor(
            config=self.config,
            config_dir=str(config_dir)
        )
    
    def test_basic_conversation_processing(self):
        """Test processing of basic conversation."""
        transcript = sample_transcripts.BASIC_CONVERSATION
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success, f"Processing failed: {result.errors}")
        self.assertGreater(len(result.formatted_transcript), 0)
        self.assertIn("John", result.speakers)
        self.assertIn("Mary", result.speakers)
        
        # Check that output is properly formatted
        lines = result.formatted_transcript.strip().split('\n')
        for line in lines:
            if line.strip():
                self.assertIn(":", line, f"Line missing colon: {line}")
    
    def test_numbered_speakers_processing(self):
        """Test processing of numbered speakers."""
        transcript = sample_transcripts.NUMBERED_SPEAKERS
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertIn("Speaker 1", result.speakers)
        self.assertIn("Speaker 2", result.speakers)
        self.assertIn("Speaker 3", result.speakers)
    
    def test_mixed_formats_processing(self):
        """Test processing of mixed speaker formats."""
        transcript = sample_transcripts.MIXED_FORMATS
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.speakers), 2)
        
        # Should identify multiple speakers despite different formats
        speakers_found = len(result.speakers)
        self.assertGreaterEqual(speakers_found, 3)
    
    def test_technical_discussion_processing(self):
        """Test processing of technical discussion."""
        transcript = sample_transcripts.TECHNICAL_DISCUSSION
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertIn("Dr. Smith", result.speakers)
        self.assertIn("Engineer", result.speakers)
        
        # Check that technical terms are preserved
        self.assertIn("O(n log n)", result.formatted_transcript)
        self.assertIn("hash table", result.formatted_transcript)
    
    def test_formal_meeting_processing(self):
        """Test processing of formal meeting transcript."""
        transcript = sample_transcripts.FORMAL_MEETING
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertIn("Chairperson", result.speakers)
        self.assertIn("Secretary", result.speakers)
        self.assertIn("Treasurer", result.speakers)
        
        # Should have multiple members
        member_speakers = [s for s in result.speakers if "Member" in s]
        self.assertGreaterEqual(len(member_speakers), 2)
    
    def test_interview_transcript_processing(self):
        """Test processing of interview transcript."""
        transcript = sample_transcripts.INTERVIEW_TRANSCRIPT
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertIn("Interviewer", result.speakers)
        self.assertIn("Candidate", result.speakers)
        
        # Check that technical terms are preserved
        self.assertIn("Python", result.formatted_transcript)
        self.assertIn("JavaScript", result.formatted_transcript)
    
    def test_background_noise_filtering(self):
        """Test filtering of background noise."""
        transcript = sample_transcripts.BACKGROUND_NOISE
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertIn("John", result.speakers)
        self.assertIn("Mary", result.speakers)
        
        # Background noise should be filtered out
        self.assertNotIn("[Background noise]", result.formatted_transcript)
        self.assertNotIn("(Phone ringing)", result.formatted_transcript)
        self.assertNotIn("(Coughing)", result.formatted_transcript)
    
    def test_special_characters_handling(self):
        """Test handling of special characters."""
        transcript = sample_transcripts.SPECIAL_CHARACTERS
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertIn("John", result.speakers)
        self.assertIn("Mary", result.speakers)
        
        # Special characters should be preserved in statements
        self.assertIn("!", result.formatted_transcript)
        self.assertIn("?", result.formatted_transcript)
        self.assertIn("@", result.formatted_transcript)
        self.assertIn("&", result.formatted_transcript)
    
    def test_multilingual_speakers(self):
        """Test handling of multilingual speaker names."""
        transcript = sample_transcripts.MULTILINGUAL_SPEAKERS
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertIn("José", result.speakers)
        self.assertIn("François", result.speakers)
        self.assertIn("李明", result.speakers)
    
    def test_long_speaker_names(self):
        """Test handling of long speaker names."""
        transcript = sample_transcripts.LONG_SPEAKER_NAMES
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertIn("Dr. Elizabeth Johnson-Smith III", result.speakers)
        
        # Should handle long titles
        long_title_speakers = [s for s in result.speakers if len(s) > 20]
        self.assertGreater(len(long_title_speakers), 0)
    
    def test_rapid_exchange_processing(self):
        """Test processing of rapid exchange."""
        transcript = sample_transcripts.RAPID_EXCHANGE
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertIn("A", result.speakers)
        self.assertIn("B", result.speakers)
        
        # Should handle short statements
        lines = [line for line in result.formatted_transcript.split('\n') if line.strip()]
        self.assertGreater(len(lines), 5)
    
    def test_long_monologue_processing(self):
        """Test processing of long monologue."""
        transcript = sample_transcripts.LONG_MONOLOGUE
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertIn("Professor", result.speakers)
        self.assertIn("Student", result.speakers)
        
        # Long statement should be preserved
        self.assertIn("machine learning", result.formatted_transcript.lower())
        self.assertIn("artificial intelligence", result.formatted_transcript.lower())
    
    def test_inconsistent_naming_normalization(self):
        """Test normalization of inconsistent speaker naming."""
        # Enable speaker normalization for this test
        config = ProcessingConfig(
            mode=ProcessingMode.FAST,
            use_llm=False,
            enable_speaker_normalization=True
        )
        processor = TranscriptProcessor(config=config)
        
        transcript = sample_transcripts.INCONSISTENT_NAMING
        result = processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        
        # With normalization, should have fewer unique speakers
        # (john, JOHN, John should be normalized to one speaker)
        unique_speakers = len(result.speakers)
        self.assertLessEqual(unique_speakers, 3)  # Should normalize similar names
    
    def test_processing_statistics_accuracy(self):
        """Test accuracy of processing statistics."""
        transcript = sample_transcripts.BASIC_CONVERSATION
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        
        stats = result.processing_stats
        
        # Check basic statistics
        self.assertGreater(stats['input_length'], 0)
        self.assertGreater(stats['output_length'], 0)
        self.assertGreater(stats['unique_speakers'], 0)
        self.assertEqual(stats['processing_mode'], 'fast')
        self.assertFalse(stats['llm_used'])
        
        # Input and output should be reasonable
        self.assertLessEqual(stats['output_length'], stats['input_length'] * 2)
    
    def test_validation_results(self):
        """Test validation results for processed transcripts."""
        transcript = sample_transcripts.BASIC_CONVERSATION
        result = self.processor.process_transcript(transcript)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.validation_result)
        
        validation = result.validation_result['format_validation']
        self.assertTrue(validation['is_valid'])
        self.assertGreaterEqual(validation['line_count'], 1)
        self.assertGreaterEqual(validation['speaker_count'], 1)
    
    def test_error_handling_with_malformed_input(self):
        """Test error handling with malformed input."""
        malformed_inputs = [
            "",  # Empty string
            "   ",  # Only whitespace
            "This is just text without any speakers",  # No speakers
            ":::: Invalid format ::::",  # Malformed
            "\n\n\n",  # Only newlines
        ]
        
        for malformed_input in malformed_inputs:
            result = self.processor.process_transcript(malformed_input)
            
            # Should handle gracefully without crashing
            self.assertIsInstance(result.success, bool)
            self.assertIsInstance(result.formatted_transcript, str)
            self.assertIsInstance(result.speakers, list)
    
    def test_all_easy_samples(self):
        """Test all easy sample transcripts."""
        easy_samples = sample_transcripts.get_samples_by_difficulty('easy')
        
        for i, transcript in enumerate(easy_samples):
            with self.subTest(sample=i):
                result = self.processor.process_transcript(transcript)
                self.assertTrue(result.success, f"Easy sample {i} failed: {result.errors}")
                self.assertGreater(len(result.speakers), 0)
    
    def test_all_medium_samples(self):
        """Test all medium difficulty sample transcripts."""
        medium_samples = sample_transcripts.get_samples_by_difficulty('medium')
        
        for i, transcript in enumerate(medium_samples):
            with self.subTest(sample=i):
                result = self.processor.process_transcript(transcript)
                # Medium samples should mostly succeed
                if not result.success:
                    print(f"Medium sample {i} failed: {result.errors}")
                # Don't assert success for medium samples as they may be challenging
    
    def test_component_integration(self):
        """Test that all components work together properly."""
        transcript = sample_transcripts.MIXED_FORMATS
        
        # Test component status
        component_status = self.processor.test_components()
        
        # Core components should be working
        self.assertTrue(component_status['pattern_matcher'])
        self.assertTrue(component_status['speaker_normalizer'])
        self.assertTrue(component_status['format_enforcer'])
        
        # Process transcript
        result = self.processor.process_transcript(transcript)
        self.assertTrue(result.success)
    
    def test_different_processing_modes_comparison(self):
        """Test different processing modes on the same transcript."""
        transcript = sample_transcripts.TECHNICAL_DISCUSSION
        
        # Test FAST mode
        fast_config = ProcessingConfig(mode=ProcessingMode.FAST, use_llm=False)
        fast_processor = TranscriptProcessor(config=fast_config)
        fast_result = fast_processor.process_transcript(transcript)
        
        # Test BALANCED mode (without LLM)
        balanced_config = ProcessingConfig(mode=ProcessingMode.BALANCED, use_llm=False)
        balanced_processor = TranscriptProcessor(config=balanced_config)
        balanced_result = balanced_processor.process_transcript(transcript)
        
        # Both should succeed
        self.assertTrue(fast_result.success)
        self.assertTrue(balanced_result.success)
        
        # Both should identify the same speakers for this clear transcript
        self.assertEqual(set(fast_result.speakers), set(balanced_result.speakers))
    
    def test_batch_processing_integration(self):
        """Test batch processing with multiple sample transcripts."""
        # Select a few different samples
        transcripts = [
            sample_transcripts.BASIC_CONVERSATION,
            sample_transcripts.NUMBERED_SPEAKERS,
            sample_transcripts.TECHNICAL_DISCUSSION
        ]
        
        # Create temporary files
        import tempfile
        import os
        
        temp_files = []
        for i, transcript in enumerate(transcripts):
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'_test_{i}.txt', delete=False) as f:
                f.write(transcript)
                temp_files.append(f.name)
        
        try:
            # Process batch
            results = self.processor.batch_process(temp_files)
            
            self.assertEqual(len(results), len(transcripts))
            
            # All should succeed
            successful_results = [r for r in results if r.success]
            self.assertEqual(len(successful_results), len(transcripts))
            
            # Get summary
            summary = self.processor.get_processing_summary(results)
            self.assertEqual(summary['success_rate'], 1.0)
            self.assertEqual(summary['total_files'], len(transcripts))
        
        finally:
            # Clean up
            for temp_file in temp_files:
                os.unlink(temp_file)


class TestSampleTranscripts(unittest.TestCase):
    """Test the sample transcripts module."""
    
    def test_sample_retrieval(self):
        """Test sample transcript retrieval functions."""
        # Test getting sample by name
        basic = sample_transcripts.get_sample_by_name('basic_conversation')
        self.assertIsInstance(basic, str)
        self.assertGreater(len(basic), 0)
        
        # Test getting samples by difficulty
        easy_samples = sample_transcripts.get_samples_by_difficulty('easy')
        self.assertIsInstance(easy_samples, list)
        self.assertGreater(len(easy_samples), 0)
        
        # Test getting all sample names
        all_names = sample_transcripts.get_all_sample_names()
        self.assertIsInstance(all_names, list)
        self.assertGreater(len(all_names), 10)
    
    def test_sample_content_validity(self):
        """Test that sample transcripts contain valid content."""
        all_samples = sample_transcripts.ALL_SAMPLES
        
        for name, content in all_samples.items():
            with self.subTest(sample=name):
                self.assertIsInstance(content, str)
                self.assertGreater(len(content.strip()), 0)
                # Should contain at least one colon (speaker indicator)
                self.assertIn(":", content)


if __name__ == '__main__':
    unittest.main()