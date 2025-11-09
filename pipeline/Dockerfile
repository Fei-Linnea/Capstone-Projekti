# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY pipeline/ ./pipeline/
COPY workflow/ ./workflow/

# Install Python dependencies with specific versions
RUN pip install --no-cache-dir \
    snakemake==7.32.4 \
    pandas>=1.5.0 \
    openpyxl>=3.0.0 \
    pulp==2.7.0

# Set entry point
CMD ["/bin/bash"]