#!/usr/bin/env python3
"""
Quick test to verify affiliate scanner is working
"""

import sys
import os

# Make sure we can import the module
sys.path.insert(0, os.path.dirname(__file__))

try:
    from affiliate_scanner import find_affiliate_links

    print("✅ Successfully imported affiliate_scanner")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def run_basic_tests():
    """Run basic functionality tests"""
    print("\n" + "=" * 60)
    print("RUNNING BASIC FUNCTIONALITY TESTS")
    print("=" * 60)

    test_cases = [
        {
            "name": "Amazon Associate Link",
            "html": '<a href="https://www.amazon.com/dp/B08N5WRWNW?tag=myaffiliate-20">Product</a>',
            "should_find": True,
            "expected_networks": ["Amazon Associates"]
        },
        {
            "name": "Amazon Short Link",
            "html": '<a href="https://amzn.to/3abc123">Short Link</a>',
            "should_find": True,
            "expected_networks": ["Amazon Associates"]
        },
        {
            "name": "ShareASale Link",
            "html": '<a href="https://www.shareasale.com/r.cfm?m=12345&u=567">ShareASale</a>',
            "should_find": True,
            "expected_networks": ["ShareASale"]
        },
        {
            "name": "CJ Affiliate Link",
            "html": '<a href="https://www.anrdoezrs.net/click-12345">CJ Link</a>',
            "should_find": True,
            "expected_networks": ["CJ Affiliate"]
        },
        {
            "name": "Regular Link (No Affiliate)",
            "html": '<a href="https://example.com/product?tag=123">Regular Product</a>',
            "should_find": False,
            "expected_networks": []
        },
        {
            "name": "Empty HTML",
            "html": "",
            "should_find": False,
            "expected_networks": []
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print("-" * 40)

        try:
            result = find_affiliate_links(test['html'])

            # Check if affiliate links were found as expected
            if result['affiliate_links_found'] == test['should_find']:
                print(f"✅ Found affiliate links: {result['affiliate_links_found']} (expected: {test['should_find']})")

                # Check networks if links were found
                if result['affiliate_links_found']:
                    print(f"   Networks: {result['affiliate_networks']}")
                    print(f"   Total links: {result['total_affiliate_links']}")
                    if result['details']:
                        print(f"   Sample: {result['details'][0]}")

                    # Verify expected networks
                    if set(result['affiliate_networks']) == set(test['expected_networks']):
                        print(f"✅ Correct networks detected")
                    else:
                        print(
                            f"❌ Network mismatch. Expected: {test['expected_networks']}, Got: {result['affiliate_networks']}")
                        failed += 1
                        continue

                passed += 1

            else:
                print(
                    f"❌ FAIL: Expected affiliate_links_found={test['should_find']}, but got {result['affiliate_links_found']}")
                failed += 1

        except Exception as e:
            print(f"❌ ERROR during test: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")

    if failed == 0:
        print("🎉 ALL TESTS PASSED! Affiliate scanner is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

    return failed == 0


def test_real_world_examples():
    """Test with more complex, real-world HTML"""
    print("\n" + "=" * 60)
    print("REAL-WORLD EXAMPLE TEST")
    print("=" * 60)

    complex_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Affiliate Review Site</title>
    </head>
    <body>
        <header>
            <nav>
                <a href="/">Home</a>
                <a href="/about">About</a>
                <a href="https://twitter.com/user">Twitter</a>
            </nav>
        </header>

        <article class="review">
            <h1>Best Wireless Headphones</h1>
            <p>These are amazing headphones I found on Amazon:</p>
            <a href="https://www.amazon.com/dp/B08N5WRWNW?tag=myblog-20&psc=1" class="buy-button">
                Buy on Amazon
            </a>

            <p>Or get them through this short link:</p>
            <a href="https://amzn.to/3xyz123">Amazon Short Link</a>

            <p>Also available via ShareASale:</p>
            <a href="https://www.shareasale.com/r.cfm?b=789&u=456&m=123&urllink=">
                Alternative Store
            </a>

            <img src="https://dpbolvw.net/track-12345" width="1" height="1" style="display:none">
        </article>

        <footer>
            <a href="/privacy">Privacy Policy</a>
            <a href="/contact">Contact</a>
        </footer>
    </body>
    </html>
    """

    print("Testing complex HTML with mixed affiliate and regular links...")
    result = find_affiliate_links(complex_html)

    print(f"Affiliate links found: {result['affiliate_links_found']}")
    if result['affiliate_links_found']:
        print(f"Networks detected: {result['affiliate_networks']}")
        print(f"Total affiliate links: {result['total_affiliate_links']}")
        print("Sample URLs:")
        for url in result['details']:
            print(f"  - {url}")

    expected_min_links = 3  # Should find at least Amazon, Amazon short, ShareASale, CJ tracker
    if result['total_affiliate_links'] >= expected_min_links:
        print(f"✅ Real-world test PASSED - found {result['total_affiliate_links']} affiliate links")
        return True
    else:
        print(
            f"❌ Real-world test FAILED - expected at least {expected_min_links} links, found {result['total_affiliate_links']}")
        return False


if __name__ == "__main__":
    print("🔍 TruthSignal Affiliate Scanner - Quick Test")
    print("=" * 60)

    # Run basic tests
    basic_ok = run_basic_tests()

    # Run real-world test
    real_world_ok = test_real_world_examples()

    print("\n" + "=" * 60)
    if basic_ok and real_world_ok:
        print("🎉 ALL TESTS PASSED! Scanner is ready for production.")
    else:
        print("⚠️  Some tests failed. Check the scanner implementation.")
    print("=" * 60)