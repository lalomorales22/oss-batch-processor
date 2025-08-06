# OSS Batch Processor
<img width="948" height="1343" alt="Screenshot 2025-08-06 at 2 22 36 PM" src="https://github.com/user-attachments/assets/062eeeea-a9b2-44be-8d1b-90943256a85d" />

**Queue tasks during the day, wake up to completed work.** An overnight AI assistant that processes ANY task using your local LLM while you sleep.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Ollama](https://img.shields.io/badge/ollama-compatible-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

- **Never times out** - Built for slow models that need hours
- **Two interfaces** - GUI for easy access, CLI for power users  
- **Phone access** - Queue tasks from anywhere on your network
- **Universal tasks** - Search, create, code, process, chain operations
- **100% local** - Your data never leaves your machine

## 🚀 Quick Start

### 1. Install (< 1 minute)
```bash
# Clone repo
git clone https://github.com/lalomorales22/oss-batch-processor
cd oss-batch-processor

# Install uv if you don't have it (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
# Alternative: python -m venv venv && source venv/bin/activate

# Run interactive installer
python install.py
# Choose option 2 (Recommended)
```

### 2. Start Ollama
```bash
# Terminal 1
ollama serve

# Terminal 2 (if you need a model)
ollama pull gpt-oss:20b
```

### 3. Run the GUI
```bash
python obp-GUI.py
# Access at http://localhost:5000
# Phone access at http://[your-ip]:5000
```

That's it! Start adding tasks from your phone or computer.

## 📱 GUI Version (`oss-GUI.py`)

Clean web interface accessible from any device:

- **Add tasks** with simple form interface
- **Monitor progress** with real-time updates
- **View results** directly in browser
- **Mobile responsive** for phones/tablets

![GUI Features](https://img.shields.io/badge/Design-Minimal%20Black%20%26%20White-000000)

## 💻 CLI Version (`oss-CLI.py`)

Power user command-line interface:

```bash
# Add tasks from file
python obp-CLI.py --add-file tasks.txt

# Process overnight
python obp-CLI.py --run

# Start API for remote access
python obp-CLI.py --api
```

## 📝 Task Format

Create a `tasks.txt` file:

```txt
{search}
Research AI safety developments in 2025

{create}
Write a blog post about quantum computing

{code}
language=python::Create a data visualization script

{process}
Make this text more professional: [your text]

{chain}
Research > Analyze > Report::Study renewable energy trends
```

### Task Types
- `{search}` - Web research and reports
- `{create}` - Generate new content
- `{code}` - Write and debug code
- `{process}` - Transform existing content
- `{chain}` - Multi-step workflows

## 🛠️ Advanced Setup

### Configuration
Edit `processor_config.yaml`:
```yaml
model: gpt-oss:20b
temperature: 0.7
delay_between_items: 2
```

### Web Search (Optional)
```bash
# Add to .env file
SERPER_API_KEY=your_key
TAVILY_API_KEY=your_key
```

### Custom Workflows
Create YAML files in `task_configs/`:
```yaml
type: search
steps:
  - name: web_search
    plugin: web_search
  - name: summarize
    prompt: "Summarize: {web_search_result}"
  - name: save
    plugin: file_operations
```

## 📦 Installation Options

### Interactive (Recommended)
```bash
python install.py
```

### Manual
```bash
# Create virtual environment first
uv venv  # Or: python -m venv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Minimal
pip install requests PyYAML Flask Flask-Cors

# Full
pip install -r requirements.txt

# Development
pip install -r requirements-dev.txt
```

### Docker
```bash
docker build -t oss-processor .
docker run -p 5000:5000 oss-processor
```

## 🔧 Commands Reference

### GUI Commands
```bash
python obp-GUI.py           # Start web interface
```

### CLI Commands
```bash
python obp-CLI.py --add-file tasks.txt   # Add tasks
python obp-CLI.py --run                  # Process tasks
python obp-CLI.py --status               # Check queue
python obp-CLI.py --api                  # Start API server
```

### Make Commands (Unix/Mac/Linux)
```bash
make install      # Install dependencies
make run-gui      # Start GUI
make run-cli      # Start CLI
make demo         # Run demo tasks
```

## 📂 Project Structure
```
oss-batch-processor/
├── obp-GUI.py              # Web interface
├── obp-CLI.py              # Command line interface
├── install.py              # Interactive installer
├── requirements.txt        # Dependencies
├── processor_config.yaml   # Configuration
├── task_configs/           # Workflow definitions
├── results/                # Output files
└── task_processor.db       # SQLite database
```

## 🐛 Troubleshooting

**Ollama not running?**
```bash
ollama serve
```

**Can't access from phone?**
- Check firewall: `sudo ufw allow 5000`
- Verify same WiFi network
- Use IP shown when starting GUI

**Processing slow?**
- This is designed for overnight processing
- Use smaller model for testing: `ollama pull llama2`

## 💡 Use Cases

- **Research Assistant** - Gather information and create reports
- **Content Creator** - Generate blog posts, articles, documentation
- **Code Generator** - Build scripts, functions, applications
- **Data Processor** - Analyze and transform text/data
- **Workflow Automation** - Chain multiple operations together

## 📊 Example Workflow

**Evening (5 PM):** Add tasks from phone while commuting
```
{search} Latest AI breakthroughs
{create} Blog post about findings
{code} Python script to track AI papers
```

**Night (11 PM):** Start processing before bed
```bash
python obp-CLI.py --run
```

**Morning (7 AM):** Review completed work over coffee

## 🤝 Contributing

Pull requests welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

```bash
# Setup development environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
make test
make lint
```

## 📄 License

MIT - See [LICENSE](LICENSE)

## 🙏 Credits

Built for the Ollama community by [@lalomorales22](https://github.com/lalomorales22)

---

**Remember:** Queue tasks by day, wake up to completed work! 🌙✨

For detailed documentation, see [REQUIREMENTS_GUIDE.md](REQUIREMENTS_GUIDE.md)
