from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ExtractedArticleDTO:
    """
    Data Transfer Object para um artigo recém-encontrado no feed RSS.
    Nesta fase inicial, carrega apenas a URL de origem.
    """
    source_url: str

@dataclass
class FeaturedImageDTO:
    """DTO para a imagem de destaque de um artigo."""
    url: Optional[str]
    alt: str

@dataclass
class PublishedArticleDTO:
    """DTO contendo todos os dados finais prontos para publicação no WordPress."""
    source_url: str
    canonical_url: Optional[str]
    title: str
    summary: str
    slug: str
    featured_image: FeaturedImageDTO
    content_html: str
    tags: List[str]
    category: str
    schema_json_ld: str
    attribution: str