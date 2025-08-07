# Requirements & Installation Guide

## 📦 Quick Install Options

### Option 1: Interactive Installer (Recommended)
```bash
python install.py
```
This will guide you through installation options and check your system.

### Option 2: Make Commands (Unix/Linux/Mac)
```bash
make install        # Recommended installation
make setup         # Install + create directories
make run-gui       # Start GUI after installation
```

### Option 3: Direct pip Install
```bash
# Minimal (just essentials)
pip install -r requirements-minimal.txt

# Or recommended (with extras)
pip install requests PyYAML Flask Flask-Cors python-dotenv colorlog schedule watchdog

# Or full installation
pip install -r requirements.txt
```

### Option 4: Modern Python (pip with pyproject.toml)
```bash
# Install with recommended extras
pip install -e ".[recommended]"

# Or install everything including dev tools
pip install -e ".[all]"
```

## 📋 Requirements Files Explained

### `requirements.txt` (Main file)
The primary requirements file with all dependencies organized by category:
- **Core**: Essential packages (requests, PyYAML, Flask)
- **GUI**: Flask and Flask-CORS for web interface
- **CLI Enhancements**: Schedule, watchdog for advanced features
- **Optional**: Web search APIs, email, etc.

Use this for standard installation.

### `requirements-minimal.txt`
Bare minimum to run the application:
```txt
requests>=2.31.0
PyYAML>=6.0.1
Flask>=3.0.0
Flask-Cors>=4.0.0
```
Use this for testing or resource-constrained environments.

### `requirements-dev.txt`
Development tools for contributors:
- Code formatting (black, isort)
- Linting (flake8, pylint, mypy)
- Testing (pytest, coverage)
- Documentation (sphinx)

Use with: `pip install -r requirements.txt -r requirements-dev.txt`

### `pyproject.toml`
Modern Python packaging configuration:
- Defines project metadata
- Specifies dependency groups
- Configures development tools

Use with: `pip install -e ".[recommended]"`

## 🎯 Which Installation Should I Choose?

### For Regular Users
```bash
# Run the interactive installer
python install.py
# Choose option 2 (Recommended)
```

### For Minimal Setup
```bash
pip install -r requirements-minimal.txt
```

### For Developers
```bash
pip install -r requirements.txt -r requirements-dev.txt
# Or using pyproject.toml
pip install -e ".[all]"
```

### For Docker Users
```bash
# Use the minimal requirements in Dockerfile
FROM python:3.11-slim
COPY requirements-minimal.txt .
RUN pip install -r requirements-minimal.txt
```

## 🔧 Installation by Feature

### Just GUI Version
```bash
pip install requests PyYAML Flask Flask-Cors
```

### Just CLI Version
```bash
pip install requests PyYAML
# Optional but recommended:
pip install colorlog schedule watchdog python-dotenv
```

### With Web Search
```bash
# Install base requirements first, then:
pip install google-search-results  # For Serper API
# OR
pip install tavily-python          # For Tavily API
```

### With Email Notifications
```bash
# Install base requirements first, then:
pip install sendgrid  # For SendGrid
# OR
pip install yagmail   # For Gmail
```

## 🐍 Python Version Requirements

- **Minimum**: Python 3.8+
- **Recommended**: Python 3.10+
- **Tested on**: Python 3.8, 3.9, 3.10, 3.11, 3.12

Check your version:
```bash
python --version
```

## 🚀 Post-Installation Setup

After installing dependencies:

1. **Create necessary directories**:
```bash
mkdir -p results task_configs workspace logs
```

2. **Create .env file** (for API keys):
```bash
cat > .env << EOF
# Optional API keys for web search
# SERPER_API_KEY=your_key_here
# TAVILY_API_KEY=your_key_here
EOF
```

3. **Verify Ollama**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it:
ollama serve

# Pull a model:
ollama pull gpt-oss:20b
```

4. **Test installation**:
```bash
# Test GUI
python oss-GUI.py

# Test CLI
python oss-CLI.py --help
```

## 📊 Dependency Tree

```
oss-batch-processor
├── Core (Required)
│   ├── requests (Ollama API)
│   └── PyYAML (Config files)
├── GUI (Required for oss-GUI.py)
│   ├── Flask (Web framework)
│   └── Flask-CORS (Cross-origin)
├── CLI Enhancements (Optional)
│   ├── colorlog (Colored logs)
│   ├── schedule (Task scheduling)
│   └── watchdog (Folder watching)
└── Plugins (Optional)
    ├── Web Search
    │   ├── google-search-results
    │   └── tavily-python
    └── Notifications
        ├── sendgrid
        └── yagmail
```

## 🆘 Troubleshooting

### pip not found
```bash
# Install pip
python -m ensurepip --upgrade
```

### Permission denied
```bash
# Use user installation
pip install --user -r requirements.txt
```

### SSL Certificate errors
```bash
# Upgrade certificates
pip install --upgrade certifi
```

### Conflicting versions
```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 📦 Virtual Environment (Recommended)

Always use a virtual environment to avoid conflicts:

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Unix/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Deactivate when done
deactivate
```

## 🐳 Docker Alternative

If you prefer Docker, here's a simple Dockerfile:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements-minimal.txt .
RUN pip install -r requirements-minimal.txt
COPY oss-GUI.py oss-CLI.py ./
EXPOSE 5000
CMD ["python", "oss-GUI.py"]
```

Build and run:
```bash
docker build -t oss-processor .
docker run -p 5000:5000 oss-processor
```