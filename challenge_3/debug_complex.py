#!/usr/bin/env python3
"""
Debug script for complex transcript processing
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from transcript_processor import TranscriptProcessor, ProcessingConfig, ProcessingMode, ValidationLevel
from pattern_matcher import PatternMatcher

def debug_complex_processing():
    print("🔍 Debugging Complex Transcript Processing")
    print("=" * 50)
    
    complex_transcript = """
    Speaker 1: Welcome everyone to today's meeting.
    SPEAKER_2: Thank you for having us here.
    Person A: I have some questions about the project.
    John Smith: Let me address those concerns.
    Mary (CEO): From a business perspective, this looks good.
    Unknown: What about the timeline?
    """
    
    print(f"Input transcript:\n{complex_transcript}")
    print()
    
    # First test pattern matcher directly
    print("Testing pattern matcher directly:")
    pattern_matcher = PatternMatcher()
    matches = pattern_matcher.find_speaker_patterns(complex_transcript)
    
    print(f"Found {len(matches)} matches:")
    for i, match in enumerate(matches, 1):
        print(f"  {i}. Speaker: '{match.speaker}' | Statement: '{match.statement}' | Pattern: {match.pattern_name}")
    
    print()
    print("=" * 50)
    
    # Now test full processor
    config = ProcessingConfig(
        mode=ProcessingMode.BALANCED,
        use_llm=False,
        validation_level=ValidationLevel.MODERATE
    )
    
    processor = TranscriptProcessor(
        config=config,
        config_dir="config"
    )
    
    try:
        result = processor.process_transcript(complex_transcript)
        
        print(f"Processing success: {result.success}")
        print(f"Number of speakers found: {len(result.speakers)}")
        print(f"Speakers: {result.speakers}")
        print()
        
        if result.formatted_transcript:
            print("Formatted transcript:")
            print(result.formatted_transcript)
            
    except Exception as e:
        print(f"Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_complex_processing()