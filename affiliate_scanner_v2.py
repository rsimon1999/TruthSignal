"""
Affiliate Link Scanner for TruthSignal
Detects affiliate marketing links from major networks in HTML content
With fallback support for external libraries
"""

import re
import logging
from typing import Dict, List, Set, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import BeautifulSoup, but provide fallback
try:
    from bs4 import BeautifulSoup

    BEAUTIFUL_SOUP_AVAILABLE = True
    logger.info("BeautifulSoup available - using enhanced HTML parsing")
except ImportError:
    BEAUTIFUL_SOUP_AVAILABLE = False
    logger.warning("BeautifulSoup not available - using regex fallback for HTML parsing")

try:
    import urllib3

    URLLIB3_AVAILABLE = True
except ImportError:
    URLLIB3_AVAILABLE = False


class AffiliateScanner:
    """
    Scans HTML content for affiliate marketing links from major networks
    """

    def __init__(self, use_advanced_parsing: bool = True):
        """
        Initialize the scanner

        Args:
            use_advanced_parsing: If True and BeautifulSoup is available, use it for parsing
        """
        self.use_advanced_parsing = use_advanced_parsing and BEAUTIFUL_SOUP_AVAILABLE

        # Compile regex patterns for better performance
        self.patterns = {
            'amazon': self._compile_amazon_patterns(),
            'shareasale': self._compile_shareasale_patterns(),
            'cj_affiliate': self._compile_cj_affiliate_patterns(),
            'ebay': self._compile_ebay_patterns(),
            'clickbank': self._compile_clickbank_patterns()
        }

        # Network display names
        self.network_names = {
            'amazon': 'Amazon Associates',
            'shareasale': 'ShareASale',
            'cj_affiliate': 'CJ Affiliate',
            'ebay': 'eBay Partner Network',
            'clickbank': 'ClickBank'
        }

    def _compile_amazon_patterns(self) -> List[re.Pattern]:
        """Compile Amazon Associates detection patterns"""
        return [
            # tag parameter in query string
            re.compile(
                r'https?://(?:www\.)?amazon\.(?:com|co\.uk|ca|de|fr|it|es|co\.jp|cn|com\.au|com\.br|com\.mx)/[^"\']*[?&](?:tag|associate-tag)=[a-zA-Z0-9_-]+',
                re.IGNORECASE),
            # gp/product with affiliate structure
            re.compile(
                r'https?://(?:www\.)?amazon\.(?:com|co\.uk|ca|de|fr|it|es|co\.jp|cn|com\.au|com\.br|com\.mx)/gp/product/[^"\']*/ref=[^"\']*\?[^"\']*tag=[a-zA-Z0-9_-]+',
                re.IGNORECASE),
            # dp with affiliate structure
            re.compile(
                r'https?://(?:www\.)?amazon\.(?:com|co\.uk|ca|de|fr|it|es|co\.jp|cn|com\.au|com\.br|com\.mx)/[^"\']*/dp/[^"\']*/ref=[^"\']*\?[^"\']*tag=[a-zA-Z0-9_-]+',
                re.IGNORECASE),
            # amzn.to short links (common affiliate shorteners)
            re.compile(r'https?://amzn\.to/[a-zA-Z0-9]+', re.IGNORECASE),
            # Amazon smile (sometimes used in affiliate marketing)
            re.compile(
                r'https?://smile\.amazon\.(?:com|co\.uk|ca|de|fr|it|es|co\.jp|cn|com\.au|com\.br|com\.mx)/[^"\']*[?&]tag=[a-zA-Z0-9_-]+',
                re.IGNORECASE)
        ]

    def _compile_shareasale_patterns(self) -> List[re.Pattern]:
        """Compile ShareASale detection patterns"""
        return [
            # shareasale.com with r parameter
            re.compile(r'https?://(?:www\.)?shareasale\.com/[^"\']*[?&]r=[0-9]+', re.IGNORECASE),
            # shareasale.com with merchant ID patterns
            re.compile(r'https?://(?:www\.)?shareasale\.com/r\.cfm\?[^"\']*(?:merchantID|m)=[0-9]+', re.IGNORECASE),
            # shareasale.com affiliate links
            re.compile(r'https?://(?:www\.)?shareasale\.com/[^"\']*\?(?:[^"\']*&)*[a-zA-Z]+=[0-9]+', re.IGNORECASE),
            # shareasale.com with affiliate parameter
            re.compile(r'https?://(?:www\.)?shareasale\.com/[^"\']*[?&]affiliate=[0-9]+', re.IGNORECASE)
        ]

    def _compile_cj_affiliate_patterns(self) -> List[re.Pattern]:
        """Compile CJ Affiliate detection patterns"""
        cj_domains = [
            'anrdoezrs.net',
            'dpbolvw.net',
            'tkqlhce.com',
            'jdoqocy.com',
            'kqzyfj.com',
            'qksrv.net',
            'awltovhc.com',
            'vwcjb.net'
        ]

        patterns = []
        for domain in cj_domains:
            # Match any URL from known CJ Affiliate domains
            patterns.append(
                re.compile(rf'https?://(?:www\.)?{re.escape(domain)}/[\w/\.-]+', re.IGNORECASE)
            )

        return patterns

    def _compile_ebay_patterns(self) -> List[re.Pattern]:
        """Compile eBay Partner Network patterns"""
        return [
            re.compile(r'https?://(?:www\.)?ebay\.com/[^"\']*[?&]_trksid=[a-zA-Z0-9_-]+', re.IGNORECASE),
            re.compile(r'https?://(?:www\.)?ebay\.com/[^"\']*[?&]mkcid=[0-9]+', re.IGNORECASE),
            re.compile(r'https?://(?:www\.)?ebay\.com/[^"\']*[?&]campid=[0-9]+', re.IGNORECASE)
        ]

    def _compile_clickbank_patterns(self) -> List[re.Pattern]:
        """Compile ClickBank patterns"""
        return [
            re.compile(r'https?://(?:[a-zA-Z0-9-]+\.)?clickbank\.net/[^"\']*', re.IGNORECASE),
            re.compile(r'https?://(?:hop|redirect)\.clickbank\.net/\?[^"\']*', re.IGNORECASE),
            re.compile(r'https?://[^"\']*\.hop\.clickbank\.net[^"\']*', re.IGNORECASE)
        ]

    def _extract_links_with_beautifulsoup(self, html_content: str) -> List[str]:
        """Extract links using BeautifulSoup (more reliable)"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []

            # Extract from href attributes
            for tag in soup.find_all(['a', 'link']):
                href = tag.get('href')
                if href:
                    links.append(href)

            # Extract from src attributes
            for tag in soup.find_all(['img', 'script', 'iframe', 'frame']):
                src = tag.get('src')
                if src:
                    links.append(src)

            # Extract from form actions
            for tag in soup.find_all('form'):
                action = tag.get('action')
                if action:
                    links.append(action)

            # Extract from meta refresh
            for tag in soup.find_all('meta', attrs={'http-equiv': re.compile('refresh', re.I)}):
                content = tag.get('content', '')
                url_match = re.search(r'url=(.+)', content, re.I)
                if url_match:
                    links.append(url_match.group(1))

            return list(set(links))

        except Exception as e:
            logger.error(f"Error extracting links with BeautifulSoup: {e}")
            # Fall back to regex method
            return self._extract_links_with_regex(html_content)

    def _extract_links_with_regex(self, html_content: str) -> List[str]:
        """Extract links using regex (fallback method)"""
        try:
            links = []

            # Pattern for href attributes
            href_pattern = r'href\s*=\s*["\']([^"\']+)["\']'
            href_matches = re.finditer(href_pattern, html_content, re.IGNORECASE)
            links.extend(match.group(1) for match in href_matches)

            # Pattern for src attributes
            src_pattern = r'src\s*=\s*["\']([^"\']+)["\']'
            src_matches = re.finditer(src_pattern, html_content, re.IGNORECASE)
            links.extend(match.group(1) for match in src_matches)

            # Pattern for action attributes
            action_pattern = r'action\s*=\s*["\']([^"\']+)["\']'
            action_matches = re.finditer(action_pattern, html_content, re.IGNORECASE)
            links.extend(match.group(1) for match in action_matches)

            # Remove duplicates and return
            return list(set(links))

        except Exception as e:
            logger.error(f"Error extracting links with regex: {e}")
            return []

    def _extract_links_from_html(self, html_content: str) -> List[str]:
        """
        Extract all URLs from HTML content using the best available method
        """
        if self.use_advanced_parsing:
            return self._extract_links_with_beautifulsoup(html_content)
        else:
            return self._extract_links_with_regex(html_content)

    def _normalize_url(self, url: str) -> str:
        """
        Basic URL normalization
        """
        try:
            # Remove leading/trailing whitespace
            url = url.strip()

            # Handle common URL encodings and entities
            url = url.replace('&amp;', '&')
            url = url.replace('&#38;', '&')
            url = url.replace('&#x26;', '&')

            return url
        except Exception:
            return url

    def _is_affiliate_link(self, url: str) -> Dict[str, str]:
        """
        Check if a URL matches any affiliate network patterns
        Returns dict with network name if found, empty dict otherwise
        """
        try:
            # Normalize URL for better matching
            normalized_url = self._normalize_url(url)

            for network, patterns in self.patterns.items():
                for pattern in patterns:
                    if pattern.search(normalized_url):
                        return {
                            'network': network,
                            'display_name': self.network_names[network],
                            'url': normalized_url
                        }

            return {}

        except Exception as e:
            logger.error(f"Error checking affiliate link {url}: {e}")
            return {}

    def find_affiliate_links(self, html_content: str) -> Dict:
        """
        Main function to find affiliate links in HTML content

        Args:
            html_content (str): HTML content as string

        Returns:
            dict: Analysis results with affiliate link information
        """
        try:
            if not html_content or not isinstance(html_content, str):
                logger.warning("Invalid HTML content provided")
                return self._empty_result()

            if len(html_content.strip()) == 0:
                return self._empty_result()

            # Extract all links from HTML
            all_links = self._extract_links_from_html(html_content)
            logger.info(f"Extracted {len(all_links)} total links from HTML")

            if not all_links:
                return self._empty_result()

            # Check each link for affiliate patterns
            affiliate_links = []
            detected_networks = set()

            for link in all_links:
                result = self._is_affiliate_link(link)
                if result:
                    affiliate_links.append(result)
                    detected_networks.add(result['network'])

            # Prepare results
            unique_links = self._get_unique_links(affiliate_links)
            sample_links = self._get_sample_urls(unique_links)

            return {
                'affiliate_links_found': len(affiliate_links) > 0,
                'affiliate_networks': [self.network_names[net] for net in detected_networks],
                'total_affiliate_links': len(affiliate_links),
                'unique_affiliate_links': len(unique_links),
                'details': sample_links,
                'all_affiliate_links': affiliate_links,  # Full list for debugging
                'parsing_method': 'beautifulsoup' if self.use_advanced_parsing else 'regex'
            }

        except Exception as e:
            logger.error(f"Error in find_affiliate_links: {e}")
            return self._error_result(str(e))

    def _get_unique_links(self, affiliate_links: List[Dict]) -> Set[str]:
        """Get unique affiliate URLs"""
        return set(link['url'] for link in affiliate_links)

    def _get_sample_urls(self, unique_links: Set[str], max_samples: int = 5) -> List[str]:
        """Get sample URLs for the result details"""
        sample_list = list(unique_links)[:max_samples]

        # Truncate long URLs for readability
        truncated_samples = []
        for url in sample_list:
            if len(url) > 100:
                truncated_samples.append(url[:100] + '...')
            else:
                truncated_samples.append(url)

        return truncated_samples

    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'affiliate_links_found': False,
            'affiliate_networks': [],
            'total_affiliate_links': 0,
            'unique_affiliate_links': 0,
            'details': [],
            'all_affiliate_links': [],
            'parsing_method': 'none'
        }

    def _error_result(self, error_message: str) -> Dict:
        """Return error result structure"""
        result = self._empty_result()
        result['error'] = error_message
        return result


# Module-level function for easy import and use
def find_affiliate_links(html_content: str, use_advanced_parsing: bool = True) -> dict:
    """
    Find affiliate marketing links in HTML content

    Args:
        html_content (str): HTML content as string
        use_advanced_parsing (bool): Whether to use BeautifulSoup if available

    Returns:
        dict: Analysis results with keys:
            - affiliate_links_found (bool): True if any affiliate links detected
            - affiliate_networks (list): Names of detected networks
            - total_affiliate_links (int): Count of affiliate links found
            - details (list): Sample of found affiliate URLs (max 5)
    """
    try:
        scanner = AffiliateScanner(use_advanced_parsing=use_advanced_parsing)
        result = scanner.find_affiliate_links(html_content)

        # Return only the specified fields in the public API
        return {
            'affiliate_links_found': result['affiliate_links_found'],
            'affiliate_networks': result['affiliate_networks'],
            'total_affiliate_links': result['total_affiliate_links'],
            'details': result['details'],
            'parsing_method': result.get('parsing_method', 'unknown')
        }
    except Exception as e:
        logger.error(f"Error in find_affiliate_links module function: {e}")
        return {
            'affiliate_links_found': False,
            'affiliate_networks': [],
            'total_affiliate_links': 0,
            'details': [],
            'error': str(e)
        }


# Utility function to check dependencies
def check_dependencies() -> Dict[str, bool]:
    """
    Check availability of optional dependencies

    Returns:
        dict: Status of optional dependencies
    """
    return {
        'beautifulsoup4': BEAUTIFUL_SOUP_AVAILABLE,
        'urllib3': URLLIB3_AVAILABLE
    }


# Example usage and testing
if __name__ == "__main__":
    print("Testing Affiliate Scanner with Dependency Check...")
    print("=" * 50)

    deps = check_dependencies()
    print("Dependency Status:")
    for dep, available in deps.items():
        print(f"  {dep}: {'✓ Available' if available else '✗ Not Available'}")

    # Test HTML content with various affiliate links
    test_html = """
    <html>
    <body>
        <a href="https://www.amazon.com/dp/B08N5WRWNW?tag=affiliate123-20&psc=1">Amazon Product</a>
        <a href="https://shareasale.com/r.cfm?m=12345&u=567">ShareASale Link</a>
        <a href="https://www.anrdoezrs.net/click-12345">CJ Affiliate</a>
        <a href="https://amzn.to/3xyz123">Amazon Short Link</a>
        <a href="https://example.com/regular-link">Regular Link</a>
        <img src="https://dpbolvw.net/imp-12345/image.jpg">
        <form action="https://shareasale.com/process-order?affiliate=789">
        <a href="https://ebay.com/itm/12345?_trksid=p2349624.m12345.l12345">eBay Item</a>
    </body>
    </html>
    """

    print("\n" + "=" * 50)
    print("Scanner Test Results:")

    # Test the function
    result = find_affiliate_links(test_html)

    print(f"Affiliate Links Found: {result['affiliate_links_found']}")
    print(f"Networks Detected: {result['affiliate_networks']}")
    print(f"Total Affiliate Links: {result['total_affiliate_links']}")
    print(f"Parsing Method: {result.get('parsing_method', 'unknown')}")
    print(f"Sample URLs: {result['details']}")