#!/usr/bin/env python3
"""
Test script for DALL-E integration
"""

import os
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_dalle_integration():
    """Test DALL-E image generation with correct settings."""
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_AUTH_TOKEN")
    if not api_key:
        print("❌ OPENAI_AUTH_TOKEN not found in environment")
        return False
    
    print(f"✅ Found OpenAI API key: {api_key[:10]}...")
    
    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Test prompt
        test_prompt = "STYLE: Produce an image in a loose and airy pen & ink wash style, in 2240 × 1256 landscape orientation. The colouring schema must be colourful but washed out, and the image should 'fade' (as irregular brushstrokes) to pure white on all sides with no hard edges on the left or right or top or bottom.  SUBJECT:  A cozy modern Scottish living room, fireplace ablaze with crackling logs, casting a warm, gentle glow. Plush armchair holds a middle-aged woman in a sweater and skirt, engrossed in an old book. Young girl in school uniform leans against her knees, listening intently. Tartan blankets,framed loch picture on wall. A cup of steaming tea on table between them. Corner reveals a modern laptop with headphones, symbolizing technology's role in contemporary storytelling."
        
        print(f"🎨 Testing DALL-E with prompt: {test_prompt[:50]}...")
        
        # Generate image with correct settings
        response = client.images.generate(
            model="dall-e-3",
            prompt=test_prompt,
            size="1792x1024",  # Supported landscape size
            quality="standard",
            n=1
        )
        
        if response.data and response.data[0].url:
            image_url = response.data[0].url
            print(f"✅ DALL-E test successful!")
            print(f"📸 Generated image URL: {image_url}")
            return True
        else:
            print("❌ No image URL in response")
            return False
            
    except Exception as e:
        print(f"❌ DALL-E test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing DALL-E Integration...")
    success = test_dalle_integration()
    if success:
        print("🎉 DALL-E integration test passed!")
    else:
        print("💥 DALL-E integration test failed!") 