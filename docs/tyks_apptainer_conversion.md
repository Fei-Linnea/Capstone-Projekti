# Converting Docker Image to Apptainer SIF for CSC/TYKS

This guide explains how to convert the hippocampus pipeline Docker image to Apptainer SIF format for use on CSC supercomputers (Puhti/Mahti) and Tyks systems that only have Apptainer installed.

## Prerequisites

- Docker image built locally: `hippocampus-pipeline:latest`
- Access to CSC supercomputer (Puhti/Mahti) or Tyks system
- Basic familiarity with SSH and command line

## Method 1: Convert on CSC/Tyks (Recommended)

This method pulls the Docker image from a registry and converts it directly on the target system.

### Step 1: Push Docker Image to Registry

First, push your Docker image to Docker Hub or another registry accessible from CSC:

```bash
# Login to Docker Hub (replace with your username)
docker login

# Tag the image
docker tag hippocampus-pipeline:latest <your-dockerhub-username>/hippocampus-pipeline:latest

# Push to registry
docker push <your-dockerhub-username>/hippocampus-pipeline:latest
```

### Step 2: Connect to CSC

```bash
ssh <your-username>@puhti.csc.fi
# or
ssh <your-username>@mahti.csc.fi
```

### Step 3: Set Up Build Environment

```bash
# Set cache directory to avoid filling home quota
export APPTAINER_CACHEDIR=/scratch/<project_id>/$USER/.apptainer

# Set virtual memory limit to hard limit
ulimit -v $(ulimit -Hv)

# Verify TMPDIR points to local disk (should be set automatically)
echo $TMPDIR
```

### Step 4: Convert Docker Image to SIF

```bash
# Pull from Docker Hub and convert to SIF
apptainer build hippocampus-pipeline.sif docker://<your-dockerhub-username>/hippocampus-pipeline:latest
```

**Expected output:**
- Build time: ~5-10 minutes (depends on image size and network)
- Result: `hippocampus-pipeline.sif` file (~800MB)

## Method 2: Save/Load Docker Image (Alternative)

If you cannot push to a public registry, you can save the Docker image locally and transfer it:

### Step 1: Save Docker Image

On your local machine:
```bash
docker save hippocampus-pipeline:latest | gzip > hippocampus-pipeline.tar.gz
```

### Step 2: Transfer to CSC

```bash
# Using scp (replace with your username and project)
scp hippocampus-pipeline.tar.gz <username>@puhti.csc.fi:/scratch/<project_id>/$USER/
```

### Step 3: Convert on CSC

SSH to CSC and run:
```bash
# Set environment
export APPTAINER_CACHEDIR=/scratch/<project_id>/$USER/.apptainer
ulimit -v $(ulimit -Hv)

# Convert from tar archive
apptainer build hippocampus-pipeline.sif docker-archive://hippocampus-pipeline.tar.gz
```

## Running the SIF Container

### Basic Execution

```bash
# Run with batch processing
apptainer exec \
  --bind="/users,/projappl,/scratch" \
  hippocampus-pipeline.sif \
  python3 /app/pipeline/run_pipeline.py --batch-size 50 --cores 4
```

### With Bind Mounts for Data

```bash
# Bind specific directories
apptainer exec \
  --bind="/scratch/<project_id>/dataset:/data" \
  --bind="/scratch/<project_id>/logs:/app/logs" \
  hippocampus-pipeline.sif \
  python3 /app/pipeline/run_pipeline.py --batch-size 50 --cores 4
```

### Interactive Shell for Testing

```bash
apptainer shell \
  --bind="/scratch/<project_id>/dataset:/data,/scratch/<project_id>/logs:/app/logs" \
  hippocampus-pipeline.sif
```

## Example Slurm Job Script

