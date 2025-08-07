#!/usr/bin/env python3
"""
Test script to debug connection issues
"""

import os
import requests
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not available")

def test_ollama_connection():
    """Test Ollama connection"""
    ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    print(f"\n🔗 Testing Ollama connection to: {ollama_host}")
    
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is reachable")
            models = response.json().get('models', [])
            print(f"📦 Available models: {len(models)}")
            for model in models[:3]:  # Show first 3
                print(f"   - {model['name']}")
        else:
            print(f"❌ Ollama responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to connect to Ollama: {e}")
        print("\n💡 Tips:")
        print("   - Make sure Ollama is running: ollama serve")
        if "host.docker.internal" in ollama_host:
            print("   - If running in Docker, ensure Ollama is on host machine")
        print(f"   - Try: curl {ollama_host}/api/tags")

def test_api_keys():
    """Test API key configuration"""
    print("\n🔑 Testing API keys")
    
    serper_key = os.getenv('SERPER_API_KEY')
    tavily_key = os.getenv('TAVILY_API_KEY')
    
    if serper_key:
        if 'your_' in serper_key:
            print("⚠️  SERPER_API_KEY contains placeholder text")
        else:
            print("✅ SERPER_API_KEY is set")
    else:
        print("❌ SERPER_API_KEY not found")
    
    if tavily_key:
        if 'your_' in tavily_key:
            print("⚠️  TAVILY_API_KEY contains placeholder text")
        else:
            print("✅ TAVILY_API_KEY is set")
    else:
        print("❌ TAVILY_API_KEY not found")
    
    if not serper_key and not tavily_key:
        print("\n💡 No API keys configured. Web search will use mock results.")
        print("   Get free keys from:")
        print("   - Serper: https://serper.dev")
        print("   - Tavily: https://tavily.com")

def test_file_structure():
    """Test file structure"""
    print("\n📁 Testing file structure")
    
    required_files = [
        'obp-GUI.py',
        'obp-CLI.py',
        'processor_config.yaml',
        'task_configs/search_tasks.yaml'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
    
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file exists")
    else:
        print("⚠️  .env file not found")
        if Path('.env.example').exists():
            print("   Copy .env.example to .env and add your API keys")

def main():
    print("="*60)
    print("🔧 OSS BATCH PROCESSOR - CONNECTION TEST")
    print("="*60)
    
    test_file_structure()
    test_ollama_connection()
    test_api_keys()
    
    print("\n" + "="*60)
    print("🏁 Test complete")
    print("="*60)

if __name__ == "__main__":
    main()