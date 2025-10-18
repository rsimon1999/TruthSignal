import requests
import json

# Test data
test_data = {
    "url": "https://example.com",
    "html_content": """
    <html>
        <body>
            <h1>Test Website</h1>
            <p>This is a sample website with some content.</p>
            <a href="https://amazon.com/ref=affiliate_123">Buy product</a>
            <a href="https://example.com/normal-link">Normal link</a>
        </body>
    </html>
    """
}

# Send request
response = requests.post(
    "http://localhost:8000/analyze",
    json=test_data
)

print("Status Code:", response.status_code)
print("Response:")
print(json.dumps(response.json(), indent=2))