# CSC HPC Cluster Pipeline

This guide describes how to run the hippocampus pipeline on CSC Puhti/Mahti using **Snakemake + SLURM + Apptainer**. Each Snakemake rule is submitted as a separate SLURM job that runs inside the container.

## Quick Start

```bash
# 1. SSH to CSC Puhti
ssh yourname@puhti.csc.fi

# 2. Set up project directories (one-time)
PROJECT=project_2001988
mkdir -p /projappl/$PROJECT/containers
mkdir -p /scratch/$PROJECT/hippocampus-pipeline

# 3. Copy or pull the container (one-time)
cd /projappl/$PROJECT/containers
# Option A: Pull from registry
apptainer pull hippocampus-pipeline.sif docker://ghcr.io/bigbrain/hippocampus-pipeline:latest
# Option B: Build from local tarball (if Docker image exported)
# apptainer build hippocampus-pipeline.sif docker-archive://hippocampus-pipeline.tar.gz

# 4. Clone/copy the pipeline code
cd /scratch/$PROJECT/hippocampus-pipeline
git clone <repo-url> .

# 5. Run the pipeline (from login node)
cd pipeline
module load snakemake/7.32.4
snakemake --profile config/profiles/csc \
  --config \
    bids_root=/scratch/$PROJECT/my_study/bids \
    derivatives_root=/scratch/$PROJECT/my_study/derivatives \
    container_image=/projappl/$PROJECT/containers/hippocampus-pipeline.sif

# 6. Monitor jobs
squeue -u $USER
```

That's it! Snakemake will submit each subject/rule as a separate SLURM job.

---

## Detailed Guide

### Key Differences: CSC vs Tyks

| Aspect | Tyks (Single Container) | CSC (Multi-Container) |
|--------|------------------------|----------------------|
| **Environment** | Single machine | HPC cluster (Puhti/Mahti) |
| **Job submission** | Direct Apptainer exec | Slurm job scheduler |
| **Containers** | One large container for all steps | Multiple optimized containers (one per rule) |
| **Configuration** | `run_pipeline.py` wrapper | Snakemake + Slurm profile |
| **Profiles** | Not used | **Essential** (`pipeline/config/profiles/csc/`) |
| **Resource mgmt** | Docker flags | Slurm job parameters |
| **Scalability** | Single machine limits | Distribute jobs across many nodes |
| **Execution** | Sequential batches | Parallel jobs across cluster |

## Architecture: Why Multiple Containers?

For CSC deployment, each pipeline step runs in an optimized container:

```
├── hsf_segmentation.sif       (~500MB) - HSF, ONNX, PyTorch
├── data_processing.sif        (~200MB) - nibabel, pandas, scikit-image
├── mesh_generation.sif        (~300MB) - VTK, PyVista, OSMesa
├── feature_extraction.sif     (~400MB) - PyRadiomics, scipy, pandas
└── aggregation.sif            (~150MB) - pandas only
```

**Advantages:**
1. **Smaller images** - Faster to pull from registry
2. **Reduced memory** - Each job uses only necessary dependencies
3. **Faster startup** - Smaller containers load quicker
4. **Better I/O** - Less overhead on Lustre parallel filesystem
5. **Flexibility** - Update one container without rebuilding all
6. **Parallelization** - Many jobs can run simultaneously on different nodes

## Step 1: Build Individual SIF Containers

First, you need to create separate Dockerfiles for each pipeline step (or modify the existing one).

### Option A: Build Individual Containers from Docker Hub

Build and push separate optimized containers for each pipeline step:

```bash
# Local: Build individual container images
docker build --target hsf_stage -t myusername/hsf-pipeline:latest -f pipeline/Dockerfile.multi .
docker build --target processing_stage -t myusername/processing-pipeline:latest -f pipeline/Dockerfile.multi .
# ... etc for each stage

# Push to registry
docker push myusername/hsf-pipeline:latest
docker push myusername/processing-pipeline:latest
# ... etc
```

**Pros:**
- **Optimized sizes** - Each container contains only dependencies for its specific step
- **Faster pulls** - Smaller images download quicker on each compute node
- **Lower memory footprint** - Jobs consume less memory during execution
- **Reduced I/O** - Less strain on Lustre filesystem when pulling images
- **Targeted updates** - Modify one step's dependencies without rebuilding others

**Cons:**
- **More Dockerfiles** - Must maintain separate build targets or files
- **Complex CI/CD** - More build/push operations to manage
- **Higher registry storage** - Multiple images consume more space
- **More cache management** - Each image needs separate caching on CSC

### Option B: Use Single Dockerfile with a Global Container Directive

Use one container for all rules by setting a **global** `container: "docker://..."` at the top of the Snakefile:

