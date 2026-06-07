import os
import smtplib
import html
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import markdown

from app.agent.email_agent import EmailDigestResponse, RankedArticleDetail

load_dotenv()

MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# HTML Template Constants
CONCEPTS_PATTERN = re.compile(r"\n*Key concepts:\s*(.+)$", re.IGNORECASE | re.DOTALL)


def _split_summary_and_concepts(summary: str) -> tuple[str, list[str]]:
    """Extract summary text and key concepts list from formatted summary."""
    match = CONCEPTS_PATTERN.search(summary)
    if not match:
        return summary.strip(), []
    body = summary[: match.start()].strip()
    concepts = [c.strip() for c in match.group(1).split(",") if c.strip()]
    return body, concepts


def _source_badge(article_type: str) -> tuple[str, str]:
    """Return badge label and CSS class for article type."""
    badges = {
        "youtube": ("YouTube Tutorial", "badge-youtube"),
        "openai": ("OpenAI", "badge-openai"),
        "anthropic": ("Anthropic", "badge-anthropic"),
    }
    return badges.get(article_type, ("Article", "badge-default"))


def _render_article_card(article: RankedArticleDetail) -> str:
    """Render HTML card for a single ranked article."""
    if not article.title or not article.url:
        return ""

    summary_body, concepts = _split_summary_and_concepts(article.summary)
    badge_label, badge_class = _source_badge(article.article_type)
    summary_html = markdown.markdown(summary_body, extensions=["extra", "nl2br"])

    concepts_html = ""
    if concepts:
        chips = "".join(
            f'<span class="concept-chip">{html.escape(c)}</span>' for c in concepts
        )
        concepts_html = f'<div class="concepts">{chips}</div>'

    reasoning_html = ""
    if article.reasoning:
        reasoning_html = (
            f'<p class="reasoning"><strong>Why this is for you:</strong> '
            f'{html.escape(article.reasoning)}</p>'
        )

    return f"""
    <div class="article-card">
      <div class="card-header">
        <span class="rank">#{article.rank}</span>
        <span class="badge {badge_class}">{html.escape(badge_label)}</span>
        <span class="score">{article.relevance_score:.1f}/10</span>
      </div>
      <h2 class="article-title">{html.escape(article.title)}</h2>
      {reasoning_html}
      <div class="summary">{summary_html}</div>
      {concepts_html}
      <a href="{html.escape(article.url)}" class="read-btn">Read more</a>
    </div>
    """


def digest_to_html(digest_response: EmailDigestResponse) -> str:
    """Convert EmailDigestResponse to formatted HTML email."""
    greeting_html = markdown.markdown(
        digest_response.introduction.greeting, extensions=["extra", "nl2br"]
    )
    introduction_html = markdown.markdown(
        digest_response.introduction.introduction, extensions=["extra", "nl2br"]
    )

    cards = "".join(_render_article_card(a) for a in digest_response.articles)
    article_count = len(digest_response.articles)

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      line-height: 1.7;
      color: #2d3748;
      max-width: 640px;
      margin: 0 auto;
      padding: 24px 16px;
      background-color: #f7fafc;
    }}
    .container {{
      background: #ffffff;
      border-radius: 12px;
      padding: 28px 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    .greeting {{
      font-size: 20px;
      font-weight: 600;
      color: #1a202c;
      margin-bottom: 8px;
    }}
    .greeting p {{ margin: 0; }}
    .introduction {{
      font-size: 15px;
      color: #4a5568;
      margin-bottom: 24px;
    }}
    .introduction p {{ margin: 0; }}
    .section-title {{
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #718096;
      margin-bottom: 16px;
    }}
    .article-card {{
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 20px;
      margin-bottom: 16px;
      background: #fafbfc;
    }}
    .card-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }}
    .rank {{
      font-size: 13px;
      font-weight: 700;
      color: #4a5568;
    }}
    .badge {{
      font-size: 11px;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 12px;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .badge-youtube {{ background: #fed7d7; color: #c53030; }}
    .badge-openai {{ background: #c6f6d5; color: #276749; }}
    .badge-anthropic {{ background: #feebc8; color: #c05621; }}
    .badge-default {{ background: #e2e8f0; color: #4a5568; }}
    .score {{
      font-size: 12px;
      color: #718096;
      margin-left: auto;
    }}
    .article-title {{
      font-size: 18px;
      font-weight: 600;
      color: #1a202c;
      margin: 0 0 8px 0;
      line-height: 1.4;
    }}
    .reasoning {{
      font-size: 13px;
      color: #718096;
      font-style: italic;
      margin: 0 0 10px 0;
    }}
    .summary {{
      font-size: 15px;
      color: #4a5568;
      margin-bottom: 12px;
    }}
    .summary p {{ margin: 6px 0; }}
    .concepts {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 14px;
    }}
    .concept-chip {{
      font-size: 12px;
      background: #ebf8ff;
      color: #2b6cb0;
      padding: 4px 10px;
      border-radius: 6px;
      font-weight: 500;
    }}
    .read-btn {{
      display: inline-block;
      font-size: 14px;
      font-weight: 600;
      color: #ffffff;
      background: #3182ce;
      padding: 8px 18px;
      border-radius: 6px;
      text-decoration: none;
    }}
    .footer {{
      font-size: 12px;
      color: #a0aec0;
      text-align: center;
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid #e2e8f0;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="greeting">{greeting_html}</div>
    <div class="introduction">{introduction_html}</div>
    <div class="section-title">Today's {article_count} learning picks</div>
    {cards}
    <div class="footer">
      Your daily AI engineering learning digest — curated for your skill level.
    </div>
  </div>
</body>
</html>"""


def send_email(subject: str, body_text: str, body_html: str = None, recipients: list = None):
    if recipients is None:
        if not MY_EMAIL:
            raise ValueError("MY_EMAIL environment variable is not set")
        recipients = [MY_EMAIL]

    recipients = [r for r in recipients if r is not None]
    if not recipients:
        raise ValueError("No valid recipients provided")

    if not MY_EMAIL:
        raise ValueError("MY_EMAIL environment variable is not set")
    if not APP_PASSWORD:
        raise ValueError("APP_PASSWORD environment variable is not set")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = MY_EMAIL
    msg["To"] = ", ".join(recipients)

    part1 = MIMEText(body_text, "plain")
    msg.attach(part1)

    if body_html:
        part2 = MIMEText(body_html, "html")
        msg.attach(part2)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(MY_EMAIL, APP_PASSWORD)
        smtp.sendmail(MY_EMAIL, recipients, msg.as_string())


def send_email_to_self(subject: str, body: str):
    if not MY_EMAIL:
        raise ValueError("MY_EMAIL environment variable is not set. Please set it in your .env file.")
    send_email(subject, body, recipients=[MY_EMAIL])


if __name__ == "__main__":
    send_email_to_self("Test from Python", "Hello from my script.")
