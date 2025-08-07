# OSS Batch Processor


**Queue tasks during the day, wake up to completed work.** An overnight AI assistant that processes ANY task using your local LLM while you sleep.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Ollama](https://img.shields.io/badge/ollama-compatible-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

<img width="626" height="866" alt="Screenshot 2025-08-06 at 2 22 36 PM" src="https://github.com/user-attachments/assets/062eeeea-a9b2-44be-8d1b-90943256a85d" />

## 🎉 Latest Updates (v2.3)

- **📱 Enhanced Mobile Access** - Improved network diagnostics and QR codes for phone access
- **✏️ Task Management** - Edit/delete tasks with confirmation dialogs
- **🔧 Processing Fixes** - Auto-stop when complete, proper button states
- **🌐 Network Diagnostics** - Built-in connectivity testing and troubleshooting
- **🎨 Unified Gallery** - Browse both GUI and CLI databases in one interface
- **📊 Database Switching** - Toggle between task databases seamlessly
- **🔍 Web Search Integration** - Serper/Tavily API support for research tasks

## ✨ Features

- **Never times out** - Built for slow models that need hours
- **Two interfaces** - GUI with gallery view, CLI for power users  
- **Phone access** - Queue tasks from anywhere on your network
- **Universal tasks** - Search, create, code, process, chain operations
- **Web search** - Optional Serper/Tavily integration for research
- **File CRUD** - Complete file management system
- **100% local** - Your data never leaves your machine (except optional web search)

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
# Access at http://localhost:5001
# Phone: Use the IP address shown in startup (e.g., http://192.168.0.64:5001)
```

**📱 Phone Access Issues?** Run `python network_test.py` for diagnostics!

> **📱 Your Phone URL:** When you start the GUI, look for "Network Access" in the output (e.g., `http://192.168.0.64:5001`). Use that exact address on your phone's browser.

## 📱 GUI Version (`obp-GUI.py`)

Clean web interface accessible from any device:

- **Add tasks** with enhanced metadata builder
- **Monitor progress** with real-time step tracking
- **View results** with formatted display
- **Browse files** in integrated workspace browser
- **Gallery view** at `/gallery` for visual task browsing with CLI/GUI database switching
- **Download files** individually or as workspace zip
- **Mobile responsive** for phones/tablets

![GUI Features](https://img.shields.io/badge/Design-Minimal%20Black%20%26%20White-000000)

### Enhanced GUI Features
- **Task Management**: Edit/delete tasks with confirmation dialogs
- **Mobile Optimized**: Network diagnostics and QR codes for easy phone access
- **Processing Control**: Auto-stop when complete, real-time status updates
- **Gallery View**: Visual task browser with CLI/GUI database switching
- **File Browser**: Download/upload files with workspace management
- **Progress Tracking**: Real-time step monitoring and metadata building

## 💻 CLI Version (`obp-CLI.py`)

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

### Web Search (Optional but Recommended)

1. **Get API Keys** (free tiers available):
   - Serper: https://serper.dev (2,500 free searches/month)
   - Tavily: https://tavily.com (1,000 free searches/month)

2. **Configure**:
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your key(s)
SERPER_API_KEY=your_serper_key_here
TAVILY_API_KEY=your_tavily_key_here
```

3. **Verify Setup**:
```bash
python setup_environment.py
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

## 📱 Mobile/Network Access

### Phone & Tablet Setup
1. **Start the GUI**: `python obp-GUI.py`
2. **Note the IP**: Look for "Network Access" in startup (e.g., `192.168.0.64:5001`)
3. **Open on Phone**: Navigate to that address in your mobile browser
4. **Bookmark It**: Save for easy access

### Troubleshooting Network Issues
```bash
# Diagnose connectivity problems
python network_test.py

# Common solutions:
# 1. Check WiFi - same network for both devices
# 2. macOS Firewall - System Preferences → Security → Firewall → Allow Python
# 3. Test basic connectivity: ping [ip-address] from phone
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

### Docker (Recommended for production)

#### Using Docker Compose (Easiest)
```bash
# Setup directories and permissions
./docker-setup.sh

# Start the processor
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop the processor
docker-compose down
```

#### Using Docker directly
```bash
# Build the image
docker build -t oss-processor .

# Run with volume mounts for persistence
docker run -d \
  --name oss-processor \
  -p 5001:5001 \
  -v $(pwd)/workspace:/app/workspace \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/.env:/app/.env \
  --add-host host.docker.internal:host-gateway \
  oss-processor
```

**Note**: Make sure Ollama is running on your host machine at `http://localhost:11434`

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

## 🆕 Enhanced Features

### File CRUD Operations
The enhanced file operations plugin supports:
- **Basic**: Create, Read, Update, Delete
- **Advanced**: Search, Copy, Move, Rename
- **Backup**: Automatic backups before destructive operations
- **Search**: Find text across multiple files
- **Directories**: Create/remove directories

Example in tasks:
```
{process}
operation=search,search_text=TODO,pattern=*.py::
Find all TODOs in Python files
```

### Gallery View
Access visual task management at `/gallery`:
- **Database Switching**: Toggle between GUI and CLI task databases
- **Visual Cards**: Task display with filtering, search, and statistics
- **Task Details**: Click any task for full results and processing steps
- **Export/Download**: JSON export and file management

### Web Search Integration
All task types now support web search:
- `search_tasks.yaml` - Primary web search
- `process_tasks.yaml` - Research before processing
- `create_tasks.yaml` - Research for content
- `code_tasks.yaml` - Documentation lookup
- `chain_tasks.yaml` - Multi-step workflows

## 📂 Project Structure
```
oss-batch-processor/
├── obp-GUI.py              # Web interface with gallery
├── obp-CLI.py              # Command line interface
├── file_crud_plugin.py     # Enhanced file operations
├── gallery_template.html   # Gallery view template
├── setup_environment.py    # Setup verification script
├── processor_config.yaml   # Main configuration
├── task_configs/           # Task type definitions
│   ├── search_tasks.yaml
│   ├── create_tasks.yaml
│   ├── process_tasks.yaml
│   ├── code_tasks.yaml
│   └── chain_tasks.yaml
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker orchestration
├── requirements.txt       # Python dependencies
├── .env.example          # API key template
├── tasks.txt             # Example tasks
├── tasks.md              # Task documentation
├── IMPROVEMENTS.md       # Recent improvements
├── workspace/            # File operations directory
├── results/              # Task output files
├── data/                 # Database directory
│   ├── task_processor.db    # GUI tasks database
│   └── universal_processor.db # CLI tasks database  
└── logs/                 # Application logs
```

## 🐛 Troubleshooting

**Quick Fixes:**
```bash
python test_connection.py    # Test Ollama connection
python network_test.py       # Test mobile access
./docker-setup.sh           # Fix Docker permissions
```

**Common Issues:**
- **Mobile Access**: Use IP from startup message, check firewall settings
- **Ollama**: Ensure `ollama serve` is running on port 11434
- **Processing Stuck**: Button auto-resets when queue is empty
- **API Keys**: Verify `.env` has real keys (not placeholders)

For detailed help: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | [REQUIREMENTS_GUIDE.md](REQUIREMENTS_GUIDE.md)

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

## 📝 Changelog

### v2.3.0 - Enhanced Mobile & Task Management (Current)
- ✅ Mobile access improvements with network diagnostics
- ✅ Task editing and deletion with confirmation dialogs
- ✅ Auto-stop processing when queue complete
- ✅ QR code generation for easy phone access (with qrcode library)
- ✅ Unified Gallery with CLI/GUI database switching
- ✅ Enhanced network troubleshooting tools

### v2.1.0 - Enhanced GUI & Docker Fixes
- ✅ Enhanced GUI with file browser and progress tracking
- ✅ Fixed Docker database permissions and Ollama connection
- ✅ Added metadata builder interface in GUI
- ✅ Real-time progress indicators and web search status
- ✅ File download/upload functionality
- ✅ Setup and testing scripts (`docker-setup.sh`, `test_connection.py`)
- ✅ Comprehensive troubleshooting guide
- ✅ Mobile-responsive design improvements

### v2.0.0 - Major Feature Release
- ✅ Web search integration (Serper/Tavily APIs)  
- ✅ Gallery view for visual task browsing
- ✅ Enhanced file CRUD operations (15+ operations)
- ✅ Docker support with compose
- ✅ All task types support web search
- ✅ Export functionality for results

### v1.0.0 - Initial Release
- Basic task processing
- GUI and CLI interfaces
- SQLite database
- YAML configuration
- Ollama integration

## 🙏 Credits

Built for the Ollama community by [@lalomorales22](https://github.com/lalomorales22)

Enhanced with love by the open source community 💜

---

**Remember:** Queue tasks by day, wake up to completed work! 🌙✨

For detailed documentation:
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Recent improvements and features
- [METADATA_GUIDE.md](METADATA_GUIDE.md) - How to use metadata for task configuration
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Complete troubleshooting guide
- [tasks.md](tasks.md) - Complete task documentation
- [REQUIREMENTS_GUIDE.md](REQUIREMENTS_GUIDE.md) - Dependency guide