**Pros:**
- **Simple maintenance** - One Dockerfile, one build pipeline
- **Easier updates** - Rebuild/push a single image when dependencies change
- **Simpler caching** - One image URL cached across all rules on CSC
- **Faster development** - No need to split dependencies across build stages
- **Single source of truth** - All dependencies in one place

**Cons:**
- **Large image size** - Contains all dependencies even if unused by some rules
- **Slower pulls** - Larger image takes longer to download on each node
- **Higher memory overhead** - Each job loads unnecessary dependencies
- **Wasteful updates** - Small changes require rebuilding entire image
- **Resource inefficiency** - GPU libraries loaded for CPU-only tasks

### Why Container Directives Are Required on CSC

On CSC you need the container directive because Snakemake itself is the “dispatcher,” submitting many jobs to Slurm, and each job must know which image to run. The Dockerfile alone only builds an image; it doesn’t tell Snakemake/Slurm which image to pull per rule. The container directive is how Snakemake encodes “use this image for this rule/job” when it schedules work on the cluster.

Why two variants:

- Tyks (single machine): one container, one command. No per-rule container selection needed.
- CSC (cluster): many independent jobs on different nodes. Each job needs an explicit image reference. The container directive is the Snakemake-native way to declare that, so Snakemake can run `apptainer exec …` under Slurm for every rule.

If you want one image for all CSC rules, you can set a global container: "docker://..." at the top of the Snakefile. If you want lighter images per step (HSF vs mesh vs features), you set the directive per rule. Either way, the directive is how Snakemake/Slurm knows which image to run; the Dockerfile by itself doesn’t provide that mapping.

## Step 2: Configure CSC Profile

The `pipeline/config/profiles/csc/` folder is **essential** for CSC deployment. This profile tells Snakemake how to submit jobs to Slurm.

Updated [pipeline/config/profiles/csc/config.yaml](../pipeline/config/profiles/csc/config.yaml):


## Step 3: Update Rules with Resources

Each rule should specify Slurm resources. Example:

```snakemake
rule hsf_segmentation:
    input:
        t1w = lambda wildcards: get_input_path(wildcards.subject, wildcards.session)
    output:
        seg = "...",
        left_crop = "...",
        right_crop = "..."
    container:
        "docker://myusername/hippocampus-pipeline:latest"
    resources:
        account = "project_2001234",
        partition = "gpu",           # HSF can use GPU
        time = "00:30:00",          # 30 minutes for HSF
        mem_mb = 16000,             # 16GB memory
        threads = 4
    script:
        "../scripts/hsf_wrapper.py"
```

## Step 4: Run on CSC Cluster

### Method 1: Direct Snakemake Execution

```bash
# SSH to CSC
ssh username@puhti.csc.fi

# Navigate to project
cd /scratch/project_id/hippocampus-pipeline

# Run with Slurm profile
snakemake \
  --profile pipeline/config/profiles/csc \
  --cores 100 \
  --jobs 20
```

### Method 2: Submit as Batch Job

Create `submit_workflow.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=snakemake_pipeline
#SBATCH --account=project_2001234
#SBATCH --partition=serial
#SBATCH --time=72:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --output=logs/snakemake-%j.out
#SBATCH --error=logs/snakemake-%j.err

cd /scratch/project_id/hippocampus-pipeline

# Load Snakemake module (if available)
module load snakemake

# Or use conda environment with Snakemake installed
source activate snakemake-env

# Run Snakemake with profile
snakemake \
  --profile pipeline/config/profiles/csc \
  --cores 100 \
  --jobs 20 \
  --local-cores 4 \
  --config bids_root=/scratch/project_id/dataset \
              derivatives_root=/scratch/project_id/dataset/derivatives
```

Submit:
```bash
sbatch submit_workflow.sh
```

## Step 5: Slurm Job Flow

When you run the workflow, Snakemake acts as the **master job controller**:

```
┌─────────────────────────────────────────────────────────────────┐
│  Master Snakemake Job (running on login/serial node)            │
│                                                                 │
│  Submits individual jobs to Slurm:                             │
│  ├─ sbatch hsf_segmentation[subject-01]  → Compute node 1      │
│  ├─ sbatch hsf_segmentation[subject-02]  → Compute node 2      │
│  ├─ sbatch hsf_segmentation[subject-03]  → Compute node 3      │
│  │  (Wait for dependencies...)                                  │
│  ├─ sbatch data_processing[subject-01]   → Compute node 1      │
│  ├─ sbatch data_processing[subject-02]   → Compute node 2      │
│  └─ sbatch mesh_generation[subject-01]   → Compute node 3      │
│     (Continues until all jobs complete)                         │
│                                                                 │
│  Each job:                                                      │
│  ├─ Pulls container from registry                              │
│  ├─ Runs Apptainer with rule-specific container                │
│  ├─ Executes step (HSF, mesh gen, feature extraction, etc)     │
│  └─ Writes results to shared scratch filesystem                │
└─────────────────────────────────────────────────────────────────┘
```

