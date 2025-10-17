"""
Score Aggregator Module for TruthSignal
Combines affiliate scanner and LLM analysis to generate trust scores.
"""

from typing import Dict, List


def calculate_trust_score(affiliate_data: dict, llm_data: dict) -> dict:
    """
    Calculate trust score based on affiliate links and LLM analysis results.

    Args:
        affiliate_data: Dictionary from affiliate_scanner.py containing:
            - affiliate_links_count: int
            - affiliate_domains: list
            - total_links: int
            - affiliate_ratio: float

        llm_data: Dictionary from llm_analysis.py containing:
            - disclosure_found: bool
            - disclosure_location: str ("beginning", "middle", "end", "nowhere")
            - content_intent: str ("informative", "persuasive", "mixed")
            - confidence_score: float
            - llm_analysis_raw: str

    Returns:
        Dictionary containing:
            - trust_score: "red", "yellow", "green"
            - reasons: list of human-readable explanations
            - final_analysis: combined insights summary
    """

    # Extract key metrics with safe defaults
    affiliate_count = affiliate_data.get('affiliate_links_count', 0)
    disclosure_found = llm_data.get('disclosure_found', False)
    disclosure_location = llm_data.get('disclosure_location', 'nowhere')
    content_intent = llm_data.get('content_intent', 'informative')

    reasons = []
    trust_score = "green"  # Start with baseline green

    # RED CONDITIONS (highest priority - any of these trigger red)
    red_conditions = []

    # Condition 1: High affiliate links (>3) AND no disclosure found
    if affiliate_count > 3 and not disclosure_found:
        red_conditions.append(f"High number of affiliate links ({affiliate_count}) with no disclosure")

    # Condition 2: Content intent is "persuasive" AND no disclosure found
    if content_intent == "persuasive" and not disclosure_found:
        red_conditions.append('Persuasive sales content with no disclosure')

    # Condition 3: High affiliate links (>5) regardless of disclosure
    if affiliate_count > 5:
        red_conditions.append(f"Very high number of affiliate links ({affiliate_count})")

    # If any red conditions met, return red immediately
    if red_conditions:
        return {
            'trust_score': 'red',
            'reasons': red_conditions,
            'final_analysis': _generate_final_analysis(affiliate_data, llm_data, 'red', red_conditions)
        }

    # YELLOW CONDITIONS (medium priority)
    yellow_conditions = []

    # Condition 1: Medium affiliate links (1-3) AND no disclosure
    if 1 <= affiliate_count <= 3 and not disclosure_found:
        yellow_conditions.append(f"Medium affiliate links ({affiliate_count}) with no disclosure")

    # Condition 2: Content intent is "mixed" AND no disclosure
    if content_intent == "mixed" and not disclosure_found:
        yellow_conditions.append('Mixed content intent with no disclosure')

    # Condition 3: Any affiliate links with disclosure at end/middle (not beginning)
    if affiliate_count > 0 and disclosure_found and disclosure_location in ['middle', 'end']:
        yellow_conditions.append(f'Affiliate links with disclosure at {disclosure_location} (not beginning)')

    # If any yellow conditions met, return yellow
    if yellow_conditions:
        return {
            'trust_score': 'yellow',
            'reasons': yellow_conditions,
            'final_analysis': _generate_final_analysis(affiliate_data, llm_data, 'yellow', yellow_conditions)
        }

    # GREEN CONDITIONS
    green_conditions = []

    # Condition 1: No affiliate links
    if affiliate_count == 0:
        green_conditions.append('No affiliate links detected')

    # Condition 2: Clear disclosure at beginning regardless of affiliate count
    if disclosure_found and disclosure_location == 'beginning':
        green_conditions.append(f'Clear disclosure at beginning with {affiliate_count} affiliate links')

    # If we reach here, it's green (either no affiliate links or proper disclosure)
    if not green_conditions:
        # Fallback green condition - should rarely hit this
        green_conditions.append('Minimal risk factors detected')

    return {
        'trust_score': 'green',
        'reasons': green_conditions,
        'final_analysis': _generate_final_analysis(affiliate_data, llm_data, 'green', green_conditions)
    }


