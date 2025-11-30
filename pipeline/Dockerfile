# ============================================================================
# Simplified Dockerfile for HSF Segmentation Pipeline
# ============================================================================
# Direct pip installation of HSF - no conda complexity
# ============================================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="BigBrain Team"
LABEL description="HSF hippocampal segmentation pipeline"
LABEL version="2.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    bash \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
# HSF for hippocampal segmentation
# PyTorch CPU version (lighter)
# Snakemake for workflow management
# Pin PuLP to 2.7.0 for compatibility with Snakemake 7.32.4
RUN pip install --no-cache-dir \
    pulp==2.7.0 \
    snakemake==7.32.4 \
    onnxruntime \
    hsf && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Set environment to allow executable stack for onnxruntime
ENV LD_PRELOAD=""

# Set entrypoint to Snakemake
ENTRYPOINT ["snakemake"]

# Default command: show help
CMD ["--help"]
