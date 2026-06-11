# AI News Aggregator - Detailed Concepts & Architecture

## Project Overview

A daily automated AI learning digest system that scrapes content from YouTube, OpenAI, and Anthropic RSS feeds, processes them through AI agents for curation and summarization, and sends personalized email digests based on user learning profile.

---

## Core Concepts & Technologies

### 1. RSS Feed Fundamentals

**RSS (Really Simple Syndication)** - A web technology that lets you receive updates from websites automatically without manual visits. The system uses:

- **YouTube RSS**: Video feed from AI engineering channels
- **OpenAI Blog RSS**: Latest models, tutorials, and research announcements
- **Anthropic Blog RSS**: Papers, tools, and updates from Anthropic

### 2. Web Scraping & Feed Parsing

- **feedparser**: Python library for parsing RSS/Atom feeds
- **Incremental scraping**: Fetches new articles since last run (72-hour lookback window)
- **User-Agent headers**: Prevents blocking by adding realistic browser identification
- **Content extraction**: Pulls title, description, publication date, URL

### 3. Content Processing Pipeline

#### A. **YouTube Transcript Processing**

- Extracts transcripts from YouTube videos using YouTube Data API
- Converts video content into searchable text for AI analysis
- Stores transcript in database for digest generation
- Status tracking: `pending_transcript` → `transcript_fetched` → `summarized`

#### B. **Article Summarization (AI Agents)**

Uses **Groq LLaMA 70B** model with JSON response format:

- **Digest Agent**: Creates structured learning summaries with:
  - `title`: 5-12 word learning focus
  - `summary`: 2-3 sentence technical explanation
  - `key_concepts`: 2-4 learnable terms (e.g., "RAG", "vector embeddings", "FastAPI")

#### C. **Content Curation & Ranking**

- **Curator Agent**: Ranks articles 0.0-10.0 based on learning value
- **Ranking priorities**: YouTube tutorials > technical concepts > new tools > press releases
- **Penalty scoring**: Corporate PR, generic marketing, hype gets <4.0 score
- **Source quotas**: Min 1-2 YouTube, max 2 corporate combined per email

### 4. Email Generation & Templating

- **Email Agent**: Writes personalized greeting + intro using user profile
- **HTML template**: Renders article cards with:
  - Rank, relevance score, source badge (YouTube/OpenAI/Anthropic)
  - Summary with key concepts as chips
  - "Why this is for you" reasoning
  - Read more link
- **Markdown fallback**: Plain text version for email clients

### 5. User Profiling & Personalization

**Haider Ali's Learning Profile:**

- **Background**: Software Engineering student, Python + AI fundamentals focus
- **Interests** (14 key areas):
  - Python & software engineering best practices
  - CS fundamentals: DSA, OOP, system design, software design and architecture
  - LLMs: architecture, training, inference
  - AI agents: multi-agent systems, agentic workflows
  - RAG systems & vector embeddings
  - Generative AI patterns & prompt engineering
  - ML engineering: training, evaluation, deployment
  - MLOps & DevOps for AI
  - Databases & backend (PostgreSQL, APIs)
  - AI tools: Groq, OpenAI, LangChain
  - YouTube tutorials from engineering channels
  - Real-world AI project implementation
  - Latest tools & framework releases
  - Beginner-to-intermediate technical tutorials

- **Preferences**:
  - Practical projects over theory
  - Beginner-friendly explanations with technical depth
  - Hands-on tutorials
  - Latest tools & updates
  - Production-focused content

### 6. Database Schema

**Tables:**

- `youtube_videos`: video_id, title, url, transcript, status, created_at
- `openai_articles`: guid, title, url, published_at, category
- `anthropic_articles`: guid, title, url, published_at, category
- `digests`: article_type, article_id, title, summary, key_concepts, created_at, emailed_at
- Tracks: Which articles are new, processed, and emailed

---

## AI Models & APIs Used

### Groq (LLaMA 3.3 70B)

- **Why Groq**: Fast inference for real-time AI processing
- **Model**: `llama-3.3-70b-versatile`
- **Use cases**:
  - Ranking articles (Curator Agent)
  - Summarizing content (Digest Agent)
  - Writing email introductions (Email Agent)
