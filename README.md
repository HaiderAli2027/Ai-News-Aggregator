# AI News Aggregator

An intelligent news aggregation system that collects, processes, and curates content from multiple AI-focused sources including YouTube channels, OpenAI blog, and Anthropic research. The system automatically generates concise digests of articles and video content using the Groq API.

## Overview

AI News Aggregator is a Python-based application designed to keep you updated with the latest developments in artificial intelligence. It aggregates content from YouTube channels, OpenAI, and Anthropic, extracts transcripts from videos, and uses advanced language models to generate meaningful summaries.

## Features

- YouTube channel video scraping with transcript extraction
- RSS feed aggregation from OpenAI and Anthropic
- Automatic digest generation using Groq API (llama-3.3-70b)
- PostgreSQL database for persistent storage
- Docker support for containerized deployment
- Modular architecture with separate scrapers and services
- Content processing pipeline for articles and videos
- RESTful API interface for content management

## Project Structure

```
ai-news-aggregator/
├── app/
│   ├── agent/
│   │   └── digest_agent.py         # Groq-based digest generation
│   ├── database/
│   │   ├── connection.py           # Database connection setup
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   ├── repository.py           # Database access layer
│   │   └── create_tables.py        # Schema initialization
│   ├── scrapers/
│   │   ├── youtube.py              # YouTube scraper with transcripts
│   │   ├── openai.py               # OpenAI RSS feed scraper
│   │   └── anthropic.py            # Anthropic RSS feed scraper
│   ├── services/
│   │   ├── process_digest.py       # Digest processing service
│   │   ├── process_anthropic.py    # Anthropic content processor
│   │   └── process_curator.py      # Content curation service
│   ├── config.py                   # Configuration and channel list
│   └── runner.py                   # Main orchestrator
├── docker/
│   ├── docker-compose.yml          # Docker Compose configuration
│   └── Dockerfile                  # PostgreSQL setup
├── main.py                         # Entry point
├── pyproject.toml                  # Project dependencies
├── .env.example                    # Environment variables template
└── README.md                       # This file
```

## Requirements

- Python 3.12 or higher
- PostgreSQL 17
- Docker Desktop (optional, for containerized setup)
- API keys: Groq

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-news-aggregator
```

### 2. Set Up Python Environment

Using uv (recommended):

```bash
uv venv
.venv\Scripts\activate
```

Or using Python venv:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
uv pip install -e .
```

Or with pip:

```bash
pip install -e .
```

### 4. Environment Configuration

Copy the example environment file:

```bash
cp app/example.env .env
```

Edit `.env` with your configuration:

```
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=ai_news_aggregator
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Obtain API keys from:

- Groq: https://console.groq.com/
- OpenAI: https://platform.openai.com/api-keys

### 5. Set Up PostgreSQL Database

Option A: Using Docker (Recommended)

```bash
cd docker
docker compose up -d
```

Option B: Local PostgreSQL
Ensure PostgreSQL is running and accessible at the configured host and port.

### 6. Initialize Database Schema

```bash
python app/database/create_tables.py
```

This creates the necessary tables:

- youtube_videos
- openai_articles
- anthropic_articles
- digests

## Usage

### Basic Scraping

Run the main scraper to collect content from all sources:

```bash
python main.py
```

Or specify the time window in hours:

```bash
python main.py 48
```

This will scrape content from the last 48 hours.

### Process Digests

Generate AI-powered summaries for collected articles:

```bash
python app/services/process_digest.py
```

### Process Anthropic Content

Extract and process Anthropic research content:

```bash
python app/services/process_anthropic.py
```

### Content Curation

Run the curator service for content recommendations:

```bash
python app/services/process_curator.py
```

## Configuration

### YouTube Channels

Edit `app/config.py` to customize which YouTube channels to monitor:

```python
YOUTUBE_CHANNELS = [
    "UCLKPca3kwwd-B59HNr-_lvA",    # AI Engineer
    "UCKWaEZ-_VweaEx1j62do_vQ",    # IBM Technology
    "UCGKEMK3s-ZPbjVOIuAV8clQ",    # Core Dumped
    # Add more channel IDs as needed
]
```

### Database Configuration

Modify database connection settings in `.env`:

- POSTGRES_HOST: Database server address
- POSTGRES_PORT: Database port (default: 5432)
- POSTGRES_USER: Database user
- POSTGRES_PASSWORD: Database password
- POSTGRES_DB: Database name

## Database Models

### YouTubeVideo

- video_id (Primary Key)
- title
- url
- channel_id
- published_at
- description
- transcript
- created_at

### OpenAIArticle

- guid (Primary Key)
- title
- url
- description
- published_at
- category
- created_at

### AnthropicArticle

- guid (Primary Key)
- title
- url
- description
- published_at
- category
- markdown
- created_at

### Digest

- id (Primary Key)
- article_type
- article_id
- url
- title
- summary
- created_at

## API Keys and Security

Sensitive information should never be committed to version control. The `.gitignore` file ensures that:

- .env files are excluded
- Virtual environments are excluded
- Cache and build files are excluded
- IDE configuration is excluded

Always use environment variables for API keys and credentials.

## Troubleshooting

### Database Connection Error

If you receive "password authentication failed":

1. Verify PostgreSQL is running: docker ps
2. Check credentials in .env match your setup
3. Wait 10 seconds after starting Docker container for initialization
4. Restart the container: docker compose restart

### Missing Transcripts

YouTube videos may not have transcripts if:

- Transcripts are disabled by the channel
- Video is too new
- Transcripts are not available in the target language

These cases are handled gracefully and recorded as NULL.

### API Rate Limiting

Groq API has rate limits. If rate limited:

- Wait before retrying
- Consider batching requests
- Check Groq dashboard for current usage

## Performance Considerations

- Large content processing may take time due to API calls
- Database queries are optimized with appropriate indexes
- Transcript extraction uses caching where possible
- Digest generation batches requests to Groq API

## Contributing

Contributions are welcome. Please follow these guidelines:

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

- YouTube Transcript API: https://pypi.org/project/youtube-transcript-api/
- Groq API Documentation: https://console.groq.com/docs
- SQLAlchemy: https://www.sqlalchemy.org/
- PostgreSQL: https://www.postgresql.org/

## Support

For issues, questions, or suggestions, please open an issue in the repository.
