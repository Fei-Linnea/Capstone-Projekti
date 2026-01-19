# Radiomic Feature Extraction Pipeline - Quick Start Guide

## Prerequisites

- **Apptainer** installed on your system (see [Apptainer installation](https://apptainer.org/docs/admin/main/installation.html))
- BIDS dataset

## Setup

Create an empty logs directory in your project folder:
   ```bash
   mkdir -p logs
   ```

## Download the Pipeline Image

Pull the Apptainer image from Docker Hub:

```bash
apptainer pull hippocampus-pipeline.sif docker://docker.io/tarizw/hippocampus-pipeline:v1.0.0
```

This will download the container image (~4.3 GiB).


## Run the Pipeline

Execute the pipeline with the following command:

```bash
apptainer run --writable-tmpfs \
  --bind {relative or absolute path to BIDS dataset}:/data \
  --bind {path to your logs directory}:/app/logs \
  hippocampus-pipeline.sif \
  --profile config/profiles/tyks \
  --batch-size 10
```

**Example:**
```bash
apptainer run --writable-tmpfs \
  --bind ./DatasetName:/data \
  --bind ./logs:/app/logs \
  hippocampus-pipeline.sif \
  --profile config/profiles/tyks \
  --batch-size 10
```

## Output Structure

After successful execution, your dataset directory will contain:

```
dataset/
├── derivatives/
│   ├── sub-01/
│   │   └── ses-1/
│   │       ├── anat/          # Segmentation outputs
│   │       ├── features/      # Extracted radiomics features
│   │       └── meshes/        # Generated 3D meshes
│   └── sub-02/
│       └── ...
└── summary/
    ├── all_features.csv       # Aggregated features from all subjects
    └── processing_issues.txt   # Any subjects with processing errors
```

Your logs directory will contain timestamped directories with detailed execution logs:

```
└── logs/
    ├── <timestamp>/
      ├── hsf/                         # Step 1 logs
      ├── data_processing/             # Step 2 logs
      ├── mesh/                        # Step 3 logs
      ├── feature_extraction/          # Steps 4-6 logs
      ├── benchmarks/                # Performance metrics
      │   ├── hsf/
      │   ├── data_processing/
      │   ├── mesh/
      │   └── feature_extraction/
      ├── snakemake_batch_001.log
      └── snakemake_aggregation.log
```

---

For comprehensive documentation, see [pipeline_guide.md](pipeline_guide.md).
