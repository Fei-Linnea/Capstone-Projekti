# Pipeline Deployment Strategies: Tyks vs CSC

### TYKS version (tyks_apptainer_conversion.md)

**Single command:**
```bash
apptainer exec --bind="/data:/data" pipeline.sif python3 /app/pipeline/run_pipeline.py --cores 4
```

### CSC version (csc_cluster_pipeline.md)

**Single command:**
```bash
snakemake --profile pipeline/config/profiles/csc --jobs 20
```

---

## Architecture Comparison

### Tyks: Single Container Model
```
┌──────────────────────────────────┐
│  Single Apptainer Container      │
│  ├─ HSF segmentation             │
│  ├─ Data processing              │
│  ├─ Mesh generation              │
│  ├─ PyRadiomics features         │
│  ├─ Curvature extraction         │
│  └─ Aggregation                  │
│                                  │
│  Size: ~800 MB                   │
│  Runs on: 1 machine              │
│  Parallelism: Batch processing   │
└──────────────────────────────────┘

Sequential Batches:
Batch 1 → Batch 2 → Batch 3 → Aggregation
(~30 mins each batch)
```

### CSC: Multi-Container Model
```
┌─────────────────────────────────────────────────┐
│  Snakemake Master Job (Slurm Serial Job)        │
├─────────────────────────────────────────────────┤
│  Submits to Slurm Job Scheduler                 │
│                                                 │
│  ├─ HSF Container (500 MB)                      │
│  │  └─ 50 parallel jobs on GPU nodes            │
│  │                                              │
│  ├─ Data Processing Container (200 MB)         │
│  │  └─ 50 parallel jobs on CPU nodes            │
│  │                                              │
│  ├─ Mesh Container (300 MB)                    │
│  │  └─ 50 parallel jobs on CPU nodes            │
│  │                                              │
│  ├─ PyRadiomics Container (400 MB)             │
│  │  └─ 50 parallel jobs on CPU nodes            │
│  │                                              │
│  └─ Aggregation Container (150 MB)             │
│     └─ 1 final job on login node                │
└─────────────────────────────────────────────────┘

Parallel Processing:
50 subjects × all steps in parallel
(2-3 hours total for 50 subjects)
```

---

## Configuration Comparison

### Tyks Setup
```
pipeline/
├── Dockerfile              # Single multi-stage or universal image
├── run_pipeline.py         # Batch wrapper script
├── run_utils/
│   ├── batchExecutor.py
│   ├── progress.py
│   └── logger.py
└── config/
    ├── config.yaml
    └── profiles/           # ← NOT USED
        ├── csc/
        └── tyks/
```

**profiles/ is unnecessary for Tyks** - You use the batch wrapper instead.

### CSC Setup
```
pipeline/
├── Dockerfile              # One image per step OR universal with container: directive
├── workflow/
│   ├── Snakefile           # References container: directive
│   └── rules/
│       ├── hsf_segmentation.smk      # container: "docker://..."
│       ├── data_processing.smk       # container: "docker://..."
│       ├── mesh_generation.smk       # container: "docker://..."
│       └── feature_extraction.smk    # container: "docker://..."
└── config/
    ├── config.yaml
    └── profiles/           # ← ESSENTIAL FOR CSC
        └── csc/
            └── config.yaml # Slurm job submission config
```

**profiles/ is essential for CSC** - Controls how Snakemake submits jobs to Slurm.

---

## Key Differences

| Feature | Tyks | CSC |
|---------|------|-----|
| **Execution Model** | Sequential batches in one container | Parallel jobs in multiple containers |
| **Job Scheduler** | None (direct execution) | Slurm |
| **Master Process** | `run_pipeline.py` | Snakemake workflow |
| **Container Approach** | One large (~800 MB) | Multiple optimized (150-500 MB each) |
| **Max Parallelism** | cores parameter (4-16) | jobs parameter (50-100+) |
| **Resource Config** | Docker flags (`--memory`, `--cpus`) | Slurm resources in profile |
| **Monitoring** | Python logging to console | Slurm job queue & per-rule logs |
| **Container Pulls** | 1 image per run | Multiple images (cached) |
| **profiles/ Folder** | ❌ Not needed | ✅ **Required** |
| **Scale Test** | <100 subjects | 1000+ subjects |
| **Time for 50 subjects** | ~150 minutes (30 min/batch × 5) | ~180 minutes (parallel + overhead) |

---


---

## Migration Path: Tyks → CSC

If you start with Tyks and later need CSC:

1. **Keep the Dockerfile** - Works for both
2. **Add container: directive to rules**
   ```snakemake
   rule hsf_segmentation:
       container: "docker://myusername/hippocampus-pipeline:latest"
       script: "..."
   ```
3. **Update profiles/csc/config.yaml** with your project ID
4. **Run on CSC** with Snakemake instead of batch wrapper

---
