# Multi-stage build for OSS Batch Processor
FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 processor && \
    mkdir -p /app/workspace /app/results /app/logs /app/task_configs && \
    chown -R processor:processor /app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/processor/.local

# Copy application files
COPY --chown=processor:processor *.py ./
COPY --chown=processor:processor *.yaml ./
COPY --chown=processor:processor *.html ./
COPY --chown=processor:processor *.md ./
COPY --chown=processor:processor *.sh ./
COPY --chown=processor:processor task_configs/ ./task_configs/
COPY --chown=processor:processor .env.example ./

# Make entrypoint executable
USER root
RUN chmod +x docker-entrypoint.sh
USER processor

# Create necessary directories
RUN mkdir -p workspace results logs .backups .deleted && \
    chown -R processor:processor .

# Switch to non-root user
USER processor

# Add user's local bin to PATH
ENV PATH=/home/processor/.local/bin:$PATH

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_HOST=http://host.docker.internal:11434

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/api/status || exit 1

# Default command - use entrypoint script
CMD ["./docker-entrypoint.sh"]