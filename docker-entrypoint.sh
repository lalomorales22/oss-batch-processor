#!/bin/bash
set -e

echo "🐳 OSS Batch Processor Docker Container Starting..."

# Check if Ollama is reachable
echo "🔗 Testing connection to Ollama at $OLLAMA_HOST"
for i in {1..5}; do
    if curl -s "$OLLAMA_HOST/api/tags" > /dev/null; then
        echo "✅ Ollama is reachable"
        break
    else
        echo "⏳ Waiting for Ollama... (attempt $i/5)"
        sleep 5
    fi
done

# Show environment info
echo "🔧 Configuration:"
echo "   OLLAMA_HOST: $OLLAMA_HOST"
echo "   API Keys: $(if [ -n "$SERPER_API_KEY" ]; then echo "Serper ✅"; else echo "Serper ❌"; fi) $(if [ -n "$TAVILY_API_KEY" ]; then echo "Tavily ✅"; else echo "Tavily ❌"; fi)"

# Create necessary directories with proper permissions
echo "📁 Setting up directories and permissions..."
mkdir -p workspace results logs .backups .deleted data
touch data/task_processor.db data/universal_processor.db
chmod -R 755 workspace results logs .backups .deleted data

# Test database creation
echo "🗄️  Testing database access..."
python -c "import sqlite3; conn = sqlite3.connect('test.db'); conn.close()" && rm -f test.db
if [ $? -eq 0 ]; then
    echo "✅ Database access working"
else
    echo "❌ Database access failed"
fi

# Start the application
echo "🚀 Starting OSS Batch Processor GUI..."
exec python obp-GUI.py