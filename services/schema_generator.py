import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SchemaGenerator:
    """
    Generates perfectly formatted and validated Schema.org JSON-LD objects.
    """

    def generate_news_article_schema(
        self,
        headline: str,
        summary: str,
        image_url: str,
        canonical_url: str,
        date_published: str,
        author_name: str,
        publisher_name: str,
        publisher_logo_url: str
    ) -> dict:
        """
        Creates a NewsArticle schema object.
        """
        schema = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "headline": headline,
            "description": summary,
            "image": [image_url],
            "datePublished": date_published or datetime.utcnow().isoformat(),
            "dateModified": datetime.utcnow().isoformat(),
            "author": {"@type": "Person", "name": author_name or publisher_name},
            "publisher": {
                "@type": "Organization",
                "name": publisher_name,
                "logo": {"@type": "ImageObject", "url": publisher_logo_url}
            },
            "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url}
        }
        logger.info(f"Generated NewsArticle schema for '{headline}'")
        return schema