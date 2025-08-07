#!/usr/bin/env python3
"""
Setup script for OSS Batch Processor
Checks dependencies and configures environment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_ollama():
    """Check if Ollama is installed"""
    if shutil.which('ollama'):
        print("✅ Ollama is installed")
        # Try to check if it's running
        try:
            result = subprocess.run(['curl', '-s', 'http://localhost:11434'], 
                                  capture_output=True, timeout=2)
            if result.returncode == 0:
                print("✅ Ollama server is running")
            else:
                print("⚠️  Ollama server is not running")
                print("   Run: ollama serve")
        except:
            print("⚠️  Could not check Ollama server status")
        return True
    else:
        print("❌ Ollama not found")
        print("   Install from: https://ollama.ai")
        return False

def check_model():
    """Check if the model is available"""
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True)
        if 'gpt-oss:20b' in result.stdout:
            print("✅ Model gpt-oss:20b is available")
            return True
        else:
            print("⚠️  Model gpt-oss:20b not found")
            print("   Run: ollama pull gpt-oss:20b")
            print("   Or use a different model like: ollama pull llama2")
            return True  # Not critical
    except:
        print("⚠️  Could not check models")
        return True

def setup_directories():
    """Create necessary directories"""
    dirs = ['workspace', 'results', 'logs', 'task_configs']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Directories created")

def check_env_file():
    """Check for .env file"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        print("⚠️  No .env file found")
        print("   Copy .env.example to .env and add your API keys")
        print("   - Serper API: https://serper.dev")
        print("   - Tavily API: https://tavily.com")
        return False
    elif env_file.exists():
        print("✅ .env file exists")
        # Check if API keys are set
        with open(env_file) as f:
            content = f.read()
            if 'your_' in content:
                print("⚠️  API keys not configured in .env")
                print("   Add your Serper or Tavily API keys")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Checking dependencies...")
    
    # Core dependencies
    core_deps = [
        'requests',
        'pyyaml',
        'flask',
        'flask-cors',
        'python-dotenv'
    ]
    
    missing_deps = []
    for dep in core_deps:
        try:
            __import__(dep.replace('-', '_'))
            print(f"✅ {dep} is installed")
        except ImportError:
            missing_deps.append(dep)
            print(f"❌ {dep} is not installed")
    
    if missing_deps:
        print(f"\n📥 To install missing dependencies, run:")
        print(f"   pip install {' '.join(missing_deps)}")
        print(f"\n   Or install all at once:")
        print(f"   pip install requests pyyaml flask flask-cors python-dotenv")

def check_ports():
    """Check if required ports are available"""
    import socket
    
    port = 5001  # GUI port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result == 0:
        print(f"⚠️  Port {port} is already in use")
        print(f"   The GUI might not start on this port")
    else:
        print(f"✅ Port {port} is available")

def display_summary():
    """Display setup summary"""
    print("\n" + "="*60)
    print("🚀 SETUP COMPLETE")
    print("="*60)
    print("\nQuick Start:")
    print("1. Start Ollama:     ollama serve")
    print("2. Run GUI:          python obp-GUI.py")
    print("3. Or run CLI:       python obp-CLI.py --help")
    print("\nAccess GUI at:       http://localhost:5001")
    print("\nOptional:")
    print("- Add API keys to .env for web search")
    print("- Pull a model:      ollama pull gpt-oss:20b")
    print("="*60)

def main():
    print("="*60)
    print("🔧 OSS BATCH PROCESSOR - SETUP")
    print("="*60)
    print("\nChecking environment...\n")
    
    # Run checks
    checks = [
        ("Python Version", check_python_version),
        ("Ollama", check_ollama),
        ("Model", check_model),
        ("Directories", setup_directories),
        ("Environment File", check_env_file),
        ("Ports", check_ports)
    ]
    
    all_good = True
    for name, check_func in checks:
        if not check_func():
            all_good = False
        print()
    
    # Install dependencies
    install_dependencies()
    
    # Display summary
    display_summary()
    
    if not all_good:
        print("\n⚠️  Some checks failed. Please address the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())