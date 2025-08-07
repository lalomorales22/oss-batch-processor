#!/bin/bash

echo "🐳 Setting up OSS Batch Processor for Docker..."

# Create necessary directories on host
echo "📁 Creating host directories..."
mkdir -p workspace results logs data

# Set permissions
echo "🔧 Setting permissions..."
chmod 755 workspace results logs data

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found"
    if [ -f .env.example ]; then
        echo "📄 Copying .env.example to .env"
        cp .env.example .env
        echo "✏️  Please edit .env with your API keys before starting!"
    else
        echo "❌ No .env.example found either"
    fi
else
    echo "✅ .env file exists"
fi

# Check if API keys are set
if [ -f .env ]; then
    if grep -q "your_" .env; then
        echo "⚠️  API keys in .env contain placeholder text"
        echo "   Edit .env and replace 'your_key_here' with actual keys"
    else
        echo "✅ .env appears to have real API keys"
    fi
fi

echo ""
echo "🚀 Ready to start! Run:"
echo "   docker-compose up --build -d"
echo ""
echo "🎯 Access at: http://localhost:5001"
echo "🎨 Gallery at: http://localhost:5001/gallery"