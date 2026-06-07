import logging
import sys
from pathlib import Path
from typing import List
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agent.curator_agent import CuratorAgent, RankedArticle
from app.profiles.user_profile import USER_PROFILE
from app.database.repository import Repository
from app.services.process_email import apply_source_quota

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def curate_digests() -> dict:
    """Curate unsent digests with source quota filtering (matches production email behavior)."""
    curator = CuratorAgent(USER_PROFILE)
    repo = Repository()
    
    digests = repo.get_unsent_digests()
    total = len(digests)
    
    if total == 0:
        logger.warning("No unsent digests found")
        return {"total": 0, "ranked": 0}
    
    logger.info(f"Curating {total} unsent digests")
    logger.info(f"User profile: {USER_PROFILE['name']} - {USER_PROFILE['background']}")
    
    ranked_articles = curator.rank_digests(digests)
    
    if not ranked_articles:
        logger.error("Failed to rank digests")
        return {"total": total, "ranked": 0}
    
    # Apply same quota filtering as production email
    youtube_count = sum(1 for d in digests if d["article_type"] == "youtube")
    min_youtube = min(2, max(1, youtube_count - 1))
    
    ranked_articles = apply_source_quota(
        ranked_articles,
        digest_lookup=digests,
        top_n=10,
        min_youtube=min_youtube,
        max_corporate=2,
    )
    
    logger.info(f"Successfully ranked {len(ranked_articles)} articles (after quota)")
    logger.info("\n=== Top 10 Ranked Articles ===")
    
    for article in ranked_articles[:10]:
        digest = next((d for d in digests if d["id"] == article.digest_id), None)
        if digest:
            logger.info(f"\nRank {article.rank} | Score: {article.relevance_score:.1f}/10.0")
            logger.info(f"Title: {digest['title']}")
            logger.info(f"Type: {digest['article_type']}")
            logger.info(f"Reasoning: {article.reasoning}")
    
    return {
        "total": total,
        "ranked": len(ranked_articles),
        "articles": [
            {
                "digest_id": a.digest_id,
                "rank": a.rank,
                "relevance_score": a.relevance_score,
                "reasoning": a.reasoning
            }
            for a in ranked_articles
        ]
    }


if __name__ == "__main__":
    result = curate_digests()
    print(f"\n=== Curation Results ===")
    print(f"Total unsent digests: {result['total']}")
    print(f"Ranked (after quota): {result['ranked']}")


