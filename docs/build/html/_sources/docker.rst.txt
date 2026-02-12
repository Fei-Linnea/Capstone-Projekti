

This Dockerfile sets up the environment for the
**Radiomic Feature Extraction Hippocampus Morphometry Pipeline**.

It uses Python 3.11 slim base and installs all system
and Python dependencies required to run the pipeline.

Full Dockerfile
---------------

.. literalinclude:: ../../pipeline/Dockerfile
   :language: docker
   :caption: Dockerfile for Radiomic Pipeline

Explanation of Instructions
---------------------------

**Base Image and Metadata**

- `FROM python:3.11-slim`  
  Uses the official slim Python 3.11 image for a lightweight base.

- `LABEL maintainer="BigBrain Team"`  
  `LABEL description="Radiomic Feature Extraction Hippocampus Morphometry Pipeline"`  
  `LABEL version="1.1.0"`  
  Adds metadata to the image.

**System Dependencies**

- `apt-get update && apt-get install -y --no-install-recommends ...`  
  Installs required system packages:
  - `git`, `bash` → basic tools
  - `gcc`, `g++`, `python3-dev` → build tools for Python packages
  - `graphviz` → visualization
  - `libxrender1`, `libosmesa6`, `xvfb` → headless rendering for PyVista
  - `rm -rf /var/lib/apt/lists/*` cleans up to reduce image size

**Python Packages**

- `pip install --no-cache-dir numpy`  
  Installs NumPy first, needed by PyRadiomics.

- Then install all other Python dependencies:
  - `nibabel`, `pandas` → for `.nii` parsing and data handling
  - `pulp==2.7.0` → LP solver pinned for Snakemake compatibility
  - `pyradiomics` → radiomics feature extraction
  - `pyyaml`, `simpleitk` → workflow utilities
  - `snakemake==7.32.4` → workflow management
  - `onnxruntime` → ONNX runtime for model execution
  - `hsf` → hippocampal segmentation framework
  - `scikit-image`, `pyvista`, `vtk` → image processing and visualization
  - `torch` → PyTorch CPU-only version (lightweight)

**Pre-download Models**

- `python3 -c "from hsf import fetch_models; ..."`  
  Pre-fetches HSF ONNX models to avoid checksum errors during execution.  
  `|| true` ensures the Docker build continues even if the download fails.

**Working Directory and Environment Variables**

- `WORKDIR /app` → sets the container working directory
- `ENV LD_PRELOAD=""` → allows ONNX runtime to work in some Linux environments
- `ENV PYVISTA_OFF_SCREEN="true"` → enables headless plotting
- `ENV VTK_OSMESA_DLL="/usr/lib/libOSMesa.so"` → points PyVista to off-screen rendering library

**Pipeline Files**

- `COPY pipeline /app/pipeline` → copies the pipeline scripts into the container
- `RUN chmod +x /app/pipeline/run_pipeline.py` → makes the pipeline script executable

**Entrypoint**

- `ENTRYPOINT ["python3", "/app/pipeline/run_pipeline.py"]`  
  Default command when the container starts.
- `CMD ["--help"]`  
  Default argument to show usage if no parameters are provided.

---

**Usage**

```bash```
docker build -t radiomic-pipeline .
docker run --rm radiomic-pipeline --help