- **Temperature settings**:
  - Ranking: 0.3 (consistent, deterministic)
  - Summarization: 0.7 (creative but coherent)
  - Introduction: 0.7 (personalized tone)

### YouTube Data API

- Fetches video metadata, transcripts
- Limits: 10,000 quota units/day
- Used for transcript extraction

---

## System Architecture

```
Scraping Layer (External)
├── YouTube RSS → feedparser
├── OpenAI Blog RSS → feedparser
└── Anthropic Blog RSS → feedparser
        ↓
Repository Layer (Database)
├── Store raw videos/articles
├── Track processing status
└── Query unsent digests
        ↓
Processing Layer (AI Agents)
├── Transcript extraction (YouTube)
├── Content summarization (Digest Agent)
├── Ranking & curation (Curator Agent)
└── Source quota enforcement
        ↓
Email Layer (Output)
├── HTML generation
├── User personalization
├── Email Agent (intro writer)
└── Send via Gmail SMTP
```

---

## Key Processing Steps (Daily Run)

1. **Scrape**: Fetch last 72 hours from all RSS feeds
2. **Extract Transcripts**: Get YouTube video transcripts
3. **Summarize**: AI-generated digest for each article
4. **Rank**: Curator agent scores all digests
5. **Apply Quota**: Enforce min YouTube + max corporate limits
6. **Select Top 10**: Pick best ranked articles
7. **Write Intro**: Email agent personalizes greeting
8. **Generate HTML**: Build styled email with cards
9. **Send**: Gmail SMTP delivery
10. **Mark Emailed**: Update emailed_at timestamp

---

## Important Configuration Parameters

| Parameter       | Current Value           | Purpose                            |
| --------------- | ----------------------- | ---------------------------------- |
| Scrape Hours    | 72                      | Look-back window for RSS feeds     |
| Top N Articles  | 10                      | Articles sent per email            |
| Min YouTube     | Adaptive (1-2)          | YouTube tutorial minimum           |
| Max Corporate   | 2                       | Cap on OpenAI + Anthropic combined |
| Groq Model      | llama-3.3-70b-versatile | AI ranking/summarization           |
| Email Recipient | User's Gmail            | Delivery destination               |
| Schedule        | Daily 3 AM UTC          | Automated trigger (GitHub Actions) |

---

## Unique Concepts for Learning

### LLM Concepts Used

- **JSON Mode**: Groq forced JSON output for structured agent responses
- **Prompt Engineering**: System prompts tuned for ranking, summarization, personalization
- **Temperature Control**: 0.3 (deterministic) vs 0.7 (creative) for different tasks
- **Pydantic Models**: Type validation for AI outputs

### Engineering Concepts

- **RSS Feed Parsing**: Incremental updates, date filtering, deduplication
- **Repository Pattern**: Abstract database access from business logic
- **Agent Architecture**: Specialized agents for ranking, digesting, emailing
- **Source Quota Pattern**: Filter ranked results by content source constraints
- **Email Template Engine**: Dynamic HTML generation with inline CSS

### Data Processing

- **Transcript Extraction**: Convert video content to text for AI analysis
- **Key Concept Extraction**: Parse AI-generated concepts from summaries
- **Status Tracking**: Pipeline progress tracking (pending → processed → emailed)
- **Deduplication**: Avoid re-processing same RSS items

### Automation & Deployment

- **GitHub Actions**: Scheduled CRON jobs for daily execution
- **Environment Variables**: Secure API key management (.env)
- **Exit Codes**: Success/failure signaling for CI/CD
- **Logging**: Structured logs for debugging & monitoring


---

## How to Run

```bash
# Local test (24 hours, 10 articles)
python main.py

# Custom window (72 hours, 5 articles)
python main.py 72 5

# Production (via GitHub Actions daily at 3 AM UTC)
# Configured in .github/workflows/daily-scraper.yml
```

---

**Last Updated:** June 7, 2026  
**User Profile:** Haider Ali (Aspiring AI Engineer & Python Developer)
