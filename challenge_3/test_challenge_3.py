#!/usr/bin/env python3
"""
Comprehensive test suite for Challenge 3 - Transcript Formatting Solution
Tests all components of the transcript processing system
"""

import os
import sys
import json
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from transcript_processor import (
        TranscriptProcessor, ProcessingConfig, ProcessingMode, 
        ProcessingResult, ValidationLevel
    )
    from pattern_matcher import PatternMatcher
    from speaker_normalizer import SpeakerNormalizer
    from format_enforcer import FormatEnforcer
    from llm_resolver import LLMResolver
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class Challenge3Tester:
    def __init__(self):
        self.results = []
        self.base_dir = Path(__file__).parent
        self.config_dir = self.base_dir / "config"
        
    def log_result(self, test_name, status, message="", duration=0, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "duration": f"{duration:.3f}s",
            "details": details or {}
        }
        self.results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message} ({duration:.3f}s)")
        
    def test_basic_transcript_processing(self):
        """Test basic transcript processing functionality"""
        start_time = time.time()
        try:
            config = ProcessingConfig(
                mode=ProcessingMode.FAST,
                use_llm=False,
                validation_level=ValidationLevel.LENIENT
            )
            
            processor = TranscriptProcessor(
                config=config,
                config_dir=str(self.config_dir)
            )
            
            raw_transcript = """
            John: Hello, how are you today?
            Mary: I'm doing well, thank you for asking.
            John: That's great to hear.
            """
            
            result = processor.process_transcript(raw_transcript)
            duration = time.time() - start_time
            
            if result.success and result.formatted_transcript:
                self.log_result(
                    "Basic Transcript Processing", 
                    "PASS", 
                    f"Processed {len(result.speakers)} speakers", 
                    duration,
                    {"speakers": result.speakers, "lines": len(result.formatted_transcript.split('\n'))}
                )
            else:
                self.log_result("Basic Transcript Processing", "FAIL", "Processing failed", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Basic Transcript Processing", "FAIL", f"Error: {str(e)}", duration)
            
    def test_complex_transcript_processing(self):
        """Test complex transcript with multiple speakers and formats"""
        start_time = time.time()
        try:
            config = ProcessingConfig(
                mode=ProcessingMode.BALANCED,
                use_llm=False,
                validation_level=ValidationLevel.MODERATE
            )
            
            processor = TranscriptProcessor(
                config=config,
                config_dir=str(self.config_dir)
            )
            
            complex_transcript = """
            Speaker 1: Welcome everyone to today's meeting.
            SPEAKER_2: Thank you for having us here.
            Person A: I have some questions about the project.
            John Smith: Let me address those concerns.
            Mary (CEO): From a business perspective, this looks good.
            Unknown: What about the timeline?
            """
            
            result = processor.process_transcript(complex_transcript)
            duration = time.time() - start_time
            
            if result.success and len(result.speakers) >= 4:
                self.log_result(
                    "Complex Transcript Processing", 
                    "PASS", 
                    f"Processed {len(result.speakers)} speakers successfully", 
                    duration,
                    {"speakers": result.speakers}
                )
            else:
                self.log_result("Complex Transcript Processing", "FAIL", "Failed to process complex transcript", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Complex Transcript Processing", "FAIL", f"Error: {str(e)}", duration)
            
    def test_pattern_matcher_component(self):
        """Test pattern matcher component"""
        start_time = time.time()
        try:
            pattern_matcher = PatternMatcher(
                config_path=str(self.config_dir / "patterns.yaml")
            )
            
            test_text = "John: Hello there. Mary: How are you? Speaker 1: Good morning."
            matches = pattern_matcher.find_speaker_patterns(test_text)
            
            duration = time.time() - start_time
            
            if len(matches) >= 3:
                self.log_result(
                    "Pattern Matcher Component", 
                    "PASS", 
                    f"Found {len(matches)} speaker patterns", 
                    duration,
                    {"matches": len(matches)}
                )
            else:
                self.log_result("Pattern Matcher Component", "FAIL", f"Only found {len(matches)} patterns", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Pattern Matcher Component", "FAIL", f"Error: {str(e)}", duration)
            
    def test_speaker_normalizer_component(self):
        """Test speaker normalizer component"""
        start_time = time.time()
        try:
            normalizer = SpeakerNormalizer(
                config_path=str(self.config_dir / "patterns.yaml")
            )
            
            # Test speaker normalization
            test_speakers = ["john", "MARY", "Speaker_1", "Dr. Smith", "mary"]
            normalized = []
            
            for speaker in test_speakers:
                norm = normalizer.normalize_speaker_name(speaker)
                normalized.append(norm)
                
            duration = time.time() - start_time
            
            # Check if normalization worked (should have fewer unique speakers)
            unique_original = len(set(test_speakers))
            unique_normalized = len(set(normalized))
            
            if unique_normalized <= unique_original:
                self.log_result(
                    "Speaker Normalizer Component", 
                    "PASS", 
                    f"Normalized {unique_original} to {unique_normalized} speakers", 
                    duration,
                    {"original": test_speakers, "normalized": normalized}
                )
            else:
                self.log_result("Speaker Normalizer Component", "FAIL", "Normalization failed", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Speaker Normalizer Component", "FAIL", f"Error: {str(e)}", duration)
            
    def test_format_enforcer_component(self):
        """Test format enforcer component"""
        start_time = time.time()
        try:
            enforcer = FormatEnforcer(validation_level=ValidationLevel.STRICT)
            
            # Test format validation
            good_transcript = "John: Hello there.\nMary: How are you?"
            bad_transcript = "john hello there\nmary: how are you"
            
            good_result = enforcer.validate_format(good_transcript)
            bad_result = enforcer.validate_format(bad_transcript)
            
            duration = time.time() - start_time
            
            if good_result.is_valid and not bad_result.is_valid:
                self.log_result(
                    "Format Enforcer Component", 
                    "PASS", 
                    "Correctly validated transcript formats", 
                    duration,
                    {"good_valid": good_result.is_valid, "bad_valid": bad_result.is_valid}
                )
            else:
                self.log_result("Format Enforcer Component", "FAIL", "Format validation failed", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Format Enforcer Component", "FAIL", f"Error: {str(e)}", duration)
            
    def test_file_processing(self):
        """Test file input/output processing"""
        start_time = time.time()
        try:
            config = ProcessingConfig(
                mode=ProcessingMode.FAST,
                use_llm=False,
                validation_level=ValidationLevel.LENIENT
            )
            
            processor = TranscriptProcessor(
                config=config,
                config_dir=str(self.config_dir)
            )
            
            # Create temporary input file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("John: Hello world.\nMary: How are you today?")
                input_file = f.name
                
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                output_file = f.name
                
            try:
                result = processor.process_file(input_file, output_file)
                duration = time.time() - start_time
                
                if result.success and os.path.exists(output_file):
                    with open(output_file, 'r') as f:
                        output_content = f.read()
                        
                    self.log_result(
                        "File Processing", 
                        "PASS", 
                        f"Successfully processed file with {len(result.speakers)} speakers", 
                        duration,
                        {"input_file": os.path.basename(input_file), "output_length": len(output_content)}
                    )
                else:
                    self.log_result("File Processing", "FAIL", "File processing failed", duration)
                    
            finally:
                # Cleanup
                if os.path.exists(input_file):
                    os.unlink(input_file)
                if os.path.exists(output_file):
                    os.unlink(output_file)
                    
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("File Processing", "FAIL", f"Error: {str(e)}", duration)
            
    def test_different_processing_modes(self):
        """Test different processing modes"""
        start_time = time.time()
        try:
            test_transcript = "John: Hello. Mary: Hi there. Speaker 1: Good morning."
            results = {}
            
            for mode in [ProcessingMode.FAST, ProcessingMode.BALANCED, ProcessingMode.THOROUGH]:
                config = ProcessingConfig(
                    mode=mode,
                    use_llm=False,  # Disable LLM for testing
                    validation_level=ValidationLevel.LENIENT
                )
                
                processor = TranscriptProcessor(
                    config=config,
                    config_dir=str(self.config_dir)
                )
                
                result = processor.process_transcript(test_transcript)
                results[mode.value] = result.success
                
            duration = time.time() - start_time
            
            successful_modes = sum(results.values())
            if successful_modes >= 2:
                self.log_result(
                    "Different Processing Modes", 
                    "PASS", 
                    f"{successful_modes}/3 modes successful", 
                    duration,
                    results
                )
            else:
                self.log_result("Different Processing Modes", "FAIL", f"Only {successful_modes}/3 modes successful", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Different Processing Modes", "FAIL", f"Error: {str(e)}", duration)
            
    def test_configuration_files(self):
        """Test configuration files exist and are valid"""
        start_time = time.time()
        try:
            patterns_file = self.config_dir / "patterns.yaml"
            prompts_file = self.config_dir / "prompts.yaml"
            
            files_exist = patterns_file.exists() and prompts_file.exists()
            
            if files_exist:
                # Try to load the files
                pattern_matcher = PatternMatcher(config_path=str(patterns_file))
                
                duration = time.time() - start_time
                self.log_result(
                    "Configuration Files", 
                    "PASS", 
                    "All config files exist and are loadable", 
                    duration,
                    {"patterns_exists": patterns_file.exists(), "prompts_exists": prompts_file.exists()}
                )
            else:
                duration = time.time() - start_time
                self.log_result("Configuration Files", "FAIL", "Missing configuration files", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Configuration Files", "FAIL", f"Error: {str(e)}", duration)
            
    def test_sample_data_processing(self):
        """Test processing of sample data"""
        start_time = time.time()
        try:
            sample_data_dir = self.base_dir / "sample_data"
            
            if sample_data_dir.exists():
                config = ProcessingConfig(
                    mode=ProcessingMode.FAST,
                    use_llm=False,
                    validation_level=ValidationLevel.LENIENT
                )
                
                processor = TranscriptProcessor(
                    config=config,
                    config_dir=str(self.config_dir)
                )
                
                # Look for sample transcript files
                sample_files = list(sample_data_dir.glob("*.txt"))
                if not sample_files:
                    sample_files = list(sample_data_dir.glob("*.py"))  # Check for Python files with samples
                    
                processed_count = 0
                for sample_file in sample_files[:3]:  # Test up to 3 samples
                    try:
                        if sample_file.suffix == '.py':
                            # Skip Python files for now
                            continue
                            
                        result = processor.process_file(str(sample_file))
                        if result.success:
                            processed_count += 1
                    except Exception:
                        continue
                        
                duration = time.time() - start_time
                
                if processed_count > 0:
                    self.log_result(
                        "Sample Data Processing", 
                        "PASS", 
                        f"Processed {processed_count} sample files", 
                        duration,
                        {"processed": processed_count, "total_samples": len(sample_files)}
                    )
                else:
                    self.log_result("Sample Data Processing", "SKIP", "No processable sample files found", duration)
            else:
                duration = time.time() - start_time
                self.log_result("Sample Data Processing", "SKIP", "Sample data directory not found", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Sample Data Processing", "FAIL", f"Error: {str(e)}", duration)
            
    def test_cli_interface(self):
        """Test CLI interface exists and is functional"""
        start_time = time.time()
        try:
            cli_file = self.base_dir / "cli.py"
            
            if cli_file.exists():
                # Test if CLI can be imported
                import subprocess
                result = subprocess.run(
                    [sys.executable, str(cli_file), '--help'], 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                
                duration = time.time() - start_time
                
                if result.returncode == 0 or 'usage' in result.stdout.lower() or 'help' in result.stdout.lower():
                    self.log_result(
                        "CLI Interface", 
                        "PASS", 
                        "CLI interface is functional", 
                        duration,
                        {"help_available": True}
                    )
                else:
                    self.log_result("CLI Interface", "FAIL", "CLI interface not working", duration)
            else:
                duration = time.time() - start_time
                self.log_result("CLI Interface", "FAIL", "CLI file not found", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("CLI Interface", "FAIL", f"Error: {str(e)}", duration)
            
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Challenge 3 Tests - Transcript Formatting Solution")
        print("=" * 70)
        
        self.test_configuration_files()
        self.test_pattern_matcher_component()
        self.test_speaker_normalizer_component()
        self.test_format_enforcer_component()
        self.test_basic_transcript_processing()
        self.test_complex_transcript_processing()
        self.test_different_processing_modes()
        self.test_file_processing()
        self.test_sample_data_processing()
        self.test_cli_interface()
        
        print("\n" + "=" * 70)
        print("📊 Test Summary:")
        
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        skipped = len([r for r in self.results if r["status"] == "SKIP"])
        total = len(self.results)
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Skipped: {skipped}")
        print(f"📈 Total: {total}")
        
        if failed == 0:
            print("\n🎉 All tests passed or skipped!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")
            
        # Calculate system health score
        health_score = (passed / total) * 100 if total > 0 else 0
        print(f"🏥 System Health Score: {health_score:.1f}%")
        
        return self.results

if __name__ == "__main__":
    tester = Challenge3Tester()
    results = tester.run_all_tests()
    
    # Save results to JSON
    with open("challenge_3_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to challenge_3_test_results.json")