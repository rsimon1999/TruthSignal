import requests
import json

# First, let's fetch the NYTimes page content
url = "https://www.nytimes.com/wirecutter/gifts/personalized/"

try:
    # Fetch the page
    response = requests.get(url)
    html_content = response.text

    print(f"Fetched page: {len(html_content)} characters")

    # Send to our analysis API
    analysis_data = {
        "url": url,
        "html_content": html_content
    }

    analysis_response = requests.post(
        "http://localhost:8000/analyze",
        json=analysis_data
    )

    print("\n=== Analysis Results ===")
    print(f"Status Code: {analysis_response.status_code}")
    print("Response:")
    print(json.dumps(analysis_response.json(), indent=2))

except Exception as e:
    print(f"Error: {e}")