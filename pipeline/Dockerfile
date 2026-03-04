FROM python:3.11-slim

# Metadata
LABEL maintainer="BigBrain Team"
LABEL description="Radiomic Feature Extraction Hippocampus Morphometry Pipeline"
LABEL version="1.1.0"

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    bash \
    gcc \
    g++ \
    graphviz \
    python3-dev \
    libxrender1 \
    libosmesa6 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
# First install numpy (required by pyradiomics build)
RUN pip install --no-cache-dir numpy

# Then install remaining packages
# HSF for hippocampal segmentation
# PyTorch CPU version (lighter)
# Snakemake for workflow management
# Pin PuLP to 2.7.0 for compatibility with Snakemake 7.32.4
# SimpleITK, nibabel and pandas for nii_parse.py functions (data_processing part)
# pyradiomics for feature extraction
RUN pip install --no-cache-dir \
    nibabel \
    pandas \
    pulp==2.7.0 \
    pyradiomics \
    pyyaml \
    simpleitk \
    snakemake==7.32.4 \
    onnxruntime \
    hsf \
    scikit-image \
    pyvista \
    pyvista[jupyter] \
    vtk && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Pre-download HSF models to avoid checksum failures during pipeline execution
RUN python3 -c "from hsf import fetch_models; fetch_models('/root/.hsf/models', {'single': {'arunet_4.0.0single_1706895706.onnx': {'url': 'https://huggingface.co/poiretclement/hsf/resolve/main/onnx/arunet_4.0.0single_1706895706.onnx', 'xxh3_64': '04ba080ed7f373c2'}}})" || true
WORKDIR /app

ENV PYTHONPATH="/app"

# Set environment to allow pipeline/executable stack for onnxruntime
ENV LD_PRELOAD=""

# Enable off-screen plotting for PyVista in headless environments
ENV PYVISTA_OFF_SCREEN="true"
ENV VTK_OSMESA_DLL="/usr/lib/libOSMesa.so"

COPY pipeline /app/pipeline

RUN chmod +x /app/pipeline/run_pipeline.py

# Run as module so absolute imports like `pipeline.run_utils` work reliably
ENTRYPOINT ["python3", "-m", "pipeline.run_pipeline"]

CMD ["--help"]
