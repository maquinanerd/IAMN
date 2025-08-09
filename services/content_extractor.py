import requests
import trafilatura
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from config import USER_AGENT

logger = logging.getLogger(__name__)

class ContentExtractor:
    """
    Extracts, cleans, and normalizes content from a given URL.
    Implements fallback logic for metadata and sanitizes HTML content.
    """

    def extract(self, url: str) -> dict:
        """
        Main method to perform content extraction from a URL.
        """
        try:
            response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=15)
            response.raise_for_status()
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract main content using trafilatura as a base
            main_content_html = trafilatura.extract(
                html_content,
                include_comments=False,
                include_tables=True,
                no_fallback=True
            )

            if not main_content_html:
                logger.warning(f"Trafilatura failed to extract main content from {url}. Falling back to body.")
                body_tag = soup.find('body')
                main_content_html = str(body_tag) if body_tag else ''

            # Sanitize and process the extracted content
            sanitized_content = self._sanitize_and_process_content(main_content_html, url)

            return {
                "metadata": self._extract_metadata(soup, url),
                "content_html": sanitized_content
            }

        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during extraction from {url}: {e}", exc_info=True)
            return None

    def _extract_metadata(self, soup: BeautifulSoup, base_url: str) -> dict:
        """Extracts metadata using fallback logic: OG -> Twitter -> Standard tags."""
        meta = {
            'canonical_url': self._find_tag(soup, 'link', {'rel': 'canonical'}, 'href') or base_url,
            'title': self._find_tag(soup, 'meta', {'property': 'og:title'}, 'content') or self._find_tag(soup, 'title'),
            'summary': self._find_tag(soup, 'meta', {'property': 'og:description'}, 'content') or self._find_tag(soup, 'meta', {'name': 'description'}, 'content'),
            'featured_image': self._find_tag(soup, 'meta', {'property': 'og:image'}, 'content') or self._find_tag(soup, 'meta', {'name': 'twitter:image'}, 'content'),
            'published_time': self._find_tag(soup, 'meta', {'property': 'article:published_time'}, 'content'),
            'author': self._find_tag(soup, 'meta', {'name': 'author'}, 'content')
        }
        # Resolve relative URLs for images and canonical
        if meta['featured_image']:
            meta['featured_image'] = urljoin(base_url, meta['featured_image'])
        if meta['canonical_url']:
            meta['canonical_url'] = urljoin(base_url, meta['canonical_url'])
        return meta

    def _find_tag(self, soup: BeautifulSoup, tag_name, attrs=None, value_attr=None):
        """Helper to find a tag and return its content or attribute."""
        tag = soup.find(tag_name, attrs)
        if not tag:
            return None
        return tag.get(value_attr) if value_attr else tag.get_text(strip=True)

    def _sanitize_and_process_content(self, html_content: str, base_url: str) -> str:
        """
        Sanitizes HTML, normalizes embeds, and resolves relative image URLs.
        A full implementation would use a library like `bleach`.
        This is a simplified version for demonstration.
        """
        if not html_content:
            return ""
            
        soup = BeautifulSoup(html_content, 'html.parser')

        # Normalize YouTube iframes
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if 'youtube.com' in src or 'youtu.be' in src:
                # Simplified normalization logic
                video_id = urlparse(src).path.split('/')[-1]
                iframe['src'] = f"https://www.youtube.com/embed/{video_id}"
                # Remove other attributes for cleanliness
                iframe.attrs = {'src': iframe['src'], 'frameborder': '0', 'allowfullscreen': ''}

        # Resolve relative image URLs
        for img in soup.find_all('img'):
            if img.get('src'):
                img['src'] = urljoin(base_url, img['src'])

        return str(soup)