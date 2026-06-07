import os
import json
from typing import List
from groq import Groq
from pydantic import BaseModel, Field
from dotenv import load_dotenv

CURATOR_PROMPT = """You are an expert learning curator for a beginner-to-intermediate AI engineer.

Your job is to rank content for a daily LEARNING digest — not a corporate news roundup.

Ranking priorities (highest first):
1. YouTube tutorials, walkthroughs, and architecture explainers
2. Content that teaches concepts: RAG, agents, embeddings, fine-tuning, MLOps, DevOps, DSA, system design
3. New tools, libraries, and frameworks with practical "how to use" value
4. Technical research or engineering posts (not press releases)

Strongly PENALIZE (score below 4.0):
- Corporate PR: product launches, partner networks, IPO/S-1, enterprise customer stories
- Generic marketing: "AI transforms productivity", "excited to share", "revolutionizing"
- OpenAI/Anthropic announcements unless genuinely technical and educational

Source guidance:
- youtube: primary learning source — boost scores for tutorial/educational videos
- openai / anthropic: only rank highly if the reader will learn a concept, pattern, or technique

Scoring Guidelines:
- 9.0-10.0: Perfect tutorial/concept match for a growing engineer
- 7.0-8.9: Strong learning value, clear technical takeaway
- 5.0-6.9: Some learning value but partial fit
- 3.0-4.9: Mostly news/PR with little learning value
- 0.0-2.9: Corporate hype or irrelevant

Rank articles from most relevant (rank 1) to least relevant. Each article gets a unique rank.

IMPORTANT: Respond ONLY with a valid JSON object in this exact format (no markdown, no extra text):
{
  "articles": [
    {
      "digest_id": "article_type:article_id",
      "relevance_score": 8.5,
      "rank": 1,
      "reasoning": "explanation here"
    }
  ]
}"""

load_dotenv()


class RankedArticle(BaseModel):
    digest_id: str = Field(description="The ID of the digest (article_type:article_id)")
    relevance_score: float = Field(description="Relevance score from 0.0 to 10.0", ge=0.0, le=10.0)
    rank: int = Field(description="Rank position (1 = most relevant)", ge=1)
    reasoning: str = Field(description="Brief explanation of why this article is ranked here")


class RankedDigestList(BaseModel):
    articles: List[RankedArticle] = Field(description="List of ranked articles")


class CuratorAgent:
    def __init__(self, user_profile: dict):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.user_profile = user_profile
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        interests = "\n".join(f"- {interest}" for interest in self.user_profile["interests"])
        preferences = self.user_profile["preferences"]
        pref_text = "\n".join(f"- {k}: {v}" for k, v in preferences.items())

        return f"""{CURATOR_PROMPT}

User Profile:
Name: {self.user_profile["name"]}
Background: {self.user_profile["background"]}
Expertise Level: {self.user_profile["expertise_level"]}

Interests:
{interests}

Preferences:
{pref_text}"""

    def rank_digests(self, digests: List[dict]) -> List[RankedArticle]:
        if not digests:
            return []

        digest_list = "\n\n".join([
            f"ID: {d['id']}\nTitle: {d['title']}\nSummary: {d['summary']}\nType: {d['article_type']}"
            for d in digests
        ])

        user_prompt = f"""Rank these {len(digests)} items for a daily LEARNING digest (not corporate news):

{digest_list}

Provide a relevance score (0.0-10.0) and rank (1-{len(digests)}) for each item, ordered from most to least relevant for learning."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)
            ranked_list = RankedDigestList(**data)
            return ranked_list.articles if ranked_list else []

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return []
        except Exception as e:
            print(f"Error ranking digests: {e}")
            return []
