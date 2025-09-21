#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.transcript_processor import TranscriptProcessor, ProcessingConfig, ProcessingMode
from src.format_enforcer import ValidationLevel

def debug_format_issue():
    print("🔍 Debugging Format Issue")
    print("=" * 50)
    
    complex_transcript = """
    Speaker 1: Welcome everyone to today's meeting.
    SPEAKER_2: Thank you for having us here.
    Person A: I have some questions about the project.
    John Smith: Let me address those concerns.
    Mary (CEO): From a business perspective, this looks good.
    Unknown: What about the timeline?
    """
    
    config = ProcessingConfig(
        mode=ProcessingMode.BALANCED,
        use_llm=False,
        validation_level=ValidationLevel.MODERATE
    )
    
    processor = TranscriptProcessor(
        config=config,
        config_dir="config"
    )
    
    result = processor.process_transcript(complex_transcript)
    
    print("Formatted transcript:")
    print(repr(result.formatted_transcript))
    print()
    print("Formatted transcript (readable):")
    print(result.formatted_transcript)
    print()
    print("=" * 50)
    
    # Test the extract_speakers method directly
    from src.format_enforcer import FormatEnforcer
    format_enforcer = FormatEnforcer()
    
    speakers = format_enforcer.extract_speakers(result.formatted_transcript)
    print(f"Extracted speakers: {speakers}")
    print(f"Number of speakers: {len(speakers)}")
    
    # Test the pattern that extract_speakers uses
    import re
    pattern = re.compile(r'^([A-Za-z0-9\s\-\'\.()[\]]+):\s*(.+)$')
    
    print("\nTesting pattern on each line:")
    for i, line in enumerate(result.formatted_transcript.split('\n')):
        line = line.strip()
        if line:
            match = pattern.match(line)
            print(f"Line {i+1}: '{line}' -> Match: {bool(match)}")
            if match:
                print(f"  Speaker: '{match.group(1)}', Statement: '{match.group(2)}'")

if __name__ == "__main__":
    debug_format_issue()