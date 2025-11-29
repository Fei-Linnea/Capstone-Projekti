# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    snakemake==7.32.4 \
    pandas>=1.5.0 \
    openpyxl>=3.0.0 \
    pulp==2.7.0

# Clone and install Hippodeep
RUN git clone https://github.com/bthyreau/hippodeep_pytorch.git /opt/hippodeep && \
    cd /opt/hippodeep && \
    pip install .

# Copy project files
COPY pipeline/ ./pipeline/
COPY workflow/ ./workflow/

# Set entry point
CMD ["/bin/bash"]