"""
PaperPilot — Stealth Scraper Service
========================================
Fallback content extractor using Scrapling.
When Tavily's extract() fails on protected sites (Cloudflare, etc.),
this module uses stealth browsers to bypass anti-bot measures.

Usage:
    from scraper_service import StealthScraper
    scraper = StealthScraper()
    result = scraper.extract("https://researchgate.net/...")
"""

import re
import time
import logging
import requests
from typing import Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger('paperpilot.scraper')

# User-Agent for standard requests
STANDARD_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

# Known sites that typically block bots
STEALTH_PRIORITY_DOMAINS = [
    "researchgate.net",
    "sciencedirect.com",
    "ieee.org",
    "springer.com",
    "nature.com",
    "wiley.com",
    "tandfonline.com",
    "sagepub.com",
]


class StealthScraper:
    """
    Fallback content extractor with stealth capabilities.
    Tries standard HTTP first, then falls back to Scrapling stealth browser.
    """

    def __init__(self):
        self._scrapling_available = None
        self._check_scrapling()

    def _check_scrapling(self):
        """Check if Scrapling is installed and available."""
        try:
            import scrapling
            self._scrapling_available = True
            logger.info("Scrapling stealth engine available.")
        except ImportError:
            self._scrapling_available = False
            logger.warning("Scrapling not installed. Stealth extraction disabled. Install: pip install scrapling")

    # ──────────────────────────────────────────
    # Standard extraction (fast, no stealth)
    # ──────────────────────────────────────────

    def _standard_extract(self, url: str, timeout: int = 15) -> Optional[str]:
        """
        Try to extract content via standard HTTP request.
        Returns clean text or None if blocked/failed.
        """
        try:
            headers = {
                "User-Agent": STANDARD_UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            response = requests.get(url, headers=headers, timeout=(5, 10), allow_redirects=True)

            # Check for blocks
            if response.status_code in [403, 429, 503]:
                logger.info(f"Standard extraction blocked ({response.status_code}): {url}")
                return None

            if response.status_code != 200:
                logger.warning(f"Standard extraction HTTP {response.status_code}: {url}")
                return None

            # Check for CAPTCHA / bot-detection indicators in HTML
            content = response.text
            bot_indicators = [
                "cf-browser-verification",
                "challenge-platform",
                "captcha",
                "recaptcha",
                "hCaptcha",
                "cf-turnstile",
                "Access Denied",
                "bot detection",
            ]

            content_lower = content.lower()
            for indicator in bot_indicators:
                if indicator.lower() in content_lower:
                    logger.info(f"Bot detection found in response: {url}")
                    return None

            # Extract text from HTML
            text = self._html_to_text(content)

            # Verify we got meaningful content (not just navigation/boilerplate)
            if len(text) < 200:
                logger.info(f"Standard extraction too short ({len(text)} chars): {url}")
                return None

            return text

        except requests.exceptions.Timeout:
            logger.warning(f"Standard extraction timed out: {url}")
            return None
        except Exception as e:
            logger.warning(f"Standard extraction failed for {url}: {e}")
            return None

    # ──────────────────────────────────────────
    # Stealth extraction (Scrapling browser)
    # ──────────────────────────────────────────

    def _stealth_extract(self, url: str) -> Optional[str]:
        """
        Use Scrapling's stealth browser to bypass anti-bot measures.
        Returns clean text or None if failed.
        """
        if not self._scrapling_available:
            logger.warning("Scrapling not available for stealth extraction")
            return None

        try:
            from scrapling import StealthyFetcher

            logger.info(f"Launching stealth browser for: {url}")
            start = time.time()

            fetcher = StealthyFetcher()
            page = fetcher.fetch(url)

            if page and page.status == 200:
                # Get text content
                text = page.get_all_text() if hasattr(page, 'get_all_text') else ""

                if not text and hasattr(page, 'html'):
                    text = self._html_to_text(page.html)

                elapsed = round(time.time() - start, 1)

                if text and len(text) > 200:
                    logger.info(f"Stealth extraction success ({len(text)} chars, {elapsed}s): {url}")
                    return text
                else:
                    logger.warning(f"Stealth extraction too short ({len(text) if text else 0} chars): {url}")
                    return None
            else:
                status = page.status if page else "no response"
                logger.warning(f"Stealth extraction failed (status={status}): {url}")
                return None

        except Exception as e:
            logger.error(f"Stealth extraction error for {url}: {e}")
            return None

    # ──────────────────────────────────────────
    # HTML → clean text
    # ──────────────────────────────────────────

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to clean readable text using BeautifulSoup."""
        if not html:
            return ""

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, 'html.parser')

            # Remove non-content elements
            for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer',
                                       'aside', 'form', 'noscript', 'iframe']):
                tag.decompose()

            # Get text with newline separators between block elements
            text = soup.get_text(separator='\n', strip=True)

            # Clean up excessive whitespace
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = text.strip()

            return text

        except ImportError:
            # Fallback to regex if bs4 somehow unavailable
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'[ \t]+', ' ', text)
            text = text.strip()
            return text

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def _should_try_stealth_first(self, url: str) -> bool:
        """Check if this URL is from a known bot-blocking domain."""
        try:
            domain = urlparse(url).netloc.lower()
            return any(d in domain for d in STEALTH_PRIORITY_DOMAINS)
        except Exception:
            return False

    def extract(self, url: str) -> Dict:
        """
        Extract clean text from a URL.
        Step 1: Try standard HTTP (fast, cheap).
        Step 2: If blocked/failed → try Scrapling stealth browser.

        Returns:
            {text, method_used, word_count, success, url}
        """
        result = {
            "url": url,
            "text": "",
            "method_used": "failed",
            "word_count": 0,
            "success": False,
        }

        # For known-difficult domains, skip straight to stealth
        if self._should_try_stealth_first(url):
            logger.info(f"Known stealth-priority domain, trying stealth first: {url}")
            text = self._stealth_extract(url)
            if text:
                result["text"] = text
                result["method_used"] = "stealth"
                result["word_count"] = len(text.split())
                result["success"] = True
                return result

        # Step 1: Standard extraction
        text = self._standard_extract(url)
        if text:
            result["text"] = text
            result["method_used"] = "standard"
            result["word_count"] = len(text.split())
            result["success"] = True
            return result

        # Step 2: Stealth fallback
        if self._scrapling_available:
            text = self._stealth_extract(url)
            if text:
                result["text"] = text
                result["method_used"] = "stealth"
                result["word_count"] = len(text.split())
                result["success"] = True
                return result

        logger.warning(f"All extraction methods failed for: {url}")
        return result

    def batch_extract(self, urls: List[str]) -> List[Dict]:
        """
        Extract content from multiple URLs.
        Returns list of extraction results with per-URL status.
        """
        results = []
        for url in urls:
            result = self.extract(url)
            results.append(result)
        return results
