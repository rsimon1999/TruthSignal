"""
Affiliate Link Scanner for TruthSignal
Detects affiliate marketing links from major networks in HTML content
Uses only Python standard library - no external dependencies
"""

import re
import logging
from typing import Dict, List, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AffiliateScanner:
    """
    Scans HTML content for affiliate marketing links from major networks
    """

    def __init__(self):
        # Compile regex patterns for better performance
        self.patterns = {
            'amazon': self._compile_amazon_patterns(),
            'shareasale': self._compile_shareasale_patterns(),
            'cj_affiliate': self._compile_cj_affiliate_patterns()
        }

        # Network display names
        self.network_names = {
            'amazon': 'Amazon Associates',
            'shareasale': 'ShareASale',
            'cj_affiliate': 'CJ Affiliate'
        }

    def _compile_amazon_patterns(self) -> List[re.Pattern]:
        """Compile Amazon Associates detection patterns"""
        return [
            # tag parameter in query string
            re.compile(
                r'https?://(?:www\.)?amazon\.(?:com|co\.uk|ca|de|fr|it|es|co\.jp|cn)/[^"\']*[?&](?:tag|associate-tag)=[a-zA-Z0-9_-]+',
                re.IGNORECASE),
            # gp/product with affiliate structure
            re.compile(
                r'https?://(?:www\.)?amazon\.(?:com|co\.uk|ca|de|fr|it|es|co\.jp|cn)/gp/product/[^"\']*/ref=[^"\']*\?[^"\']*tag=[a-zA-Z0-9_-]+',
                re.IGNORECASE),
            # dp with affiliate structure
            re.compile(
                r'https?://(?:www\.)?amazon\.(?:com|co\.uk|ca|de|fr|it|es|co\.jp|cn)/[^"\']*/dp/[^"\']*/ref=[^"\']*\?[^"\']*tag=[a-zA-Z0-9_-]+',
                re.IGNORECASE),
            # amzn.to short links (common affiliate shorteners)
            re.compile(r'https?://amzn\.to/[a-zA-Z0-9]+', re.IGNORECASE),
            # Amazon smile (sometimes used in affiliate marketing)
            re.compile(r'https?://smile\.amazon\.(?:com|co\.uk|ca|de|fr|it|es|co\.jp|cn)/[^"\']*[?&]tag=[a-zA-Z0-9_-]+',
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
            'qksrv.net'
        ]

        patterns = []
        for domain in cj_domains:
            # Match any URL from known CJ Affiliate domains
            patterns.append(
                re.compile(rf'https?://(?:www\.)?{re.escape(domain)}/[\w/\.-]+', re.IGNORECASE)
            )

        return patterns

    def _extract_links_from_html(self, html_content: str) -> List[str]:
        """
        Extract all href URLs from HTML content using regex
        """
        try:
            links = []

            # Pattern for href attributes
            href_pattern = r'href\s*=\s*["\']([^"\']+)["\']'
            href_matches = re.finditer(href_pattern, html_content, re.IGNORECASE)
            links.extend(match.group(1) for match in href_matches)

            # Pattern for src attributes (for images, scripts, etc.)
            src_pattern = r'src\s*=\s*["\']([^"\']+)["\']'
            src_matches = re.finditer(src_pattern, html_content, re.IGNORECASE)
            links.extend(match.group(1) for match in src_matches)

            # Pattern for action attributes (forms)
            action_pattern = r'action\s*=\s*["\']([^"\']+)["\']'
            action_matches = re.finditer(action_pattern, html_content, re.IGNORECASE)
            links.extend(match.group(1) for match in action_matches)

            # Remove duplicates and return
            return list(set(links))

        except Exception as e:
            logger.error(f"Error extracting links from HTML: {e}")
            return []

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
                'all_affiliate_links': affiliate_links  # Full list for debugging
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
            'all_affiliate_links': []
        }

    def _error_result(self, error_message: str) -> Dict:
        """Return error result structure"""
        result = self._empty_result()
        result['error'] = error_message
        return result


# Module-level function for easy import and use
def find_affiliate_links(html_content: str) -> dict:
    """
    Find affiliate marketing links in HTML content

    Args:
        html_content (str): HTML content as string

    Returns:
        dict: Analysis results with keys:
            - affiliate_links_found (bool): True if any affiliate links detected
            - affiliate_networks (list): Names of detected networks
            - total_affiliate_links (int): Count of affiliate links found
            - details (list): Sample of found affiliate URLs (max 5)
    """
    try:
        scanner = AffiliateScanner()
        result = scanner.find_affiliate_links(html_content)

        # Return only the specified fields in the public API
        return {
            'affiliate_links_found': result['affiliate_links_found'],
            'affiliate_networks': result['affiliate_networks'],
            'total_affiliate_links': result['total_affiliate_links'],
            'details': result['details']
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


# Example usage and testing
if __name__ == "__main__":
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
    </body>
    </html>
    """

    print("Testing Affiliate Scanner...")
    print("=" * 50)

    # Test the function
    result = find_affiliate_links(test_html)

    print("Affiliate Scanner Test Results:")
    print(f"Affiliate Links Found: {result['affiliate_links_found']}")
    print(f"Networks Detected: {result['affiliate_networks']}")
    print(f"Total Affiliate Links: {result['total_affiliate_links']}")
    print(f"Sample URLs: {result['details']}")

    # Test with empty content
    print("\n" + "=" * 50)
    print("Testing with empty content...")
    empty_result = find_affiliate_links("")
    print(f"Empty test - Links Found: {empty_result['affiliate_links_found']}")

    # Test with no affiliate links
    print("\n" + "=" * 50)
    print("Testing with no affiliate links...")
    clean_html = "<html><body><a href='https://example.com'>Clean Link</a></body></html>"
    clean_result = find_affiliate_links(clean_html)
    print(f"Clean test - Links Found: {clean_result['affiliate_links_found']}")