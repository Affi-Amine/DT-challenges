# Transcript Formatting Solution

A comprehensive Python solution for converting unformatted transcripts into structured, speaker-labeled format using regex patterns and optional LLM enhancement.

## Features

- **Regex-based Pattern Recognition**: Fast and accurate speaker identification using configurable patterns
- **Speaker Name Normalization**: Intelligent grouping and normalization of speaker variations
- **Format Enforcement**: Ensures consistent output formatting with validation
- **LLM Enhancement**: Optional OpenAI integration for handling ambiguous cases
- **Batch Processing**: Process multiple files efficiently
- **Comprehensive Testing**: Full test suite with sample data
- **CLI Interface**: Easy-to-use command-line interface

## Installation

1. Clone or download the project:
```bash
cd challenge_3
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up OpenAI API key for LLM features:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Quick Start

### Basic Usage

Process a single transcript file:
```bash
python cli.py input.txt -o output.txt
```

Process with LLM enhancement:
```bash
python cli.py input.txt -o output.txt --use-llm
```

### Batch Processing

Process multiple files:
```bash
python cli.py file1.txt file2.txt file3.txt --batch-output ./formatted/
```

### Testing

Test all components:
```bash
python cli.py --test-components
```

Test with sample data:
```bash
python cli.py --test-samples
```

List available samples:
```bash
python cli.py --list-samples
```

## Command-Line Options

### Input/Output
- `input_files`: Input transcript file(s) to process
- `-o, --output`: Output file path (for single file processing)
- `--batch-output`: Output directory for batch processing

### Processing Configuration
- `-m, --mode`: Processing mode (`fast`, `balanced`, `thorough`)
- `--confidence-threshold`: Confidence threshold for pattern matching (default: 0.8)
- `--use-llm`: Enable LLM-based resolution for ambiguous cases
- `--api-key`: OpenAI API key
- `--max-speakers`: Maximum number of speakers to expect (default: 30)

### Format Options
- `--validation-level`: Validation level (`basic`, `strict`)
- `--numbered-speakers`: Convert speaker names to numbered format
- `--disable-normalization`: Disable speaker name normalization
- `--disable-format-enforcement`: Disable format enforcement

### Output Options
- `--verbose, -v`: Enable verbose output
- `--quiet, -q`: Suppress all output except errors
- `--json-output`: Output results in JSON format
- `--stats`: Show processing statistics

## Usage Examples

### Example 1: Basic Processing
```bash
python cli.py transcript.txt -o formatted.txt
```

Input:
```
John: Hello, how are you today?
Mary: I'm doing well, thanks for asking.
John: That's great to hear!
```

Output:
```
John: Hello, how are you today?
Mary: I'm doing well, thanks for asking.
John: That's great to hear!
```

### Example 2: Complex Transcript with Noise
```bash
python cli.py messy_transcript.txt -o clean.txt --mode thorough
```

Input:
```
[Background noise] JOHN SMITH - Hey there!
mary_jones: Hi John! [cough]
JOHN SMITH: How's it going?
[Phone rings] mary_jones - Pretty good, thanks!
```

Output:
```
John Smith: Hey there!
Mary Jones: Hi John!
John Smith: How's it going?
Mary Jones: Pretty good, thanks!
```

### Example 3: Numbered Speakers
```bash
python cli.py transcript.txt --numbered-speakers -o numbered.txt
```

Output:
```
Speaker 1: Hello, how are you today?
Speaker 2: I'm doing well, thanks for asking.
Speaker 1: That's great to hear!
```

### Example 4: Batch Processing with Statistics
```bash
python cli.py *.txt --batch-output ./formatted/ --stats --verbose
```

## Configuration

The solution uses YAML configuration files in the `config/` directory:

### patterns.yaml
Contains regex patterns for speaker identification:
- Speaker patterns with confidence scores
- Edge case patterns
- Noise patterns to filter out
- Normalization rules

### prompts.yaml
Contains LLM prompt templates for:
- Speaker identification
- Boundary detection
- Validation tasks

## Architecture

The solution consists of several key components:

1. **PatternMatcher** (`src/pattern_matcher.py`): Regex-based pattern recognition
2. **SpeakerNormalizer** (`src/speaker_normalizer.py`): Speaker name normalization
3. **FormatEnforcer** (`src/format_enforcer.py`): Output format validation and enforcement
4. **LLMResolver** (`src/llm_resolver.py`): OpenAI-based ambiguity resolution
5. **TranscriptProcessor** (`src/transcript_processor.py`): Main orchestration class

## Processing Modes

### Fast Mode
- Basic regex patterns only
- Minimal normalization
- Fastest processing

### Balanced Mode (Default)
- Full regex pattern matching
- Speaker normalization
- Format enforcement
- Good balance of speed and accuracy

### Thorough Mode
- All regex patterns
- Advanced normalization
- Optional LLM enhancement
- Comprehensive validation
- Highest accuracy

## API Usage

You can also use the solution programmatically:

```python
from src.transcript_processor import TranscriptProcessor, ProcessingConfig

# Create processor
config = ProcessingConfig(use_llm=True)
processor = TranscriptProcessor(config=config, api_key="your-api-key")

# Process transcript
result = processor.process_transcript("John: Hello\nMary: Hi there!")

if result.success:
    print(result.formatted_transcript)
    print(f"Speakers: {result.speakers}")
```

## Testing

Run the test suite:
```bash
pytest tests/
```

Run specific test files:
```bash
pytest tests/test_pattern_matcher.py
pytest tests/test_transcript_processor.py
pytest tests/test_integration.py
```

## Sample Data

The `sample_data/` directory contains various sample transcripts for testing:
- Basic conversations
- Edge cases (multiple formats, noise, etc.)
- Challenging scenarios

Access samples programmatically:
```python
from sample_data.sample_transcripts import get_samples_by_difficulty

easy_samples = get_samples_by_difficulty('easy')
```

## Error Handling

The solution provides comprehensive error handling:
- Invalid input format detection
- Missing speaker identification
- API failures (for LLM mode)
- Configuration errors

Errors are reported with detailed messages and suggestions for resolution.

## Performance

- **Fast mode**: ~1000 lines/second
- **Balanced mode**: ~500 lines/second  
- **Thorough mode**: ~200 lines/second (without LLM)
- **LLM mode**: Depends on API response times

## Limitations

- Requires clear speaker indicators in the input
- LLM mode requires internet connection and API key
- Very noisy transcripts may need manual preprocessing
- Performance scales with transcript length and complexity

## Contributing

1. Follow the existing code style (use `black` for formatting)
2. Add tests for new features
3. Update documentation as needed
4. Ensure all tests pass before submitting

## License

This project is part of a technical challenge and is provided as-is for evaluation purposes.

## Support

For issues or questions, please refer to the test cases and sample data for expected behavior and usage patterns.