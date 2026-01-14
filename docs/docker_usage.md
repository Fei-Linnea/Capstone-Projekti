# Docker Usage Guide - Hippocampus Radiomics Pipeline

## Overview

This guide shows how to run the hippocampal segmentation and radiomics feature extraction pipeline using Docker with your BIDS-formatted MRI dataset.

The pipeline performs:
1. **HSF Segmentation** - Hippocampal subfield segmentation
2. **Data Processing** - Label splitting and mask generation
3. **Mesh Generation** - 3D mesh creation from segmentations
4. **Feature Extraction** - PyRadiomics and curvature features
5. **Aggregation** - Combined feature summary across all subjects

## Prerequisites

- Docker Desktop installed and running
- BIDS-formatted dataset with T1w images
- At least 8GB RAM allocated to Docker
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
docker build -f pipeline/Dockerfile -t hippocampus-pipeline:latest .
```

Build time: ~5-10 minutes (first time only)

## Run the Pipeline

### **Recommended: Automatic Batch Processing**

The pipeline includes automatic batching to handle large datasets efficiently:

```powershell
docker run --rm `
  --security-opt seccomp=unconfined `
  --memory="8g" `
  -v "D:\Path\To\Your\BIDS_Dataset:/data" `
  -v "${PWD}/logs:/app/logs" `
  hippocampus-pipeline:latest `
  --batch-size 50 `
  --cores 4
```

**Parameters:**
- `--batch-size 50` - Process 50 subjects per batch (adjust based on memory)
- `--cores 4` - Use 4 CPU cores
- `--memory="8g"` - Allocate 8GB RAM to Docker

**What happens:**
- Automatically discovers all subjects in dataset
- Processes them in batches of 50
- Continues to next batch automatically
- Runs final aggregation when complete

### PowerShell Example (Windows)

```powershell
# Full dataset processing with batching
docker run --rm `
  --security-opt seccomp=unconfined `
  --memory="8g" `
  -v "D:\Work\BigBrain\data\Fulldataset:/data" `
  -v "${PWD}/logs:/app/logs" `
  hippocampus-pipeline:latest `
  --batch-size 50 `
  --cores 4
```

### Smaller Batches (Lower Memory)

```powershell
# Process 10 subjects per batch (safer for 8GB RAM)
docker run --rm `
  --security-opt seccomp=unconfined `
  --memory="8g" `
  -v "D:\Work\BigBrain\data\Fulldataset:/data" `
  -v "${PWD}/logs:/app/logs" `
  hippocampus-pipeline:latest `
  --batch-size 10 `
  --cores 4
```

### Process All Subjects at Once (No Batching)

⚠️ Only for small datasets (<50 subjects) or high-memory systems:

```powershell
docker run --rm `
  --security-opt seccomp=unconfined `
  --memory="16g" `
  -v "D:\Work\BigBrain\data\Fulldataset:/data" `
  -v "${PWD}/logs:/app/logs" `
  hippocampus-pipeline:latest `
  --batch-size 0 `
  --cores 8
```

### Resume from Specific Batch

If processing was interrupted, resume from a specific batch:

```powershell
docker run --rm `
  --security-opt seccomp=unconfined `
  --memory="8g" `
  -v "D:\Work\BigBrain\data\Fulldataset:/data" `
  -v "${PWD}/logs:/app/logs" `
  hippocampus-pipeline:latest `
  --batch-size 50 `
  --start-batch 5 `
  --cores 4
```

## Output Structure

Results are saved in your dataset directory under `derivatives/`:

```
dataset/
├── sub-01/
│   └── ses-1/
│       └── anat/
│           └── sub-01_ses-1_T1w.nii.gz
└── derivatives/
    ├── sub-01/
    │   └── ses-1/
    │       ├── anat/                           # Segmentations & masks
    │       │   ├── *_desc-hsf_dseg.nii.gz      # Full segmentation
    │       │   ├── *_hemi-L_seg_crop.nii.gz    # Left hemisphere
    │       │   ├── *_hemi-R_seg_crop.nii.gz    # Right hemisphere
    │       │   ├── *_hemi-{L|R}_label-{DG|CA1|CA2|CA3|SUB}_mask.nii.gz
    │       │   └── *_hemi-{L|R}_mask.nii.gz    # Combined masks
    │       ├── meshes/                          # 3D meshes + visualizations
    │       │   ├── *_label-{DG|CA1|CA2|CA3|SUB}_mesh.vtk
    │       │   ├── *_label-{DG|CA1|CA2|CA3|SUB}_mesh.png
    │       │   ├── *_combined_mesh.vtk
    │       │   └── *_combined_mesh.png
    │       └── features/                        # Extracted features
    │           ├── *_label-{DG|CA1|CA2|CA3|SUB}_pyradiomics.csv
    │           ├── *_combined_pyradiomics.csv
    │           ├── *_label-{DG|CA1|CA2|CA3|SUB}_curvature.csv
    │           ├── *_combined_curvature.csv
    │           └── *_all_features.csv          # Per-subject summary
    └── summary/
        ├── all_features.csv                     # ✅ FINAL OUTPUT
        └── processing_issues.txt                # Quality report
