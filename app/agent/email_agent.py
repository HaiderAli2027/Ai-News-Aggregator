import os
import json
from datetime import datetime
from typing import List, Optional
from groq import Groq
from pydantic import BaseModel, Field
from dotenv import load_dotenv

EMAIL_PROMPT = """You are a friendly mentor writing the intro for a daily AI learning digest email.

The reader is a beginner-to-intermediate engineer who wants:
- Clear CS and AI engineering concepts
- Practical tutorials and tool discoveries
- NOT corporate product launch news

Write a warm, human introduction that:
- Greets the user by name with today's date
- Previews what they will learn today (concepts, tools, tutorials)
- Sounds like a helpful senior engineer, not a marketing newsletter
- Stays concise: 2-3 sentences for the introduction body

Avoid corporate tone and hype. Focus on learning outcomes.

IMPORTANT: Respond ONLY with a valid JSON object in this exact format (no markdown, no extra text):
{"greeting": "your greeting here", "introduction": "your introduction here"}"""

load_dotenv()


class EmailIntroduction(BaseModel):
    greeting: str = Field(description="Personalized greeting with user's name and date")
    introduction: str = Field(description="2-3 sentence overview of today's learning picks")


class RankedArticleDetail(BaseModel):
    digest_id: str
    rank: int
    relevance_score: float
    title: str
    summary: str
    url: str
    article_type: str
    reasoning: Optional[str] = None


class EmailDigestResponse(BaseModel):
    introduction: EmailIntroduction
    articles: List[RankedArticleDetail]
    total_ranked: int
    top_n: int

    def to_markdown(self) -> str:
        lines = [
            self.introduction.greeting,
            "",
            self.introduction.introduction,
            "",
            "---",
            "",
        ]

        for article in self.articles:
            if not article.title or not article.url:
                continue
            lines.append(f"## #{article.rank} {article.title}")
            lines.append("")
            if article.reasoning:
                lines.append(f"*Why this is for you:* {article.reasoning}")
                lines.append("")
            lines.append(article.summary)
            lines.append("")
            lines.append(f"[Read more]({article.url})")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)


class EmailDigest(BaseModel):
    introduction: EmailIntroduction
    ranked_articles: List[dict] = Field(description="Top ranked articles with their details")


class EmailAgent:
    def __init__(self, user_profile: dict):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.user_profile = user_profile

    def generate_introduction(self, ranked_articles: List) -> EmailIntroduction:
        current_date = datetime.now().strftime("%B %d, %Y")

        if not ranked_articles:
            return EmailIntroduction(
                greeting=f"Hey {self.user_profile['name']}, here is your daily learning digest for {current_date}.",
                introduction="No new learning content today.",
            )

        top_articles = ranked_articles[:10]
        article_summaries = "\n".join([
            f"{idx + 1}. {article.title if hasattr(article, 'title') else article.get('title', 'N/A')} "
            f"(Score: {article.relevance_score if hasattr(article, 'relevance_score') else article.get('relevance_score', 0):.1f}/10)"
            for idx, article in enumerate(top_articles)
        ])

        user_prompt = f"""Create a learning digest email introduction for {self.user_profile['name']} for {current_date}.

Today's picks (tutorials, concepts, tools):
{article_summaries}

The reader is a beginner-to-intermediate engineer learning AI engineering concepts — not reading corporate news."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": EMAIL_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )

            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)
            intro = EmailIntroduction(**data)

            if not intro.greeting.startswith(f"Hey {self.user_profile['name']}"):
                intro.greeting = (
                    f"Hey {self.user_profile['name']}, here is your daily learning digest for {current_date}."
                )

            return intro

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return self._fallback_introduction(current_date)
        except Exception as e:
            print(f"Error generating introduction: {e}")
            return self._fallback_introduction(current_date)

    def _fallback_introduction(self, current_date: str) -> EmailIntroduction:
        return EmailIntroduction(
            greeting=f"Hey {self.user_profile['name']}, here is your daily learning digest for {current_date}.",
            introduction="Here are today's top picks to help you learn AI engineering concepts and tools.",
        )

    def create_email_digest(self, ranked_articles: List[dict], limit: int = 10) -> EmailDigest:
        top_articles = ranked_articles[:limit]
        introduction = self.generate_introduction(top_articles)
        return EmailDigest(introduction=introduction, ranked_articles=top_articles)

    def create_email_digest_response(
        self, ranked_articles: List[RankedArticleDetail], total_ranked: int, limit: int = 10
    ) -> EmailDigestResponse:
        top_articles = [a for a in ranked_articles[:limit] if a.title and a.url]
        introduction = self.generate_introduction(top_articles)
        return EmailDigestResponse(
            introduction=introduction,
            articles=top_articles,
            total_ranked=total_ranked,
            top_n=limit,
        )
