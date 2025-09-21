#!/usr/bin/env python3
"""
Command-line interface for the Transcript Formatting Solution.
Provides easy access to all functionality through command-line arguments.
"""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from transcript_processor import (
    TranscriptProcessor, ProcessingConfig, ProcessingMode, ValidationLevel
)


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Transcript Formatting Solution - Convert unformatted transcripts to structured format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single file
  python cli.py input.txt -o output.txt
  
  # Process with specific mode
  python cli.py input.txt -m balanced --use-llm
  
  # Batch process multiple files
  python cli.py file1.txt file2.txt file3.txt --batch-output ./formatted/
  
  # Process with numbered speakers
  python cli.py input.txt --numbered-speakers
  
  # Test with sample data
  python cli.py --test-samples
  
  # Run component tests
  python cli.py --test-components
        """
    )
    
    # Input/Output arguments
    parser.add_argument(
        'input_files',
        nargs='*',
        help='Input transcript file(s) to process'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file path (for single file processing)'
    )
    
    parser.add_argument(
        '--batch-output',
        type=str,
        help='Output directory for batch processing'
    )
    
    # Processing configuration
    parser.add_argument(
        '-m', '--mode',
        choices=['fast', 'balanced', 'thorough'],
        default='balanced',
        help='Processing mode (default: balanced)'
    )
    
    parser.add_argument(
        '--confidence-threshold',
        type=float,
        default=0.8,
        help='Confidence threshold for pattern matching (default: 0.8)'
    )
    
    parser.add_argument(
        '--use-llm',
        action='store_true',
        help='Enable LLM-based resolution for ambiguous cases'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='OpenAI API key (or set OPENAI_API_KEY environment variable)'
    )
    
    parser.add_argument(
        '--max-speakers',
        type=int,
        default=30,
        help='Maximum number of speakers to expect (default: 30)'
    )
    
    # Format options
    parser.add_argument(
        '--validation-level',
        choices=['basic', 'strict'],
        default='strict',
        help='Validation level for output format (default: strict)'
    )
    
    parser.add_argument(
        '--numbered-speakers',
        action='store_true',
        help='Convert speaker names to numbered format (Speaker 1, Speaker 2, etc.)'
    )
    
    parser.add_argument(
        '--disable-normalization',
        action='store_true',
        help='Disable speaker name normalization'
    )
    
    parser.add_argument(
        '--disable-format-enforcement',
        action='store_true',
        help='Disable format enforcement'
    )
    
    # Configuration
    parser.add_argument(
        '--config-dir',
        type=str,
        help='Directory containing configuration files'
    )
    
    # Output options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    parser.add_argument(
        '--json-output',
        action='store_true',
        help='Output results in JSON format'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show processing statistics'
    )
    
    # Testing and utilities
    parser.add_argument(
        '--test-components',
        action='store_true',
        help='Test all components and exit'
    )
    
    parser.add_argument(
        '--test-samples',
        action='store_true',
        help='Process sample transcripts and show results'
    )
    
    parser.add_argument(
        '--list-samples',
        action='store_true',
        help='List available sample transcripts'
    )
    
    parser.add_argument(
        '--sample',
        type=str,
        help='Process a specific sample transcript by name'
    )
    
    return parser


def create_processing_config(args) -> ProcessingConfig:
    """Create processing configuration from command-line arguments."""
    # Map string mode to enum
    mode_map = {
        'fast': ProcessingMode.FAST,
        'balanced': ProcessingMode.BALANCED,
        'thorough': ProcessingMode.THOROUGH
    }
    
    validation_map = {
        'basic': ValidationLevel.LENIENT,
        'strict': ValidationLevel.STRICT
    }
    
    return ProcessingConfig(
        mode=mode_map[args.mode],
        confidence_threshold=args.confidence_threshold,
        use_llm=args.use_llm,
        max_speakers=args.max_speakers,
        validation_level=validation_map[args.validation_level],
        enable_speaker_normalization=not args.disable_normalization,
        enable_format_enforcement=not args.disable_format_enforcement,
        output_numbered_speakers=args.numbered_speakers
    )


def print_result(result, args, filename=None):
    """Print processing result based on output options."""
    if args.quiet:
        return
    
    if args.json_output:
        result_dict = {
            'filename': filename,
            'success': result.success,
            'speakers': result.speakers,
            'processing_stats': result.processing_stats,
            'validation_result': result.validation_result,
            'errors': result.errors or [],
            'warnings': result.warnings or []
        }
        print(json.dumps(result_dict, indent=2))
    else:
        # Text output
        if filename:
            print(f"\n{'='*60}")
            print(f"Processing: {filename}")
            print(f"{'='*60}")
        
        if result.success:
            print("✅ Processing successful!")
            print(f"Speakers found: {', '.join(result.speakers)}")
            
            if args.stats:
                print(f"\nStatistics:")
                for key, value in result.processing_stats.items():
                    print(f"  {key}: {value}")
            
            if args.verbose and result.validation_result:
                print(f"\nValidation:")
                validation = result.validation_result.get('format_validation', {})
                print(f"  Valid format: {validation.get('is_valid', 'Unknown')}")
                print(f"  Line count: {validation.get('line_count', 'Unknown')}")
                print(f"  Speaker count: {validation.get('speaker_count', 'Unknown')}")
        else:
            print("❌ Processing failed!")
            if result.errors:
                print("Errors:")
                for error in result.errors:
                    print(f"  - {error}")
        
        if result.warnings and args.verbose:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")


def test_components(processor):
    """Test all components and print results."""
    print("Testing components...")
    results = processor.test_components()
    
    print(f"\n{'Component':<20} {'Status':<10}")
    print("-" * 30)
    
    for component, status in results.items():
        status_str = "✅ OK" if status else "❌ FAIL"
        print(f"{component:<20} {status_str:<10}")
    
    all_working = all(results.values())
    print(f"\nOverall status: {'✅ All components working' if all_working else '❌ Some components failed'}")
    
    return all_working


def test_samples(processor, args):
    """Test with sample transcripts."""
    try:
        sys.path.insert(0, str(Path(__file__).parent / "sample_data"))
        import sample_transcripts
        
        if args.list_samples:
            print("Available sample transcripts:")
            for name in sample_transcripts.get_all_sample_names():
                print(f"  - {name}")
            return
        
        if args.sample:
            # Process specific sample
            transcript = sample_transcripts.get_sample_by_name(args.sample)
            if not transcript:
                print(f"❌ Sample '{args.sample}' not found")
                return
            
            print(f"Processing sample: {args.sample}")
            result = processor.process_transcript(transcript)
            print_result(result, args, args.sample)
            
            if result.success and not args.quiet:
                print(f"\nFormatted output:")
                print("-" * 40)
                print(result.formatted_transcript)
        else:
            # Test easy samples
            easy_samples = sample_transcripts.get_samples_by_difficulty('easy')
            print(f"Testing {len(easy_samples)} easy samples...")
            
            successful = 0
            for i, transcript in enumerate(easy_samples):
                result = processor.process_transcript(transcript)
                if result.success:
                    successful += 1
                    if args.verbose:
                        print(f"✅ Sample {i+1}: {len(result.speakers)} speakers found")
                else:
                    print(f"❌ Sample {i+1}: Failed")
            
            print(f"\nResults: {successful}/{len(easy_samples)} samples processed successfully")
    
    except ImportError:
        print("❌ Sample transcripts not available")


def main():
    """Main CLI function."""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Handle special commands first
    if args.test_components or args.test_samples or args.list_samples or args.sample:
        config = create_processing_config(args)
        # Use appropriate API key based on LLM provider
        api_key = args.api_key
        if not api_key:
            # Check for provider-specific API key
            provider = os.getenv('LLM_PROVIDER', 'openai')
            if provider == 'gemini':
                api_key = os.getenv('GEMINI_API_KEY')
            else:
                api_key = os.getenv('OPENAI_API_KEY')
        
        try:
            processor = TranscriptProcessor(
                config=config,
                config_dir=args.config_dir,
                api_key=api_key
            )
        except Exception as e:
            print(f"❌ Failed to initialize processor: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        if args.test_components:
            # For component testing, we need to enable LLM to test the LLM resolver
            config.use_llm = True
            # Recreate processor with LLM enabled
            try:
                processor = TranscriptProcessor(
                    config=config,
                    config_dir=args.config_dir,
                    api_key=api_key
                )
            except Exception as e:
                print(f"❌ Failed to re-initialize processor for testing: {e}")
                import traceback
                traceback.print_exc()
                return 1
            
            success = test_components(processor)
            return 0 if success else 1
        
        if args.test_samples or args.list_samples or args.sample:
            test_samples(processor, args)
            return 0
    
    # Validate input files
    if not args.input_files:
        print("❌ No input files specified")
        parser.print_help()
        return 1
    
    # Check input files exist
    for input_file in args.input_files:
        if not os.path.exists(input_file):
            print(f"❌ Input file not found: {input_file}")
            return 1
    
    # Create processor
    config = create_processing_config(args)
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    
    if config.use_llm and not api_key:
        print("❌ LLM mode requires OpenAI API key. Set --api-key or OPENAI_API_KEY environment variable.")
        return 1
    
    try:
        processor = TranscriptProcessor(
            config=config,
            config_dir=args.config_dir,
            api_key=api_key
        )
    except Exception as e:
        print(f"❌ Failed to initialize processor: {e}")
        return 1
    
    # Process files
    if len(args.input_files) == 1 and not args.batch_output:
        # Single file processing
        input_file = args.input_files[0]
        result = processor.process_file(input_file, args.output)
        
        print_result(result, args, input_file)
        
        if result.success and args.output:
            print(f"✅ Output written to: {args.output}")
        elif result.success and not args.quiet:
            print(f"\nFormatted transcript:")
            print("-" * 40)
            print(result.formatted_transcript)
        
        return 0 if result.success else 1
    
    else:
        # Batch processing
        if args.batch_output:
            os.makedirs(args.batch_output, exist_ok=True)
        
        results = processor.batch_process(args.input_files, args.batch_output)
        
        # Print individual results
        for result, input_file in zip(results, args.input_files):
            print_result(result, args, input_file)
        
        # Print summary
        if not args.quiet:
            summary = processor.get_processing_summary(results)
            print(f"\n{'='*60}")
            print("BATCH PROCESSING SUMMARY")
            print(f"{'='*60}")
            print(f"Total files: {summary['total_files']}")
            print(f"Successful: {summary['successful']}")
            print(f"Failed: {summary['failed']}")
            print(f"Success rate: {summary['success_rate']:.1%}")
            print(f"Average speakers per file: {summary['average_speakers_per_file']:.1f}")
            
            if args.batch_output:
                print(f"Output directory: {args.batch_output}")
        
        return 0 if summary['success_rate'] == 1.0 else 1


if __name__ == '__main__':
    sys.exit(main())