Create a file `run_pipeline.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=hippocampus_pipeline
#SBATCH --account=<project_id>
#SBATCH --partition=small
#SBATCH --time=48:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=logs/slurm-%j.out
#SBATCH --error=logs/slurm-%j.err

# Load any required modules (usually not needed for Apptainer)
# module load apptainer  # If not loaded by default

# Set paths
CONTAINER="/scratch/<project_id>/$USER/hippocampus-pipeline.sif"
DATASET_DIR="/scratch/<project_id>/dataset"
LOGS_DIR="/scratch/<project_id>/logs"

# Create logs directory
mkdir -p $LOGS_DIR

# Run pipeline
apptainer exec \
  --bind="${DATASET_DIR}:/data,${LOGS_DIR}:/app/logs" \
  $CONTAINER \
  python3 /app/pipeline/run_pipeline.py \
    --batch-size 50 \
    --cores $SLURM_CPUS_PER_TASK
```

Submit the job:
```bash
sbatch run_pipeline.sh
```

## Differences from Docker Execution

| Feature | Docker | Apptainer |
|---------|--------|-----------|
| Command prefix | `docker run` | `apptainer exec` |
| Volume mounts | `-v` or `--volume` | `--bind` |
| Memory limit | `--memory="8g"` | Set via Slurm `#SBATCH --mem=8G` |
| CPU cores | `--cpus 4` | Set via Slurm `#SBATCH --cpus-per-task=4` |
| Security opts | `--security-opt seccomp=unconfined` | Not needed (runs as user) |
| Image format | `.tar`, registry | `.sif` file |

## Key Advantages of Apptainer on HPC

1. **Runs as regular user** - No root/sudo required
2. **Integrates with Slurm** - Resource management via job scheduler
3. **Shared filesystem access** - Home, scratch, and project directories automatically available
4. **No daemon** - Simpler architecture, better security
5. **HPC-optimized** - Designed for multi-user compute environments

## Troubleshooting

### Cache fills up home directory

```bash
# Set cache to scratch
export APPTAINER_CACHEDIR=/scratch/<project_id>/$USER/.apptainer

# Clean cache if needed
apptainer cache clean
```

### Virtual memory limit exceeded

```bash
# Increase to hard limit
ulimit -v $(ulimit -Hv)

# Or use interactive job with more memory
sinteractive --cores 4 --mem 16000 --tmp 10 --time 1:00:00
```

### Build fails on login node

Use an interactive job with local disk:
```bash
sinteractive --cores 4 --mem 8000 --tmp 20 --time 2:00:00
apptainer build hippocampus-pipeline.sif docker://username/hippocampus-pipeline:latest
```

### Cannot bind mount directory

Ensure the directory exists and you have permissions:
```bash
ls -la /scratch/<project_id>/dataset
# Create if missing
mkdir -p /scratch/<project_id>/dataset
```

## Performance Tips

1. **Store SIF on scratch** - Faster access than home or project directories
2. **Bind mount only needed dirs** - Reduces overhead
3. **Use local disk for temp files** - $TMPDIR automatically set in jobs
4. **Batch processing** - Optimal batch_size depends on memory (`--mem` in Slurm)

## CSC-Specific Notes

- **Puhti**: General-purpose, good for most workloads
- **Mahti**: Large parallel jobs, more cores per node
- **Disk areas**:
  - `/users/$USER` - Home (10 GB quota)
  - `/scratch/<project_id>` - Scratch (fast, 1 TB+ quota, purged after 180 days)
  - `/projappl/<project_id>` - Project applications (50 GB quota)

Store the SIF file and datasets in `/scratch/<project_id>/` for best performance.

## References

- [CSC Apptainer Documentation](https://docs.csc.fi/computing/containers/overview/)
- [CSC Disk Areas](https://docs.csc.fi/computing/disk/)
- [Puhti User Guide](https://docs.csc.fi/computing/systems-puhti/)
- [Slurm Job Scripts](https://docs.csc.fi/computing/running/creating-job-scripts-puhti/)