```

**Key Output Files:**
- `derivatives/summary/all_features.csv` - **Main result**: All subjects aggregated
- `derivatives/summary/processing_issues.txt` - Lists subjects with processing issues
- `derivatives/sub-XX/ses-Y/features/*_all_features.csv` - Per-subject features

## Logs

Logs are written to the mounted logs directory:

```
logs/
├── hsf/                      # Segmentation logs
├── data_processing/          # Label splitting logs
├── mesh/                     # Mesh generation logs
└── feature_extraction/       # Feature extraction logs
```

## Useful Commands

### Check Pipeline Help

```powershell
docker run --rm hippocampus-pipeline:latest --help
```

### Dry Run (Preview What Will Execute)

```powershell
docker run --rm `
  -v "D:\Path\To\Data:/data" `
  hippocampus-pipeline:latest `
  --batch-size 10 `
  --cores 4 `
  --skip-aggregation `
  --dry-run
```

### Skip Final Aggregation

If you only want to process batches without final aggregation:

```powershell
docker run --rm `
  --security-opt seccomp=unconfined `
  --memory="8g" `
  -v "D:\Path\To\Data:/data" `
  -v "${PWD}/logs:/app/logs" `
  hippocampus-pipeline:latest `
  --batch-size 50 `
  --cores 4 `
  --skip-aggregation
```

## Troubleshooting

### Out of Memory (Exit Code -9)

If the container crashes with "Exit code -9":
- **Reduce batch size**: Use `--batch-size 10` instead of 50
- **Increase Docker memory**: Allocate 12-16GB in Docker Desktop settings
- **Use fewer cores**: Try `--cores 2`

### No Subjects Found

Check dataset structure and discovery:
```powershell
# The wrapper shows discovered subjects on startup
docker run --rm `
  -v "D:\Path\To\Data:/data" `
  hippocampus-pipeline:latest `
  --batch-size 1 `
  --cores 1
```

Look for: `[INFO] Found XXX subject-session pairs`

### Mesh Generation Warnings

VTK/EGL warnings like "bad X server connection" are **expected and harmless**:
```
vtkXOpenGLRenderWindow: bad X server connection. DISPLAY=
Failed to load EGL! Please install the EGL library...
```

The pipeline uses software rendering (OSMesa) and meshes are generated correctly.

### Empty Masks/Failed Processing

Some subjects may have empty subregion masks (e.g., CA2 too small). This is normal:
- Empty masks are handled gracefully
- Pipeline continues processing
- Issues are logged in `derivatives/summary/processing_issues.txt`

### Permission Issues on Linux

```bash
docker run --rm \
  --user $(id -u):$(id -g) \
  --security-opt seccomp=unconfined \
  --memory="8g" \
  -v "/path/to/data:/data" \
  -v "$(pwd)/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --batch-size 50 \
  --cores 4
```

## Configuration

Edit `pipeline/config/config.yaml` to customize:

### Basic Settings
```yaml
bids_root: "/data"
derivatives_root: "/data/derivatives/"
cores: 4
memory_mb: 8000
```

### HSF Segmentation Parameters
```yaml
hsf_params:
  contrast: "t1"
  margin: "[8,8,8]"
  segmentation_mode: "single_fast"  # or single_accurate
  ca_mode: "1/2/3"                   # Separate CA1/CA2/CA3
```

### Mesh Generation
```yaml
mesh_params:
  min_voxel_count: 20
  smooth_iters: 50
  decimation_degree: 0.7
```

### Batch Processing (Optional)
```yaml
batch_size: 50      # Default batch size (0 = no batching)
batch_number: 0     # Starting batch
```

## Performance Notes

**Timing per subject:**
- Segmentation: ~5-10 minutes
- Data processing: ~1 minute
- Mesh generation: ~1-2 minutes
- Feature extraction: ~2-3 minutes
- **Total: ~10-20 minutes per subject**

**For 300 subjects:**
- Sequential: ~50-100 hours
- With 4 cores + batching: ~12-25 hours

**Recommendations:**
- Use batch size 50 for datasets >100 subjects
- Use batch size 10-25 for 8GB RAM systems
- Allocate 16GB RAM for batch size 100+
