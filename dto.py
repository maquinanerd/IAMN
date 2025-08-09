from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FeaturedImageDTO:
    """DTO for a featured image."""
    url: str
    alt: str


@dataclass
class ExtractedArticleDTO:
    """DTO for a raw article fetched from an RSS feed, ready for processing."""
    source_url: str
    feed_key: str


@dataclass
class PublishedArticleDTO:
    """DTO for a fully processed article ready for publishing."""
    source_url: str
    title: str
    slug: str
    content_html: str
    summary: str
    category: str
    tags: List[str]
    featured_image: FeaturedImageDTO
    schema_json_ld: str
    attribution: str
    canonical_url: Optional[str] = None