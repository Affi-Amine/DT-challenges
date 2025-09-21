# DiploTools Internship Challenges

Welcome to the DiploTools internship technical challenges repository. This repository contains three distinct challenges showcasing different aspects of software development, automation, and data processing.

## 📁 Repository Structure

```
DiploTools internship/
├── challenge_1/          # Document Processing & Search System
├── challenge_2/          # Automated Cron Job System  
├── challenge_3/          # Transcript Formatting Solution
├── README.md            # This file
└── .gitignore           # Git ignore rules
```

## 🎯 Challenge Overview

### Challenge 1: Intelligent Document Processing & Search System
**Technology Stack**: Python, FastAPI, PostgreSQL, Redis, Docker  
**Focus**: Backend development, API design, database optimization, vector search

A sophisticated document processing pipeline designed for diplomatic content with:
- Multi-format document processing (PDF, DOCX, Markdown, TXT)
- Semantic search with vector embeddings
- Intelligent chunking and metadata extraction
- RESTful API with FastAPI
- Docker containerization

**Key Features**:
- Hybrid search (semantic + keyword)
- Multiple embedding providers (OpenAI, Gemini, local)
- Redis caching layer
- Comprehensive API documentation

### Challenge 2: Automated Cron Job System
**Technology Stack**: Python, Cron, System Administration  
**Focus**: System automation, scheduling, monitoring, notifications

A robust cron job system that executes scripts at random intervals with:
- Automated installation and configuration
- Comprehensive logging and monitoring
- iPhone push notifications via Pushover
- Email notifications for failures
- Configurable execution parameters

**Key Features**:
- 10 daily executions at random times
- Automatic log rotation and cleanup
- Multi-channel notifications
- Error handling and recovery

### Challenge 3: Transcript Formatting Solution
**Technology Stack**: Python, Regex, OpenAI API, CLI  
**Focus**: Text processing, pattern matching, AI integration

An intelligent transcript formatter that converts unstructured text to speaker-labeled format:
- Regex-based speaker detection
- Speaker name normalization
- Optional LLM enhancement for ambiguous cases
- Batch processing capabilities
- Command-line interface

**Key Features**:
- Configurable pattern matching
- Smart speaker grouping
- Format validation
- Comprehensive test suite

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+ (3.13+ recommended)
- Docker and Docker Compose (for Challenge 1)
- Git
- macOS/Linux environment

### Getting Started

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "DiploTools internship"
   ```

2. **Choose a challenge to explore**:
   ```bash
   cd challenge_1  # or challenge_2, challenge_3
   ```

3. **Follow the specific README in each challenge folder for detailed setup instructions**

## 📖 Detailed Setup Instructions

### Challenge 1: Document Processing System

```bash
cd challenge_1

# Option 1: Docker (Recommended)
docker-compose up -d

# Option 2: Local Setup
pip install -r requirements.txt
# Configure PostgreSQL and Redis
# Set environment variables in .env
python src/main.py
```

**Testing the API**:
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`
- Upload Document: `POST /documents/upload`
- Search: `GET /search?query=your_query`

### Challenge 2: Cron Job System

```bash
cd challenge_2

# Install and configure
python3 setup.py --install

# Configure notifications (optional)
cp config/.env.template config/.env
# Edit config/.env with your Pushover/email credentials

# Manual test run
python3 scripts/daily_scheduler.py
```

**Monitoring**:
- Logs: `logs/` directory
- Cron status: `crontab -l`
- Execution history: `logs/scheduler_*.log`

### Challenge 3: Transcript Formatter

```bash
cd challenge_3

# Install dependencies
pip install -r requirements.txt

# Basic usage
python cli.py test_transcript.txt -o formatted_output.txt

# With LLM enhancement (requires OpenAI API key)
export OPENAI_API_KEY="your-key-here"
python cli.py test_transcript.txt -o formatted_output.txt --use-llm

# Batch processing
python cli.py *.txt --batch-output ./formatted/
```

## 🧪 Testing

Each challenge includes comprehensive tests:

### Challenge 1
```bash
cd challenge_1
pytest tests/ -v
```

### Challenge 2
```bash
cd challenge_2
python -m pytest tests/ -v
```

### Challenge 3
```bash
cd challenge_3
python -m pytest tests/ -v
```

## 🔧 Configuration

Each challenge supports extensive configuration:

- **Challenge 1**: Environment variables, Docker Compose overrides
- **Challenge 2**: YAML configuration files, environment variables
- **Challenge 3**: YAML pattern files, CLI arguments

## 📝 Documentation

Detailed documentation is available in each challenge folder:

- `challenge_1/challenge_1_documentation.md` - Complete API and architecture docs
- `challenge_2/README.md` - System administration guide
- `challenge_3/README.md` - Usage examples and API reference

## 🛠️ Development Environment

**Recommended IDE Setup**:
- VS Code with Python extension
- Docker extension for Challenge 1
- REST Client extension for API testing

**Code Quality**:
- All code follows PEP 8 standards
- Comprehensive error handling
- Extensive logging and monitoring
- Type hints throughout

## 📞 Support & Troubleshooting

**Common Issues**:

1. **Challenge 1**: Database connection issues
   - Ensure PostgreSQL is running
   - Check connection strings in `.env`

2. **Challenge 2**: Cron job not executing
   - Verify cron service is running: `sudo service cron status`
   - Check cron logs: `grep CRON /var/log/syslog`

3. **Challenge 3**: Poor speaker detection
   - Adjust patterns in `config/patterns.yaml`
   - Enable LLM enhancement for better accuracy

**Getting Help**:
- Check individual README files for detailed troubleshooting
- Review solution design documents for architecture insights
- Examine test files for usage examples

## 🎉 Demo Data

Each challenge includes sample data for immediate testing:

- **Challenge 1**: UN diplomatic transcripts in `sample_data/`
- **Challenge 2**: Configured with sample target script
- **Challenge 3**: Various transcript formats in `sample_data/`# DT-challenges
