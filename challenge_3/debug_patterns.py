#!/usr/bin/env python3
"""
Debug script for pattern matcher
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pattern_matcher import PatternMatcher

def debug_pattern_matcher():
    print("🔍 Debugging Pattern Matcher")
    print("=" * 50)
    
    # Initialize pattern matcher
    pattern_matcher = PatternMatcher()
    
    # Test text from the failing test
    test_text = "John: Hello there. Mary: How are you? Speaker 1: Good morning."
    print(f"Test text: {test_text}")
    print()
    
    # Find patterns
    matches = pattern_matcher.find_speaker_patterns(test_text)
    print(f"Found {len(matches)} matches:")
    
    for i, match in enumerate(matches, 1):
        print(f"  {i}. Speaker: '{match.speaker}' | Statement: '{match.statement}' | Pattern: {match.pattern_name} | Confidence: {match.confidence}")
    
    print()
    print("Available patterns:")
    for name, config in pattern_matcher.patterns.items():
        print(f"  - {name}: {config.get('description', 'No description')}")
    
    print()
    print("Testing each pattern individually:")
    
    # Test each pattern individually
    import re
    for name, config in pattern_matcher.patterns.items():
        pattern = config['pattern']
        compiled = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
        matches_found = compiled.findall(test_text)
        print(f"  {name}: {len(matches_found)} matches - {matches_found}")

if __name__ == "__main__":
    debug_pattern_matcher()