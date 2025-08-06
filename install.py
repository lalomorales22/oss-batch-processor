#!/usr/bin/env python3
"""
OSS Batch Processor - Installation Helper
Helps users choose the right installation for their needs
"""

import subprocess
import sys
import os

def print_banner():
    print("""
    ╔══════════════════════════════════════════╗
    ║     OSS Batch Processor Installer        ║
    ╚══════════════════════════════════════════╝
    """)

def run_command(cmd):
    """Run a shell command and return success status"""
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_python_version():
    """Check if Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8+ is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def check_pip():
    """Check if pip is installed"""
    if not run_command("pip --version > /dev/null 2>&1"):
        print("❌ Error: pip is not installed")
        print("   Install pip: https://pip.pypa.io/en/stable/installation/")
        sys.exit(1)
    print("✅ pip is installed")

def check_ollama():
    """Check if Ollama is accessible"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✅ Ollama server is running")
            models = response.json().get('models', [])
            if models:
                print(f"   Available models: {', '.join([m['name'] for m in models[:3]])}")
            else:
                print("   ⚠️  No models found. Run: ollama pull gpt-oss:20b")
        else:
            print("⚠️  Ollama server responded but may have issues")
    except:
        print("⚠️  Ollama server not detected at http://localhost:11434")
        print("   Start it with: ollama serve")

def install_minimal():
    """Install minimal requirements"""
    print("\n📦 Installing minimal requirements...")
    if run_command("pip install requests PyYAML Flask Flask-Cors"):
        print("✅ Minimal installation complete!")
        return True
    return False

def install_recommended():
    """Install recommended requirements"""
    print("\n📦 Installing recommended requirements...")
    requirements = [
        "requests>=2.31.0",
        "PyYAML>=6.0.1", 
        "Flask>=3.0.0",
        "Flask-Cors>=4.0.0",
        "python-dotenv>=1.0.0",
        "colorlog>=6.8.0",
        "schedule>=1.2.0",
        "watchdog>=3.0.0"
    ]
    
    if run_command(f"pip install {' '.join(requirements)}"):
        print("✅ Recommended installation complete!")
        return True
    return False

def install_full():
    """Install full requirements including optional features"""
    print("\n📦 Installing full requirements...")
    if os.path.exists("requirements.txt"):
        if run_command("pip install -r requirements.txt"):
            print("✅ Full installation complete!")
            return True
    else:
        print("❌ requirements.txt not found")
    return False

def install_dev():
    """Install development requirements"""
    print("\n📦 Installing development requirements...")
    if os.path.exists("requirements-dev.txt"):
        run_command("pip install -r requirements.txt")
        if run_command("pip install -r requirements-dev.txt"):
            print("✅ Development installation complete!")
            return True
    else:
        print("❌ requirements-dev.txt not found")
    return False

def create_env_file():
    """Create .env file template"""
    if not os.path.exists(".env"):
        print("\n📝 Creating .env file template...")
        with open(".env", "w") as f:
            f.write("""# OSS Batch Processor Environment Variables
# Uncomment and add your API keys if using web search

# SERPER_API_KEY=your_serper_api_key_here
# TAVILY_API_KEY=your_tavily_api_key_here

# Ollama settings (optional)
# OLLAMA_HOST=http://localhost:11434
# OLLAMA_MODEL=gpt-oss:20b
""")
        print("✅ Created .env file template")
    else:
        print("ℹ️  .env file already exists")

def create_directories():
    """Create necessary directories"""
    dirs = ["results", "task_configs", "workspace", "logs"]
    print("\n📁 Creating directories...")
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"   ✅ {dir_name}/")

def main():
    print_banner()
    
    # System checks
    print("🔍 Checking system requirements...\n")
    check_python_version()
    check_pip()
    
    # Installation options
    print("\n📋 Installation Options:\n")
    print("  1. Minimal   - Just the essentials (fastest)")
    print("  2. Recommended - Includes helpful extras (best for most users)")
    print("  3. Full      - All features from requirements.txt")
    print("  4. Developer - Full + development tools")
    print("  5. Cancel\n")
    
    choice = input("Select installation type (1-5): ").strip()
    
    success = False
    if choice == "1":
        success = install_minimal()
    elif choice == "2":
        success = install_recommended()
    elif choice == "3":
        success = install_full()
    elif choice == "4":
        success = install_dev()
    elif choice == "5":
        print("Installation cancelled")
        sys.exit(0)
    else:
        print("Invalid choice")
        sys.exit(1)
    
    if success:
        # Post-installation setup
        create_env_file()
        create_directories()
        
        print("\n" + "="*50)
        print("🎉 Installation Complete!")
        print("="*50)
        
        # Check Ollama
        print("\n🔍 Checking Ollama...")
        check_ollama()
        
        # Next steps
        print("\n📖 Next Steps:")
        print("  1. Start Ollama: ollama serve")
        print("  2. Pull a model: ollama pull gpt-oss:20b")
        print("  3. Run GUI version: python obp-GUI.py")
        print("  4. Or CLI version: python obp-CLI.py --help")
        print("\n💡 Tip: Start with the GUI version for easier setup!")
        print("\n📱 Access from phone: Run GUI and check the displayed URL")
    else:
        print("\n❌ Installation failed. Please check error messages above.")
        print("   Try manual installation: pip install -r requirements.txt")

if __name__ == "__main__":
    main()