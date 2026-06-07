import logging
from typing import List
from dotenv import load_dotenv

load_dotenv()

from app.agent.email_agent import EmailAgent, RankedArticleDetail, EmailDigestResponse
from app.agent.curator_agent import CuratorAgent, RankedArticle
from app.profiles.user_profile import USER_PROFILE
from app.database.repository import Repository
from app.services.email import send_email, digest_to_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def apply_source_quota(
    ranked: List[RankedArticle],
    digest_lookup: list | dict,
    top_n: int = 10,
    min_youtube: int = 6,
    max_corporate: int = 2,
) -> List[RankedArticle]:
    """Enforce YouTube-heavy mix: min YouTube items, cap openai+anthropic combined."""
    if not ranked:
        return []

    if isinstance(digest_lookup, list):
        digest_by_id = {d["id"]: d for d in digest_lookup}
    else:
        digest_by_id = digest_lookup

    def article_type(digest_id: str) -> str:
        d = digest_by_id.get(digest_id)
        return d["article_type"] if d else digest_id.split(":")[0]

    selected: List[RankedArticle] = []
    selected_ids: set[str] = set()

    def add_item(item: RankedArticle) -> bool:
        if item.digest_id in selected_ids or len(selected) >= top_n:
            return False
        selected.append(item)
        selected_ids.add(item.digest_id)
        return True

    corporate_count = 0

    for item in ranked:
        if len(selected) >= top_n:
            break
        atype = article_type(item.digest_id)
        if atype in ("openai", "anthropic"):
            if corporate_count >= max_corporate:
                continue
            corporate_count += 1
        add_item(item)

    youtube_selected = sum(1 for s in selected if article_type(s.digest_id) == "youtube")
    if youtube_selected < min_youtube:
        for item in ranked:
            if len(selected) >= top_n:
                break
            if item.digest_id in selected_ids:
                continue
            if article_type(item.digest_id) != "youtube":
                continue
            if add_item(item):
                youtube_selected += 1
                if youtube_selected >= min_youtube:
                    break

    if len(selected) < top_n:
        for item in ranked:
            if len(selected) >= top_n:
                break
            if item.digest_id in selected_ids:
                continue
            atype = article_type(item.digest_id)
            if atype in ("openai", "anthropic") and corporate_count >= max_corporate:
                continue
            if atype in ("openai", "anthropic"):
                corporate_count += 1
            add_item(item)

    return [item.model_copy(update={"rank": i}) for i, item in enumerate(selected, start=1)]


def generate_email_digest(top_n: int = 10) -> EmailDigestResponse:
    curator = CuratorAgent(USER_PROFILE)
    email_agent = EmailAgent(USER_PROFILE)
    repo = Repository()

    digests = repo.get_unsent_digests()
    total = len(digests)

    if total == 0:
        logger.warning("No new digests to email (all previously sent or none created)")
        raise ValueError("No new content to email today")

    logger.info(f"Ranking {total} unsent digests for email generation")
    ranked_articles = curator.rank_digests(digests)

    if not ranked_articles:
        logger.error("Failed to rank digests")
        raise ValueError("Failed to rank articles")

    # Count available YouTube in digests to set realistic quota
    youtube_count = sum(1 for d in digests if d["article_type"] == "youtube")
    min_youtube = min(2, max(1, youtube_count - 1))  # At least 1 YouTube, but don't over-require
    
    ranked_articles = apply_source_quota(
        ranked_articles,
        digest_lookup=digests,
        top_n=top_n,
        min_youtube=min_youtube,
        max_corporate=2,
    )

    if not ranked_articles:
        raise ValueError("No articles passed source quota filtering")

    logger.info(f"Generating email digest with top {min(top_n, len(ranked_articles))} articles")

    digest_map = {d["id"]: d for d in digests}
    article_details = []
    for a in ranked_articles[:top_n]:
        d = digest_map.get(a.digest_id)
        if not d or not d.get("title") or not d.get("url"):
            continue
        article_details.append(
            RankedArticleDetail(
                digest_id=a.digest_id,
                rank=a.rank,
                relevance_score=a.relevance_score,
                reasoning=a.reasoning,
                title=d["title"],
                summary=d["summary"],
                url=d["url"],
                article_type=d["article_type"],
            )
        )

    if not article_details:
        raise ValueError("No valid articles to include in email")

    email_digest = email_agent.create_email_digest_response(
        ranked_articles=article_details,
        total_ranked=total,
        limit=top_n,
    )

    logger.info("Email digest generated successfully")
    logger.info("\n=== Email Introduction ===")
    logger.info(email_digest.introduction.greeting)
    logger.info(f"\n{email_digest.introduction.introduction}")

    return email_digest


def send_digest_email(hours: int = 24, top_n: int = 10) -> dict:
    try:
        result = generate_email_digest(top_n=top_n)
        markdown_content = result.to_markdown()
        html_content = digest_to_html(result)

        subject = "Daily AI Learning Digest"
        greeting = result.introduction.greeting
        if "for " in greeting:
            subject = f"Daily AI Learning Digest — {greeting.split('for ')[-1].rstrip('.')}"

        send_email(
            subject=subject,
            body_text=markdown_content,
            body_html=html_content,
        )

        repo = Repository()
        sent_ids = [a.digest_id for a in result.articles]
        marked = repo.mark_digests_emailed(sent_ids)
        logger.info(f"Marked {marked} digests as emailed")

        logger.info("Email sent successfully!")
        return {
            "success": True,
            "subject": subject,
            "articles_count": len(result.articles),
            "digest_ids_sent": sent_ids,
        }
    except ValueError as e:
        logger.error(f"Error sending email: {e}")
        return {
            "success": False,
            "error": str(e),
        }


if __name__ == "__main__":
    result = send_digest_email(top_n=10)
    if result["success"]:
        print("\n=== Email Digest Sent ===")
        print(f"Subject: {result['subject']}")
        print(f"Articles: {result['articles_count']}")
    else:
        print(f"Error: {result['error']}")
