import feedparser
import logging
from extensions import db
from models import Article
from config import RSS_FEEDS, USER_AGENT

logger = logging.getLogger(__name__)

class RSSMonitor:
    """
    Monitors RSS feeds to find new article URLs that are not yet in the database.
    """

    def fetch_new_articles(self, limit=None):
        """
        Fetches new articles from all configured RSS feeds.

        Args:
            limit (int, optional): The maximum number of new articles to return.
                                   If None, returns all new articles found.

        Returns:
            list: A list of feedparser entry objects for new articles.
        """
        new_entries = []
        # Query all existing URLs from the database at once for efficiency
        urls_in_db = {row.original_url for row in db.session.query(Article.original_url).all()}
        logger.info(f"Found {len(urls_in_db)} URLs in the database to check against.")

        for feed_type, feed_url in RSS_FEEDS.items():
            try:
                logger.debug(f"Fetching feed: {feed_type} from {feed_url}")
                feed = feedparser.parse(feed_url, agent=USER_AGENT)

                if feed.bozo:
                    logger.warning(f"Feed {feed_type} might be malformed. Bozo reason: {getattr(feed, 'bozo_exception', 'Unknown')}")

                for entry in feed.entries:
                    if limit is not None and len(new_entries) >= limit:
                        logger.info(f"Reached fetch limit of {limit}. Stopping feed processing.")
                        return new_entries

                    if hasattr(entry, 'link') and entry.link not in urls_in_db:
                        entry.feed_type = feed_type  # Add feed_type to the entry for later use
                        new_entries.append(entry)
                        urls_in_db.add(entry.link)  # Avoid adding duplicates from other feeds in the same run
                        logger.info(f"Found new article: '{entry.title}' from {feed_type}")

            except Exception as e:
                logger.error(f"Error fetching or parsing feed {feed_type}: {e}", exc_info=True)

        return new_entries

    def cleanup_old_articles(self):
        """Placeholder for the cleanup function called by the scheduler."""
        logger.info("Cleanup function in RSSMonitor called. No specific action implemented.")
        pass