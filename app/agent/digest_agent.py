import os
import json
from typing import List, Optional
from groq import Groq
from pydantic import BaseModel, Field
from dotenv import load_dotenv

DIGEST_PROMPT = """You are a technical educator summarizing content for a beginner-to-intermediate AI engineer who wants to clear concepts and learn new tools.

Create a learning-focused digest — not marketing copy.

Guidelines:
- Title (5-12 words): state the concept, tool, or skill the reader will learn
- Summary: 2-3 sentences in plain, friendly language explaining what this teaches and why it matters for learning
- key_concepts: 2-4 short terms the reader should look up or remember (e.g. "RAG", "vector embeddings", "FastAPI")
- Focus on engineering perspective: how things work, when to use them, what problem they solve
- Avoid hype words: "revolutionizing", "transforming", "game-changing", "excited to announce"
- For YouTube: emphasize what the viewer will learn step-by-step
- For articles: extract the core technical idea, not the company's announcement

IMPORTANT: Respond ONLY with a valid JSON object in this exact format (no markdown, no extra text):
{"title": "your title here", "summary": "your summary here", "key_concepts": ["concept1", "concept2"]}"""

load_dotenv()


class DigestOutput(BaseModel):
    title: str
    summary: str
    key_concepts: List[str] = Field(default_factory=list)


class DigestAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"
        self.system_prompt = DIGEST_PROMPT

    def format_summary(self, digest: DigestOutput) -> str:
        summary = digest.summary.strip()
        if digest.key_concepts:
            concepts = ", ".join(digest.key_concepts)
            summary = f"{summary}\n\nKey concepts: {concepts}"
        return summary

    def generate_digest(self, title: str, content: str, article_type: str) -> Optional[DigestOutput]:
        try:
            user_prompt = f"Create a learning digest for this {article_type}:\nTitle: {title}\nContent: {content[:8000]}"

            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )

            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)
            return DigestOutput(**data)

        except Exception as e:
            print(f"Error generating digest: {e}")
            return None
