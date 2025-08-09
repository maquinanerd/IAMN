from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class FeaturedImageDTO(BaseModel):
    """
    Data Transfer Object for a featured image.
    """
    url: HttpUrl
    alt: str

class PublishedArticleDTO(BaseModel):
    """
    Data Transfer Object representing a fully processed article,
    ready for publishing. This structure standardizes the output
    of the content pipeline.
    """
    source_url: HttpUrl
    canonical_url: HttpUrl
    title: str  # Rewritten and SEO-optimized
    summary: str  # Optimized meta description
    slug: str
    featured_image: FeaturedImageDTO
    content_html: str  # Rewritten, sanitized, with embeds
    tags: List[str]
    category: Optional[str]
    schema_json_ld: dict  # Complete and validated Schema.org object
    attribution: str  # e.g., "Via {domain/origin}"