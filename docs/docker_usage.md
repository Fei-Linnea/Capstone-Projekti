# Docker Usage Guide - Hippocampal Segmentation Pipeline

## Overview

This guide shows how to run the hippocampal segmentation pipeline using Docker with your BIDS-formatted MRI dataset.

## Prerequisites

- Docker Desktop installed and running
- BIDS-formatted dataset with T1w images
- Expected structure:
  ```
  dataset/
  ├── sub-01/
  │   └── ses-1/
  │       └── anat/
  │           ├── sub-01_ses-1_T1w.nii.gz
  │           └── sub-01_ses-1_T1w.json
  ├── sub-02/
  │   └── ses-1/
  │       └── anat/
  │           ├── sub-02_ses-1_T1w.nii.gz
  │           └── sub-02_ses-1_T1w.json
  ```

## Build the Docker Image

From the project root directory:

```powershell
docker build -t hippodeep-pipeline -f pipeline/Dockerfile .
```

## Run the Pipeline

### Basic Usage

Mount your BIDS dataset to `/data` inside the container:

```powershell
docker run --rm -it \
  -v "D:\Path\To\Your\BIDS_Dataset:/data" \
  -v "${PWD}:/app" \
  hippodeep-pipeline \
  snakemake --snakefile /app/pipeline/workflow/Snakefile \
    --configfile /app/pipeline/config/config.yaml \
    --use-conda \
    --cores 4
```

**Replace** `D:\Path\To\Your\BIDS_Dataset` with your actual dataset path.

### PowerShell Example (Windows)

```powershell
# Set your dataset path
$DATASET_PATH = "D:\Work\Uni Work\Capstone\Dataset"

# Run pipeline
docker run --rm -it `
  -v "${DATASET_PATH}:/data" `
  -v "${PWD}:/app" `
  hippodeep-pipeline `
  snakemake --snakefile /app/pipeline/workflow/Snakefile `
    --configfile /app/pipeline/config/config.yaml `
    --use-conda `
    --cores 4 `
    --printshellcmds
```

### With Different Cores

```powershell
docker run --rm -it \
  -v "${DATASET_PATH}:/data" \
  -v "${PWD}:/app" \
  hippodeep-pipeline \
  snakemake --snakefile /app/pipeline/workflow/Snakefile \
    --configfile /app/pipeline/config/config.yaml \
    --use-conda \
    --cores 8  # Use 8 cores
```

### Continue on Error (Process All Subjects)

```powershell
docker run --rm -it \
  -v "${DATASET_PATH}:/data" \
  -v "${PWD}:/app" \
  hippodeep-pipeline \
  snakemake --snakefile /app/pipeline/workflow/Snakefile \
    --configfile /app/pipeline/config/config.yaml \
    --use-conda \
    --cores 4 \
    --keep-going  # Continue processing even if some jobs fail
```

## Output Structure

Results will be saved in your dataset directory under `derivatives/hippodeep/`:

```
dataset/
├── sub-01/
│   └── ses-1/
│       └── anat/
│           └── sub-01_ses-1_T1w.nii.gz
├── derivatives/
│   └── hippodeep/
│       ├── sub-01/
│       │   └── ses-1/
│       │       └── anat/
│       │           ├── sub-01_ses-1_space-T1w_label-hippocampusL_mask.nii.gz
│       │           └── sub-01_ses-1_space-T1w_label-hippocampusR_mask.nii.gz
│       ├── sub-02/
│       │   └── ses-1/
│       │       └── anat/
│       │           ├── sub-02_ses-1_space-T1w_label-hippocampusL_mask.nii.gz
│       │           └── sub-02_ses-1_space-T1w_label-hippocampusR_mask.nii.gz
│       └── processing_summary.txt
```

## Logs

Logs are saved in the project directory under `logs/hippodeep/`:

```
logs/
└── hippodeep/
    ├── sub-01_ses-1.log
    ├── sub-02_ses-1.log
    └── ...
```

## Useful Commands

### Dry Run (See What Will Execute)

```powershell
docker run --rm -it \
  -v "${DATASET_PATH}:/data" \
  -v "${PWD}:/app" \
  hippodeep-pipeline \
  snakemake --snakefile /app/pipeline/workflow/Snakefile \
    --configfile /app/pipeline/config/config.yaml \
    --use-conda \
    --cores 4 \
    --dry-run
```

### Generate DAG Visualization

```powershell
docker run --rm -it \
  -v "${DATASET_PATH}:/data" \
  -v "${PWD}:/app" \
  hippodeep-pipeline \
  snakemake --snakefile /app/pipeline/workflow/Snakefile \
    --configfile /app/pipeline/config/config.yaml \
    --dag | dot -Tpng > dag.png
```

### Clean Up Results (Careful!)

```powershell
docker run --rm -it \
  -v "${DATASET_PATH}:/data" \
  -v "${PWD}:/app" \
  hippodeep-pipeline \
  snakemake --snakefile /app/pipeline/workflow/Snakefile \
    --configfile /app/pipeline/config/config.yaml \
    --delete-all-output
```

## Troubleshooting

### Permission Issues

If you encounter permission errors on Linux:

```bash
docker run --rm -it \
  --user $(id -u):$(id -g) \
  -v "${DATASET_PATH}:/data" \
  -v "${PWD}:/app" \
  hippodeep-pipeline \
  snakemake ...
```

### Check Discovered Subjects

To see which subjects were discovered:

```powershell
docker run --rm -it \
  -v "${DATASET_PATH}:/data" \
  -v "${PWD}:/app" \
  hippodeep-pipeline \
  snakemake --snakefile /app/pipeline/workflow/Snakefile \
    --configfile /app/pipeline/config/config.yaml \
    --dry-run
```

Look for the output:
```
[INFO] Discovered X T1w images for processing:
  - sub-01/ses-1
  - sub-02/ses-1
  ...
```

### View Processing Summary

After completion:

```powershell
cat "${DATASET_PATH}\derivatives\hippodeep\processing_summary.txt"
```

## Configuration Options

Edit `pipeline/config/config.yaml` to customize:

- `bids_root`: Input dataset location (default: `/data`)
- `derivatives_root`: Output location (default: `/data/derivatives/hippodeep`)
- `continue_on_error`: Continue on failures (default: `false`)
- `cores`: Number of parallel jobs

## Notes

- First run will take longer as Snakemake creates the conda environment
- Conda environments are cached in `.snakemake/conda/`
- Results are written directly to your mounted dataset directory
- The pipeline automatically discovers all subjects with T1w images
