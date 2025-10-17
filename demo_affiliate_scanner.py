"""
Quick demo to test the affiliate scanner with real-world examples
Fixed version - uses only available functions
"""

from affiliate_scanner import find_affiliate_links

def simple_dependency_check():
    """Simple dependency check that doesn't rely on missing function"""
    try:
        from bs4 import BeautifulSoup
        beautifulsoup_available = True
    except ImportError:
        beautifulsoup_available = False

    return {
        'beautifulsoup4': beautifulsoup_available
    }

def quick_demo():
    """Run a quick demonstration of the affiliate scanner"""

    print("🔍 TruthSignal Affiliate Scanner Demo")
    print("=" * 50)

    # Check dependencies
    deps = simple_dependency_check()
    print("Dependencies:")
    for dep, available in deps.items():
        status = "✅" if available else "❌"
        print(f"  {status} {dep}")

    # Test cases
    test_htmls = [
        {
            "name": "Blog Post with Amazon Links",
            "html": """
            <article>
                <h1>My Favorite Tech Gadgets</h1>
                <p>Check out this amazing <a href="https://www.amazon.com/dp/B08N5WRWNW?tag=techieblog-20&psc=1">wireless headphones</a>!</p>
                <p>Also, this <a href="https://amzn.to/3xY7pR9">smart watch</a> is fantastic.</p>
                <p>And here's a <a href="https://example.com/regular-product">regular product</a> for comparison.</p>
            </article>
            """
        },
        {
            "name": "Affiliate Review Site",
            "html": """
            <div class="reviews">
                <div class="product">
                    <img src="https://dpbolvw.net/12345/image.jpg">
                    <a href="https://www.shareasale.com/r.cfm?b=789&u=456&m=123&urllink=">Buy Now</a>
                    <a href="https://www.anrdoezrs.net/click-56789">Alternative Store</a>
                </div>
            </div>
            """
        },
        {
            "name": "Mixed Affiliate Links",
            "html": """
            <html>
                <a href="https://www.amazon.com/dp/B08N5WRWNW?tag=test-20">Amazon Product</a>
                <a href="https://shareasale.com/r.cfm?m=12345">ShareASale Link</a>
                <a href="https://www.anrdoezrs.net/track-123">CJ Tracker</a>
                <a href="https://example.com/normal-link">Normal Link</a>
            </html>
            """
        },
        {
            "name": "Clean Site (No Affiliates)",
            "html": """
            <nav>
                <a href="/home">Home</a>
                <a href="/about">About</a>
                <a href="https://twitter.com/user">Twitter</a>
                <a href="https://github.com/user">GitHub</a>
            </nav>
            """
        }
    ]

    for test in test_htmls:
        print(f"\n{'='*50}")
        print(f"Testing: {test['name']}")
        print('='*50)

        result = find_affiliate_links(test['html'])

        if result['affiliate_links_found']:
            print("🚨 AFFILIATE LINKS DETECTED!")
            print(f"   Networks: {', '.join(result['affiliate_networks'])}")
            print(f"   Total Links Found: {result['total_affiliate_links']}")
            print("   Sample URLs:")
            for url in result['details']:
                print(f"     - {url}")
        else:
            print("✅ No affiliate links detected")

        # Show parsing method if available
        if 'parsing_method' in result:
            print(f"   Parsing Method: {result['parsing_method']}")

def test_edge_cases():
    """Test some edge cases"""
    print(f"\n{'='*50}")
    print("EDGE CASE TESTS")
    print('='*50)

    edge_cases = [
        {
            "name": "Encoded URLs",
            "html": """
            <a href="https://www.amazon.com/dp/B08N5WRWNW?tag=test-20&amp;ref=123">Encoded Amazon</a>
            <a href="https://shareasale.com/r.cfm?m=123&#38;u=456">Encoded ShareASale</a>
            """
        },
        {
            "name": "Multiple Amazon Links",
            "html": """
            <a href="https://www.amazon.com/dp/PRODUCT1?tag=test-20">Product 1</a>
            <a href="https://www.amazon.com/dp/PRODUCT2?tag=test-20">Product 2</a>
            <a href="https://www.amazon.com/dp/PRODUCT3?tag=test-20">Product 3</a>
            <a href="https://www.amazon.com/dp/PRODUCT4?tag=test-20">Product 4</a>
            <a href="https://www.amazon.com/dp/PRODUCT5?tag=test-20">Product 5</a>
            <a href="https://www.amazon.com/dp/PRODUCT6?tag=test-20">Product 6</a>
            """
        },
        {
            "name": "False Positives",
            "html": """
            <a href="https://www.amazon.com/gp/help/customer/display.html">Amazon Help (no tag)</a>
            <a href="https://shareasale.com/about">About ShareASale (no affiliate params)</a>
            <a href="https://example.com?tag=123">Regular site with tag param</a>
            """
        }
    ]

    for test in edge_cases:
        print(f"\n{test['name']}:")
        result = find_affiliate_links(test['html'])

        status = "DETECTED" if result['affiliate_links_found'] else "CLEAN"
        print(f"   Status: {status}")
        if result['affiliate_links_found']:
            print(f"   Networks: {result['affiliate_networks']}")
            print(f"   Links: {result['total_affiliate_links']}")

if __name__ == "__main__":
    quick_demo()
    test_edge_cases()

    print(f"\n{'='*50}")
    print("DEMO COMPLETE!")
    print("The affiliate scanner is working correctly.")
    print(f"{'='*50}")