def _generate_final_analysis(affiliate_data: dict, llm_data: dict, score: str, reasons: List[str]) -> str:
    """
    Generate a comprehensive final analysis combining both data sources.

    Args:
        affiliate_data: Affiliate scanner results
        llm_data: LLM analysis results
        score: Final trust score
        reasons: List of scoring reasons

    Returns:
        Comprehensive analysis string
    """

    affiliate_count = affiliate_data.get('affiliate_links_count', 0)
    disclosure_found = llm_data.get('disclosure_found', False)
    disclosure_location = llm_data.get('disclosure_location', 'nowhere')
    content_intent = llm_data.get('content_intent', 'informative')
    confidence = llm_data.get('confidence_score', 0.0)

    analysis_parts = []

    # Add trust score summary
    analysis_parts.append(f"Trust Score: {score.upper()}")

    # Add primary reasons
    analysis_parts.append("Primary Factors:")
    for reason in reasons:
        analysis_parts.append(f"  - {reason}")

    # Add affiliate analysis
    analysis_parts.append("\nAffiliate Analysis:")
    analysis_parts.append(f"  - Affiliate Links: {affiliate_count}")
    if affiliate_count > 0:
        domains = affiliate_data.get('affiliate_domains', [])
        if domains:
            analysis_parts.append(f"  - Affiliate Domains: {', '.join(domains[:3])}{'...' if len(domains) > 3 else ''}")

    # Add disclosure analysis
    analysis_parts.append("\nDisclosure Analysis:")
    analysis_parts.append(f"  - Disclosure Found: {'Yes' if disclosure_found else 'No'}")
    if disclosure_found:
        analysis_parts.append(f"  - Disclosure Location: {disclosure_location}")
    analysis_parts.append(f"  - Content Intent: {content_intent}")
    analysis_parts.append(f"  - Analysis Confidence: {confidence:.1%}")

    # Add LLM insights if available
    llm_raw = llm_data.get('llm_analysis_raw', '')
    if llm_raw and len(llm_raw) < 500:  # Only include if not too long
        analysis_parts.append(f"\nLLM Insights: {llm_raw}")

    return "\n".join(analysis_parts)


# Example usage and testing
if __name__ == "__main__":
    # Test case 1: Red scenario - high affiliate links, no disclosure
    affiliate_data_red = {
        'affiliate_links_count': 4,
        'affiliate_domains': ['amazon.com', 'shareasale.com'],
        'total_links': 10,
        'affiliate_ratio': 0.4
    }

    llm_data_red = {
        'disclosure_found': False,
        'disclosure_location': 'nowhere',
        'content_intent': 'persuasive',
        'confidence_score': 0.9,
        'llm_analysis_raw': 'Content appears to be sales-oriented with multiple product recommendations but no clear disclosure.'
    }

    # Test case 2: Yellow scenario - medium affiliate links, disclosure at end
    affiliate_data_yellow = {
        'affiliate_links_count': 2,
        'affiliate_domains': ['amazon.com'],
        'total_links': 8,
        'affiliate_ratio': 0.25
    }

    llm_data_yellow = {
        'disclosure_found': True,
        'disclosure_location': 'end',
        'content_intent': 'mixed',
        'confidence_score': 0.8,
        'llm_analysis_raw': 'Content provides useful information but includes affiliate links with disclosure at the end.'
    }

    # Test case 3: Green scenario - disclosure at beginning
    affiliate_data_green = {
        'affiliate_links_count': 3,
        'affiliate_domains': ['amazon.com', 'ebay.com'],
        'total_links': 12,
        'affiliate_ratio': 0.25
    }

    llm_data_green = {
        'disclosure_found': True,
        'disclosure_location': 'beginning',
        'content_intent': 'informative',
        'confidence_score': 0.95,
        'llm_analysis_raw': 'Clear disclosure at the beginning with informative content throughout.'
    }

    # Run tests
    test_cases = [
        ("RED Scenario", affiliate_data_red, llm_data_red),
        ("YELLOW Scenario", affiliate_data_yellow, llm_data_yellow),
        ("GREEN Scenario", affiliate_data_green, llm_data_green)
    ]

    for test_name, aff_data, llm_data in test_cases:
        print(f"\n{'=' * 50}")
        print(f"TEST: {test_name}")
        print(f"{'=' * 50}")

        result = calculate_trust_score(aff_data, llm_data)

        print(f"Trust Score: {result['trust_score']}")
        print("Reasons:")
        for reason in result['reasons']:
            print(f"  - {reason}")
        print(f"\nFinal Analysis:\n{result['final_analysis']}")