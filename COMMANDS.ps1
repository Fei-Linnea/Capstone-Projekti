# ============================================================================
# HSF Pipeline - Quick Commands
# ============================================================================

# Build Docker image
docker build -f pipeline/Dockerfile -t hsf-pipeline:latest .

# Dry run (check what will be processed)
docker run --rm `
  --security-opt seccomp=unconfined `
  -v "D:\Work\Uni Work\Capstone\SampleDataset:/data" `
  -v "${PWD}/pipeline/workflow:/app/workflow" `
  -v "${PWD}/pipeline/config:/app/config" `
  -v "${PWD}/logs:/app/logs" `
  hsf-pipeline:latest `
  --snakefile /app/workflow/Snakefile `
  --cores 4 `
  --dry-run

# Run pipeline (with security option for onnxruntime)
docker run --rm `
  --security-opt seccomp=unconfined `
  -v "D:\Work\Uni Work\Capstone\SampleDataset:/data" `
  -v "${PWD}/pipeline/workflow:/app/workflow" `
  -v "${PWD}/pipeline/config:/app/config" `
  -v "${PWD}/logs:/app/logs" `
  hsf-pipeline:latest `
  --snakefile /app/workflow/Snakefile `
  --cores 4

# Interactive shell (debugging)
docker run --rm -it `
  --security-opt seccomp=unconfined `
  --entrypoint bash `
  -v "D:\Work\Uni Work\Capstone\SampleDataset:/data" `
  -v "${PWD}/pipeline/workflow:/app/workflow" `
  -v "${PWD}/pipeline/config:/app/config" `
  -v "${PWD}/logs:/app/logs" `
  hsf-pipeline:latest

# Verify HSF installation
docker run --rm hsf-pipeline:latest bash -c "python -c 'import hsf; print(hsf.__version__)'"
