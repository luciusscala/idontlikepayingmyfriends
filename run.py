#!/usr/bin/env python3
"""
Startup script for the Trip Commitment System
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if required environment variables are set"""
    load_dotenv()
    
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_key:
        print("❌ STRIPE_SECRET_KEY not found in environment")
        print("Please create a .env file with your Stripe test key:")
        print("STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here")
        return False
    
    if not stripe_key.startswith("sk_test_"):
        print("⚠️  Warning: STRIPE_SECRET_KEY doesn't start with 'sk_test_'")
        print("Make sure you're using Stripe test keys, not live keys!")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    print("✅ Environment configured correctly")
    return True

def main():
    print("🚀 Starting Trip Commitment System")
    print("=" * 40)
    
    if not check_environment():
        sys.exit(1)
    
    print("\n📋 Available endpoints:")
    print("  POST /trips - Create a new trip")
    print("  POST /trips/{trip_id}/commit - Commit to a trip")
    print("  GET /trips/{trip_id}/status - Get trip status")
    print("  GET / - Health check")
    
    print("\n🧪 To test the API, run: python test_api.py")
    print("\n🌐 API will be available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    
    print("\n" + "=" * 40)
    
    # Import and run the app
    try:
        import uvicorn
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("❌ uvicorn not found. Please install dependencies:")
        print("pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
