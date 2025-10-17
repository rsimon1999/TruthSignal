"""
LLM Analysis Module for TruthSignal
Analyzes website content for disclosures and intent using free LLM APIs.
"""

import json
import logging
import os
import requests
from typing import Dict, Optional, List
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMAnalysisError(Exception):
    """Custom exception for LLM analysis failures"""
    pass

class FreeLLMClient:
    """Client for various free LLM providers"""

    def __init__(self):
        self.providers = self._setup_providers()

    def _setup_providers(self) -> List[Dict]:
        """Setup available free LLM providers"""
        return [
            {
                'name': 'deepseek',
                'base_url': 'https://api.deepseek.com/v1',
                'api_key': os.getenv('DEEPSEEK_API_KEY'),
                'model': 'deepseek-chat',
                'headers': lambda key: {
                    'Authorization': f'Bearer {key}',
                    'Content-Type': 'application/json'
                }
            },
            {
                'name': 'groq',
                'base_url': 'https://api.groq.com/openai/v1',
                'api_key': os.getenv('GROQ_API_KEY'),
                'model': 'llama-3.1-8b-instant',  # Fast and free - updated model
                'headers': lambda key: {
                    'Authorization': f'Bearer {key}',
                    'Content-Type': 'application/json'
                }
            }
        ]

    def get_available_providers(self) -> List[str]:
        """Get list of providers with API keys available"""
        available = []
        for provider in self.providers:
            if provider['api_key']:
                available.append(provider['name'])
        return available

    def call_provider(self, prompt: str, provider_name: str = None) -> str:
        """
        Call LLM provider with fallback logic
        """
        # Try specified provider first, then fall back to available ones
        providers_to_try = []

        if provider_name:
            # Try the specified provider
            target_provider = next((p for p in self.providers if p['name'] == provider_name), None)
            if target_provider and target_provider['api_key']:
                providers_to_try.append(target_provider)

        # Add other available providers as fallbacks
        for provider in self.providers:
            if provider['api_key'] and provider not in providers_to_try:
                providers_to_try.append(provider)

        if not providers_to_try:
            raise LLMAnalysisError("No LLM providers configured. Please set at least one API key.")

        # Try each provider until one works
        last_error = None
        for provider in providers_to_try:
            try:
                logger.info(f"Trying provider: {provider['name']}")
                return self._make_request(provider, prompt)
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider['name']} failed: {e}")
                continue

        raise LLMAnalysisError(f"All providers failed. Last error: {last_error}")

    def _make_request(self, provider: Dict, prompt: str) -> str:
        """Make actual API request to provider"""
        url = f"{provider['base_url']}/chat/completions"

        payload = {
            'model': provider['model'],
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an expert analyst specialized in identifying content disclosures and intent. Provide precise, structured JSON responses.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 1000,
            'temperature': 0.1,
            'response_format': {'type': 'json_object'}
        }

        headers = provider['headers'](provider['api_key'])

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code != 200:
            raise LLMAnalysisError(f"API request failed: {response.status_code} - {response.text}")

        result = response.json()
        return result['choices'][0]['message']['content']

