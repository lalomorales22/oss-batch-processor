# OSS Batch Processor - Troubleshooting Guide

## 🔧 Quick Diagnosis

Run this first to check your setup:
```bash
python test_connection.py
```

## 🐳 Docker Issues

### "Connection refused" to Ollama

**Problem**: Docker can't connect to Ollama on localhost:11434

**Solutions**:

1. **Make sure Ollama is running** on your host machine:
   ```bash
   ollama serve
   ```

2. **Use host.docker.internal** (Mac/Windows):
   ```bash
   # In docker-compose.yml, this should already be set:
   OLLAMA_HOST=http://host.docker.internal:11434
   ```

3. **For Linux**, use the Docker bridge IP:
   ```yaml
   environment:
     - OLLAMA_HOST=http://172.17.0.1:11434
   ```

4. **Test the connection** from inside container:
   ```bash
   docker exec -it oss-processor curl http://host.docker.internal:11434/api/tags
   ```

### Rebuild after fixes:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### "unable to open database file" Error

**Problem**: SQLite can't create/access database in Docker

**Solutions**:

1. **Run the setup script first**:
   ```bash
   ./docker-setup.sh
   ```

2. **Create directories manually**:
   ```bash
   mkdir -p workspace results logs data
   chmod 755 workspace results logs data
   ```

3. **Full reset**:
   ```bash
   docker-compose down
   docker volume rm $(docker volume ls -q)
   ./docker-setup.sh
   docker-compose up --build -d
   ```

## 🔑 API Key Issues

### "No search API key found"

**Problem**: Web search shows mock results

**Solutions**:

1. **Check your .env file exists**:
   ```bash
   ls -la .env
   ```

2. **Copy from example if missing**:
   ```bash
   cp .env.example .env
   ```

3. **Edit .env with real keys** (not the placeholder text):
   ```bash
   # Wrong (placeholder):
   SERPER_API_KEY=your_serper_api_key_here
   
   # Right (actual key):
   SERPER_API_KEY=abc123def456...
   ```

4. **Get free API keys**:
   - Serper: https://serper.dev (2,500/month free)
   - Tavily: https://tavily.com (1,000/month free)

5. **For Docker, restart after .env changes**:
   ```bash
   docker-compose restart
   ```

## 📝 Task Format Issues

### Tasks not processing correctly

**Problem**: Tasks appear complete but no AI responses

**Solution**: Make sure you include the brackets in tasks.txt:

```txt
{search}
Research AI developments in 2025

{create}
Write a blog post about remote work

{process}
format=bullet_points::
Transform this text into clear bullet points

{code}
language=python,filename=analyzer.py::
Create a data analysis script

{chain}
research=true,analyze=true::
Complete workflow with multiple steps
```

**Wrong format** (missing brackets):
```txt
search
Research something...
```

## 🌐 Network Issues

### Can't access GUI from phone

**Problem**: GUI works on localhost but not from other devices

**Solutions**:

1. **Check firewall** (Linux/WSL):
   ```bash
   sudo ufw allow 5001
   ```

2. **For macOS**, allow in System Preferences > Security

3. **Use the correct IP** shown when starting:
   ```bash
   python obp-GUI.py
   # Look for: Network Access: http://192.168.x.x:5001
   ```

4. **Make sure devices are on same WiFi network**

## 🤖 Model Issues

### "Model not found" errors

**Solutions**:

1. **Pull the model**:
   ```bash
   ollama pull gpt-oss:20b
   ```

2. **Or use a different model** in processor_config.yaml:
   ```yaml
   model: llama2  # or another available model
   ```

3. **List available models**:
   ```bash
   ollama list
   ```

## 🗄️ Database Issues

### Tasks not saving / corrupt database

**Solutions**:

1. **Delete and recreate database**:
   ```bash
   rm task_processor.db
   rm universal_processor.db
   python obp-GUI.py  # Will recreate
   ```

2. **Check disk space**:
   ```bash
   df -h .
   ```

## 🔄 Processing Issues

### Tasks stuck in "processing" state

**Solutions**:

1. **Check Ollama logs**:
   ```bash
   # In separate terminal:
   ollama serve --verbose
   ```

2. **Restart processing**:
   - Stop processing in GUI
   - Check tasks are marked as "failed" or "pending"
   - Start processing again

3. **Check for stuck processes**:
   ```bash
   ps aux | grep ollama
   ps aux | grep python
   ```

## 📊 Performance Issues

### Very slow processing

**Expected behavior**: This tool is designed for overnight processing with large models.

**To speed up for testing**:

1. **Use smaller model**:
   ```bash
   ollama pull llama2  # Much faster than gpt-oss:20b
   ```

2. **Adjust temperature** in processor_config.yaml:
   ```yaml
   temperature: 0.1  # Lower = faster, less creative
   ```

3. **Reduce delays**:
   ```yaml
   delay_between_items: 0
   delay_between_steps: 0
   ```

## 🆘 Emergency Reset

### Complete reset (nuclear option)

```bash
# Stop everything
docker-compose down
pkill -f ollama
pkill -f obp-GUI.py

# Clean up files
rm -rf workspace/* results/* logs/*
rm *.db

# Reset Docker
docker system prune -f
docker volume prune -f

# Start fresh
docker-compose up --build -d
```

## 📋 Debug Checklist

Before asking for help, check:

- [ ] Ollama is running (`ollama serve`)
- [ ] Model is available (`ollama list`)
- [ ] .env file exists with real API keys
- [ ] Port 5001 is not in use by another app
- [ ] Tasks.txt format includes {brackets}
- [ ] Docker has access to host network
- [ ] Firewall allows port 5001

## 🛠️ Advanced Debugging

### Enable verbose logging:

```python
# Add to top of obp-GUI.py or obp-CLI.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test individual components:

```bash
# Test Ollama directly
curl http://localhost:11434/api/generate -d '{"model":"gpt-oss:20b","prompt":"Hello"}'

# Test web search
python -c "from obp_CLI import WebSearchPlugin; print(WebSearchPlugin().execute(None, {}))"

# Test file operations
python -c "from file_crud_plugin import EnhancedFileOperationsPlugin; print('Plugin loaded')"
```

## 📞 Getting Help

If none of these solutions work:

1. Run `python test_connection.py` and include output
2. Share the exact error messages from logs
3. Mention your OS (Mac/Windows/Linux)
4. Include your docker-compose.yml if using Docker