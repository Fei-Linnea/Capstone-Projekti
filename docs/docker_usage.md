# Docker Usage Guide - Hippocampus Radiomics Pipeline

## Build the Docker Image

From the project root directory:

```powershell
docker build -f pipeline/Dockerfile -t hippocampus-pipeline:latest .
```

## Run the Pipeline

The pipeline includes automatic batching to handle large datasets efficiently:

```powershell
docker run --rm \
  --security-opt seccomp=unconfined \
  --memory="8g" \
  -v "D:\Path\To\Your\BIDS_Dataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --batch-size 50 \
  --cores 4
```

**Parameters:**
- `--batch-size 50` - Process 50 subjects per batch (adjust based on memory)
- `--cores 4` - Use 4 CPU cores
- `--memory="8g"` - Allocate 8GB RAM to Docker

