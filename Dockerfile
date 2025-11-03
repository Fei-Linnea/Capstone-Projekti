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

# Install Python dependencies
RUN pip install --no-cache-dir snakemake pandas openpyxl

# Set entry point
CMD ["/bin/bash"]