import logging
import feedparser
from datetime import datetime, timedelta
from sqlalchemy import or_

from extensions import db
from models import Article
from dto import ExtractedArticleDTO
from config import USER_AGENT, SCHEDULE_CONFIG

logger = logging.getLogger(__name__)

class RSSMonitor:
    """
    Monitors RSS feeds for new articles, checks for duplicates in the database,
    and handles feed parsing errors gracefully.
    """

    def fetch_new_articles(self, feed_key: str, urls: list, limit: int) -> list[ExtractedArticleDTO]:
        """
        Fetches new articles from a list of URLs for a given feed, avoiding duplicates.

        Args:
            feed_key: The identifier for the feed source (e.g., 'screenrant_filmes_tv').
            urls: A list of RSS feed URLs to check.
            limit: The maximum number of new articles to fetch for this feed key.

        Returns:
            A list of ExtractedArticleDTO objects for new articles.
        """
        logger.info(f"[{feed_key}] Verificando novos artigos em {len(urls)} URL(s).")
        existing_urls = {article.source_url for article in Article.query.with_entities(Article.source_url).all()}
        new_articles = []

        for url in urls:
            if len(new_articles) >= limit:
                logger.info(f"[{feed_key}] Limite de {limit} artigos atingido. Parando a busca.")
                break

            try:
                feed = feedparser.parse(url, agent=USER_AGENT)

                # Improved error handling for malformed feeds
                if feed.bozo:
                    # This specifically checks for XML format errors like "mismatched tag"
                    if isinstance(feed.bozo_exception, (feedparser.expat.ExpatError, feedparser.sax.SAXParseException)):
                        logger.warning(
                            f"[{feed_key}] Ignorando feed malformado em {url}. "
                            f"O provedor do feed parece ter um erro de XML. Detalhe: {feed.bozo_exception}"
                        )
                    else: # Log other types of "bozo" errors
                        logger.warning(f"[{feed_key}] Problema de parsing no feed {url}. Detalhe: {feed.bozo_exception}")
                    continue # Skip this faulty URL and move to the next one

                for entry in feed.entries:
                    if len(new_articles) >= limit:
                        break
                    
                    if hasattr(entry, 'link') and entry.link not in existing_urls:
                        logger.info(f"[{feed_key}] Novo artigo encontrado: {entry.title}")
                        dto = ExtractedArticleDTO(source_url=entry.link, title=entry.title)
                        new_articles.append(dto)
                        existing_urls.add(entry.link) # Avoid processing duplicates in the same run

            except Exception as e:
                logger.error(f"[{feed_key}] Falha inesperada ao processar o feed {url}. Erro: {e}", exc_info=True)
                continue

        return new_articles

    def cleanup_old_articles(self):
        """Removes old articles from the database to keep it clean."""
        cleanup_hours = SCHEDULE_CONFIG.get('cleanup_after_hours', 24)
        cutoff_date = datetime.utcnow() - timedelta(hours=cleanup_hours)
        
        articles_to_delete = Article.query.filter(Article.created_at < cutoff_date).delete()
        db.session.commit()
        logger.info(f"Cleanup complete. Removed {articles_to_delete} articles older than {cleanup_hours} hours.")