def analyze_with_llm(cleaned_text: str, preferred_provider: str = None) -> Dict:
    """
    Analyze cleaned text for sponsorship disclosures and content intent using free LLM APIs.

    Args:
        cleaned_text: Text content with HTML tags removed
        preferred_provider: Preferred provider name ('deepseek', 'groq')

    Returns:
        Dictionary containing:
            - disclosure_found: boolean
            - disclosure_location: string ("beginning", "middle", "end", "nowhere")
            - content_intent: string ("informative", "persuasive", "mixed")
            - confidence_score: float (0.0 to 1.0)
            - llm_analysis_raw: string (raw LLM reasoning)
            - provider_used: string (which LLM provider was used)

    Raises:
        LLMAnalysisError: If analysis fails due to API errors or timeouts
    """

    # Initialize LLM client
    client = FreeLLMClient()

    # Check available providers
    available_providers = client.get_available_providers()
    if not available_providers:
        raise LLMAnalysisError(
            "No LLM API keys configured. Please set one of:\n"
            "- DEEPSEEK_API_KEY (get free tier at https://platform.deepseek.com/)\n"
            "- GROQ_API_KEY (get free tier at https://console.groq.com/)\n"
        )

    logger.info(f"Available LLM providers: {available_providers}")

    # Optimized prompt template
    prompt_template = """
Analyze the following text content and provide a structured assessment of sponsorship disclosures and content intent.

TEXT TO ANALYZE:
{text}

INSTRUCTIONS:
1. Disclosure Analysis:
   - Look for clear statements about sponsorships, affiliate links, partnerships, paid content, or compensation
   - Identify if disclosure is present and its location in the content
   - Consider phrases like "sponsored", "affiliate", "paid", "commission", "partner", "advertisement"

2. Content Intent Assessment:
   - "informative": Primarily educational, factual, or news-oriented without strong sales pressure
   - "persuasive": Clearly sales-oriented, promotional, or trying to convince to purchase
   - "mixed": Combination of informative and persuasive elements

3. Provide your analysis in this exact JSON format:
{{
    "disclosure_found": true/false,
    "disclosure_location": "beginning/middle/end/nowhere",
    "content_intent": "informative/persuasive/mixed",
    "confidence_score": 0.0-1.0,
    "reasoning": "Your detailed reasoning here"
}}

CRITICAL GUIDELINES:
- Be precise about disclosure location: "beginning" (first 20%), "middle" (20-80%), "end" (last 20%), "nowhere"
- Confidence score should reflect certainty in your assessment (0.5 = uncertain, 0.9+ = very confident)
- If no clear disclosure is found, set disclosure_found to false and location to "nowhere"
- Consider the overall tone, language, and explicit statements in the content
- Base your assessment on the actual text content, not assumptions
"""

    try:
        # Prepare the prompt
        formatted_prompt = prompt_template.format(text=cleaned_text[:8000])  # Limit text length

        logger.info("Sending request to LLM API for analysis")

        # Make API call
        llm_response = client.call_provider(formatted_prompt, preferred_provider)
        logger.info("Received response from LLM")

        # Parse JSON response from LLM
        try:
            analysis_result = json.loads(llm_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Raw response: {llm_response}")
            raise LLMAnalysisError(f"Invalid JSON response from LLM: {e}")

        # Validate required fields
        required_fields = ['disclosure_found', 'disclosure_location', 'content_intent', 'confidence_score', 'reasoning']
        for field in required_fields:
            if field not in analysis_result:
                raise LLMAnalysisError(f"Missing required field in LLM response: {field}")

        # Validate field types and values
        if not isinstance(analysis_result['disclosure_found'], bool):
            raise LLMAnalysisError("disclosure_found must be a boolean")

        valid_locations = ['beginning', 'middle', 'end', 'nowhere']
        if analysis_result['disclosure_location'] not in valid_locations:
            raise LLMAnalysisError(f"disclosure_location must be one of: {valid_locations}")

        valid_intents = ['informative', 'persuasive', 'mixed']
        if analysis_result['content_intent'] not in valid_intents:
            raise LLMAnalysisError(f"content_intent must be one of: {valid_intents}")

        confidence = analysis_result['confidence_score']
        if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
            raise LLMAnalysisError("confidence_score must be a float between 0.0 and 1.0")

        # Return structured result
        return {
            'disclosure_found': analysis_result['disclosure_found'],
            'disclosure_location': analysis_result['disclosure_location'],
            'content_intent': analysis_result['content_intent'],
            'confidence_score': float(confidence),
            'llm_analysis_raw': analysis_result['reasoning'],
            'provider_used': 'multiple' if len(available_providers) > 1 else available_providers[0]
        }

    except requests.exceptions.Timeout:
        error_msg = "LLM API request timed out"
        logger.error(error_msg)
        raise LLMAnalysisError(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"API request error: {str(e)}"
        logger.error(error_msg)
        raise LLMAnalysisError(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during LLM analysis: {str(e)}"
        logger.error(error_msg)
        raise LLMAnalysisError(error_msg)

# Updated test script
def test_providers():
    """Test which providers are available"""
    client = FreeLLMClient()
    available = client.get_available_providers()

    print("🔍 Checking available LLM providers...")
    print(f"Available providers: {available}")

    providers_info = [
        ('DeepSeek', 'DEEPSEEK_API_KEY'),
        ('Groq', 'GROQ_API_KEY')
    ]

    for name, env_var in providers_info:
        key = os.getenv(env_var)
        status = "✅ Found" if key else "❌ Missing"
        print(f"{name} ({env_var}): {status}")
        if key:
            masked_key = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
            print(f"   Key preview: {masked_key}")

    if available:
        print(f"\n🎉 Ready to use: {', '.join(available)}")
        return True
    else:
        print("\n❌ No providers configured. Please set API keys.")
        return False

# Example usage and testing
if __name__ == "__main__":
    # Test provider availability first
    if test_providers():
        # Test with sample content if providers are available
        sample_text = """
        This post contains affiliate links, which means I may earn a commission if you make a purchase through these links. 
        
        Today I want to share my honest review of the new XYZ product. I've been testing it for the past month and here's what I found...
        
        The product has excellent features and I highly recommend it for anyone looking for a reliable solution. 
        Don't forget to use my discount code for 10% off!
        """

        try:
            print("\n🧪 Testing analysis with sample text...")
            result = analyze_with_llm(sample_text)
            print("✅ Analysis Result:")
            print(json.dumps(result, indent=2))
        except LLMAnalysisError as e:
            print(f"❌ Analysis failed: {e}")
    else:
        print("\n📝 SETUP INSTRUCTIONS:")
        print("1. Get free API keys from:")
        print("   - DeepSeek: https://platform.deepseek.com/ (Free tier available)")
        print("   - Groq: https://console.groq.com/ (Free tier available)")
        print("\n2. Set environment variables:")
        print("   export DEEPSEEK_API_KEY='your_key_here'")
        print("   # or")
        print("   export GROQ_API_KEY='your_key_here'")
        print("\n3. Reload your shell: source ~/.bashrc")