## Pipeline Flow with CSC Profile

```
Snakemake Master Process (1 serial job)
    │
    ├─ Rule: hsf_segmentation
    │   ├─ Job 1 (sub-01): sbatch → node-001 (GPU) → runs apptainer
    │   ├─ Job 2 (sub-02): sbatch → node-002 (GPU) → runs apptainer
    │   └─ Job 3 (sub-03): sbatch → node-003 (GPU) → runs apptainer
    │
    ├─ Rule: data_processing (depends on hsf_segmentation)
    │   ├─ Job 4 (sub-01): sbatch → node-004 (CPU) → runs apptainer
    │   ├─ Job 5 (sub-02): sbatch → node-005 (CPU) → runs apptainer
    │   └─ Job 6 (sub-03): sbatch → node-006 (CPU) → runs apptainer
    │
    └─ ... (continues for remaining rules)
```

## Performance Optimization for CSC

### 1. Resource Allocation per Rule

Different rules need different resources:

```snakemake
# HSF segmentation: GPU intensive
rule hsf_segmentation:
    resources:
        partition = "gpu",
        time = "00:30:00",
        mem_mb = 16000,
        threads = 4

# Mesh generation: CPU intensive
rule mesh_per_label:
    resources:
        partition = "serial",
        time = "00:05:00",
        mem_mb = 4000,
        threads = 2

# Feature extraction: Memory intensive
rule extract_pyradiomics_per_label:
    resources:
        partition = "serial",
        time = "00:10:00",
        mem_mb = 8000,
        threads = 1
```

### 2. Parallel Job Configuration

In `config/profiles/csc/config.yaml`:

```yaml
jobs: 100                  # Max 100 parallel jobs total
local-cores: 4            # Master job uses 4 cores
```

This allows up to 100 independent jobs to run simultaneously across the cluster.

### 3. Container Caching

Set cache on scratch (not home directory):

```bash
# In .bash_profile or before running
export APPTAINER_CACHEDIR=/scratch/project_id/$USER/.apptainer
export TMPDIR=/scratch/project_id/$USER/tmp
```

## Advantages of CSC Multi-Container Approach

1. **Scalability**: 1000+ subjects can be processed in parallel
2. **Efficiency**: Only necessary dependencies loaded per job
3. **Flexibility**: Update one container without rebuilding all
4. **Resilience**: Single job failure doesn't stop workflow
5. **Monitoring**: Each job has separate Slurm logs and benchmarks
6. **Cost**: Pay only for compute time actually used per step

## Monitoring & Debugging

### Check Submitted Jobs

```bash
squeue -u $USER | grep snakemake
```

### View Slurm Logs

```bash
# Per-rule logs
ls -la logs/slurm/

# View specific job log
cat logs/slurm/hsf_segmentation-12345.out
```

### Check Snakemake Status

```bash
# Run dry-run to check
snakemake --profile pipeline/config/profiles/csc --dry-run

# Run with detailed progress
snakemake --profile pipeline/config/profiles/csc -v
```

### Troubleshoot Container Issues

```bash
# Pull container manually to cache it
apptainer pull docker://myusername/hippocampus-pipeline:latest

# Test rule in container interactively
apptainer shell docker://myusername/hippocampus-pipeline:latest
```

## Comparison: Tyks vs CSC Execution

### Tyks Command
```bash
apptainer exec \
  --bind="/data:/data,/app/logs:/app/logs" \
  hippocampus-pipeline.sif \
  python3 /app/pipeline/run_pipeline.py --batch-size 50 --cores 4
```

### CSC Command
```bash
snakemake \
  --profile pipeline/config/profiles/csc \
  --cores 100 \
  --jobs 20
```

**Key difference**: Tyks runs everything in one container on one machine. CSC distributes jobs across the cluster and manages them via Slurm.

## References

- [CSC Slurm Documentation](https://docs.csc.fi/computing/running/submitting-jobs/)
- [Snakemake Cluster Execution](https://snakemake.readthedocs.io/en/v7.19.1/executing/cluster.html)
- [Snakemake Container Integration](https://snakemake.readthedocs.io/en/stable/snakefiles/deployment.html#running-jobs-in-containers)
- [Puhti Batch Partitions](https://docs.csc.fi/computing/running/batch-job-partitions/)
- [Apptainer on HPC](https://docs.csc.fi/computing/containers/overview/)
