# OSS Batch Processor

**Queue tasks during the day, wake up to completed work.** An overnight AI assistant that processes ANY task using your local LLM while you sleep.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Ollama](https://img.shields.io/badge/ollama-compatible-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

<img width="626" height="866" alt="Screenshot 2025-08-06 at 2 22 36 PM" src="https://github.com/user-attachments/assets/062eeeea-a9b2-44be-8d1b-90943256a85d" />




## The Core Concept
The OSS Batch Processor solves a simple but frustrating problem: local AI models are powerful but slow. Instead of waiting for each task to complete, this app lets you queue up multiple tasks throughout your day and then process them all at once while you sleep.

Think of it like a print queue, but for AI tasks. It's designed to never time out, making it perfect for complex jobs that might take hours. You can add tasks from any device on your network—phone, tablet, or laptop—and wake up to the completed work.

## Key Features

- **Never Times Out**: Built from the ground up for slow, local models that need hours to run.
- **Dual Interfaces**: A modern web GUI for easy access and a powerful CLI for automation and power users.
- **Phone & Tablet Access**: Queue tasks from anywhere on your network with a mobile-responsive interface.
- **Universal Task Engine**: Handles a wide variety of tasks:
  - **search**: In-depth research and report generation.
  - **create**: Generate new content like articles, documentation, or creative writing.
  - **process**: Transform existing content—summarize, rephrase, or change its tone.
  - **code**: Generate, debug, or document software code.
  - **chain**: Execute multi-step workflows where the output of one step feeds into the next.
- **Web Search Integration**: Optionally uses Serper or Tavily APIs to incorporate real-time information into any task.
- **Full File Management**: A complete file CRUD (Create, Read, Update, Delete) plugin with over 15 operations for managing your workspace.
- **Visual Gallery**: A beautiful, filterable gallery view at `/gallery` to browse, inspect, and export completed tasks from both GUI and CLI databases.
- **100% Local & Private**: Your data never leaves your machine (unless you enable the optional web search).

## Quick Start Guide

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/lalomorales22/oss-batch-processor
cd oss-batch-processor

# We recommend 'uv' for fast package management
# Install uv if you don't have it:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment and activate it
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run the interactive installer (Recommended)
python install.py
```

The installer will check your dependencies, verify your Ollama connection, and help you get set up.

### 2. Start Ollama

Open a new terminal and ensure your Ollama instance is running.

```bash
# Terminal 1: Start the Ollama server
ollama serve

# Terminal 2: Pull the recommended model if you don't have it
ollama pull gpt-oss:20b
```

### 3. Run the GUI

```bash
# Start the web application
python obp-GUI.py
```

Access the GUI on your computer at http://localhost:5001.

To access from your phone or another device, use the "Network Access" URL shown in the startup message (e.g., http://192.168.0.64:5001).

## How It Works

### Task Queuing & Processing
The system operates on a simple principle: queue now, process later.

1. **Add Tasks**: Throughout the day, you add tasks using either the web GUI or the CLI. You can define the task type and add specific instructions using metadata.

2. **Process Queue**: When you're ready, you start the processor. It works through the queue one task at a time, sending carefully crafted prompts to your local Ollama model.

3. **Get Results**: The system saves the results of each task to an SQLite database and as individual files in the `results/` directory. The process is fault-tolerant; if it crashes, it remembers where it left off.

### Task Format & Metadata

You can provide tasks in a simple text format or through the GUI's metadata builder. Metadata allows you to customize how each task is handled.

**CLI Task Format (tasks.txt):**

```text
{search}
search_query=AI safety 2025::Research the latest developments in AI safety.

{create}
tone=professional,filename=blog_post.md::Write a blog post about quantum computing.

{code}
language=python,filename=analyzer.py::Create a data visualization script using pandas.
```

**Metadata Guide:**

Metadata is a set of key-value pairs that give the AI specific instructions.

- **For Search**: `search_query`, `comparison`, `filename`
- **For Create**: `tone`, `audience`, `format`, `filename`
- **For Code**: `language`, `filename`, `include_docs`, `include_tests`
- **For File Ops**: `operation` (e.g., create, search, list), `pattern`, `search_text`

**Example (Code Task Metadata):**

```json
{
  "language": "python",
  "filename": "data_analyzer.py",
  "include_docs": true,
  "libraries": "pandas,matplotlib"
}
```

## Advanced Setup & Configuration

### Web Search (Optional but Recommended)

To allow tasks to access real-time information, you can connect a web search provider.

**Get a Free API Key:**

- **Serper**: [serper.dev](https://serper.dev) (2,500 free searches/month)
- **Tavily**: [tavily.com](https://tavily.com) (1,000 free searches/month)

**Configure:**

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file and add your key
SERPER_API_KEY=your_serper_key_here
# or TAVILY_API_KEY=your_tavily_key_here
```

The application will automatically use the key if it's present.

### Custom Workflows (YAML)

You can define or modify task processing steps by editing the YAML files in the `task_configs/` directory. This allows you to create highly customized, multi-step workflows.

**Example (search_tasks.yaml):**

```yaml
type: search
steps:
  - name: web_search        # First, run a web search
    plugin: web_search
    optional: true
  - name: summarize          # Then, summarize the results
    prompt: "Summarize these search results in a clear, organized way: {web_search_result}"
  - name: create_report      # Finally, create a detailed report
    prompt: "Create a detailed report based on this summary: {summarize_result}"
  - name: save_report        # And save the file
    plugin: file_operations
    operation: create
    filename_template: "search_{task_id}.md"
```

## Docker Deployment (Recommended for Production)

Docker provides an isolated and consistent environment.

**Run Setup Script:** This script creates necessary directories and sets permissions.

```bash
./docker-setup.sh
```

**Start with Docker Compose:**

```bash
# Build and start the containers in the background
docker-compose up --build -d
```

**Manage:**

- **View logs**: `docker-compose logs -f`
- **Stop**: `docker-compose down`

## Troubleshooting Guide

### 1. Quick Diagnosis

First, run the connection test script to diagnose common issues with your Ollama setup.

```bash
python test_connection.py
```

### 2. Mobile / Network Access Issues

If you can't access the GUI from your phone or another device:

- **Same Network**: Ensure your phone and computer are on the same Wi-Fi network.
- **Correct IP Address**: Use the exact "Network Access" IP address shown in the terminal when you start the app (e.g., `http://192.168.0.64:5001`), not localhost.
- **Firewall**: Your OS firewall might be blocking the connection.
  - **macOS**: Go to System Preferences → Security & Privacy → Firewall and allow incoming connections for "Python".
  - **Linux**: `sudo ufw allow 5001`
- **Run Network Test**: `python network_test.py` provides detailed diagnostics.

### 3. Docker Connection Issues

If the Docker container can't connect to Ollama:

- Ensure Ollama is running on your host machine (`ollama serve`).
- Your `docker-compose.yml` should set `OLLAMA_HOST=http://host.docker.internal:11434`. This is the standard for Mac and Windows. For Linux, you may need to use `http://172.17.0.1:11434`.
- If you see database errors in Docker, run `./docker-setup.sh` again and rebuild with `docker-compose up --build`.

### 4. API Key / Web Search Issues

If web search isn't working:

- Make sure your `.env` file exists and contains your actual API key, not the placeholder text.
- Restart the application (or Docker container) after editing the `.env` file.

## Project Information

### Project Structure

```
oss-batch-processor/
├── obp-GUI.py              # Main Web interface application
├── obp-CLI.py              # Main Command-line interface
├── processor_config.yaml   # Global configuration for the processor
├── task_configs/           # Directory for custom task workflow definitions
├── gallery_template.html   # Template for the /gallery view
├── install.py              # Interactive installer script
├── Dockerfile              # Docker container definition
├── docker-compose.yml      # Docker orchestration file
├── requirements.txt        # Python dependencies
├── .env.example            # Template for API keys
├── workspace/              # Default directory for file operations
├── results/                # Output directory for completed task files
└── data/                   # Contains the SQLite databases
```

## Contributing

Pull requests are welcome! Please see CONTRIBUTING.md for guidelines. To set up a development environment:

```bash
# Install development and testing tools
pip install -r requirements-dev.txt

# Run tests
make test

# Check code formatting
make lint
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.