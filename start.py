#!/usr/bin/env python3
"""
Startup script for Personal AI Assistant
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import twilio
        import openai
        import schedule
        import requests
        import pydantic
        import dateutil
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_config():
    """Check if config.env exists and has required variables"""
    config_path = Path("config.env")
    if not config_path.exists():
        print("❌ config.env file not found")
        print("Please copy config.env and fill in your API keys")
        return False
    
    # Check for required environment variables
    required_vars = [
        "OPENAI_API_KEY",
        "SUPERMEMORY_API_KEY", 
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
        "USER_PHONE_NUMBER"
    ]
    
    missing_vars = []
    with open(config_path) as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=your_" in content or f"{var}=" not in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or incomplete configuration: {', '.join(missing_vars)}")
        print("Please update config.env with your actual API keys")
        return False
    
    print("✅ Configuration looks good")
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Personal AI Assistant...")
    print()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check configuration
    if not check_config():
        sys.exit(1)
    
    print()
    print("🎉 All checks passed! Starting the application...")
    print("📱 The assistant will be available at: http://localhost:8000")
    print("📞 Make sure your Twilio webhook points to: http://your-domain.com/sms")
    print()
    print("Press Ctrl+C to stop the application")
    print("-" * 50)
    
    # Start the application
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Personal AI Assistant stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


