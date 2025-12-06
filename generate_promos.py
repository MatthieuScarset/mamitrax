#!/usr/bin/env python3
"""
Generate funny supermarket promotional texts using OpenAI.
Saves them to promos.json for use in the game.
"""

import json
import os
from openai import OpenAI

# Initialize OpenAI client
client = None
api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('OPEN_API_KEY')
if api_key:
    client = OpenAI(api_key=api_key)
else:
    raise RuntimeError("No OpenAI API key found. Set OPENAI_API_KEY or OPEN_API_KEY environment variable.")

def generate_promo_texts(count=30):
    """Generate funny supermarket promotional texts"""
    
    prompt = f"""Generate {count} funny, ironic supermarket promotional texts that make fun of boomer stereotypes and behaviors.

Examples of the style:
- "2 for 1 on our delicious Pineapples - Now with 50% less avocado toast guilt!"
- "Senior Discount: 10% off - But only if you can find the coupon you clipped 6 months ago"
- "SPECIAL: Reading glasses on every aisle - Because you definitely forgot yours at home"
- "BUY 1 GET 1: Prune juice - Your colon will thank you (eventually)"
- "MEGA SALE: Rotary phones - For those who still don't trust smartphones"
- "Limited Offer: Newspapers - Remember when news came on paper?"
- "Flash Sale: Complaining to the manager - Now 100% FREE!"
- "TODAY ONLY: Patience lessons for millennials - Taught by people who waited 3 days for a letter"
- "CLEARANCE: Facebook conspiracy theory starter kits"
- "HOT DEAL: Uncomfortable chairs - Perfect for judging younger generations"

Make them:
1. Funny and lighthearted
2. Related to boomer stereotypes (technology confusion, nostalgia, coupons, complaining, etc.)
3. Supermarket-themed
4. Short (under 80 characters if possible)
5. A mix of products (food, household items, activities)

Return ONLY a JSON array of strings, no other text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a witty copywriter creating humorous supermarket promotional texts that gently poke fun at boomer culture."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
        )
        
        content = response.choices[0].message.content.strip()
        
        # Parse JSON from response
        # Remove markdown code blocks if present
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
            content = content.strip()
        
        promos = json.loads(content)
        return promos
        
    except Exception as e:
        print(f"❌ Error generating promos: {e}")
        return []

def save_promos(promos, filename='promos.json'):
    """Save promotional texts to JSON file"""
    with open(filename, 'w') as f:
        json.dump({
            'supermarket_name': 'MAMITRAX',
            'promos': promos
        }, f, indent=2)
    print(f"✅ Saved {len(promos)} promotional texts to {filename}")

def main():
    print("🎨 Generating funny supermarket promotional texts...")
    print("(This may take a moment...)\n")
    
    promos = generate_promo_texts(30)
    
    if promos:
        print(f"\n📋 Generated {len(promos)} promos:")
        for i, promo in enumerate(promos[:5], 1):
            print(f"  {i}. {promo}")
        if len(promos) > 5:
            print(f"  ... and {len(promos) - 5} more")
        
        save_promos(promos)
        print("\n✨ Done! Use these promos in your game.")
    else:
        print("❌ Failed to generate promos")

if __name__ == '__main__':
    main()
