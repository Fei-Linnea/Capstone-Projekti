# Radiomic Feature Extraction Pipeline - Complete Guide

## Pipeline Overview

This pipeline performs comprehensive radiomics and morphometric analysis of hippocampal subfields:

### Step 1: HSF Segmentation
- Uses HSF (Hippocampal Segmentation Factory) to segment hippocampal subfields
- Outputs: Full segmentation + cropped hemispheres (left/right)

### Step 2: Data Processing
- Splits segmentations into individual subfield labels (DG, CA1, CA2, CA3, SUB)
- Combines all labels into whole-hippocampus masks
- Outputs: Binary masks per label and hemisphere

### Step 3: Mesh Generation
- Converts segmentation masks to 3D VTK mesh files
- Generates PNG visualizations for each mesh
- Applies smoothing, decimation, and mesh optimization
- Handles empty/small masks gracefully

### Step 4: PyRadiomics Feature Extraction
- Extracts shape-based radiomics features from each label mask
- Features: MeshVolume, SurfaceVolumeRatio, and more
- Outputs: CSV files for each label and combined mask per hemisphere

### Step 5: Curvature Feature Extraction
- Calculates curvature metrics from 3D meshes
- Features: Mean curvature, Gaussian curvature
- Outputs: CSV files with curvature statistics per label

### Step 6: Data Aggregation
- Combines radiomics and curvature features per subject
- Merges all hemispheres and labels into single-row summary
- Final aggregation combines all subjects into master CSV

## Build Instructions

### Build Docker Image

From the project root directory:

```powershell
docker build -f pipeline/Dockerfile -t hippocampus-pipeline:latest .
```

**Expected output:**
- Image size: ~800MB
- Build time: 5-10 minutes
- Contains: HSF, PyRadiomics, PyVista, VTK, Snakemake, Python wrapper

### Verify Installation

```powershell
docker run --rm hippocampus-pipeline:latest --help
```

You should see the batch processing wrapper help message.

## Run Instructions

### Prerequisites

Ensure your dataset follows BIDS structure:
```
dataset/
  sub-01/
    ses-1/
      anat/
        sub-01_ses-1_T1w.nii.gz
        sub-01_ses-1_T1w.json
  sub-02/
    ses-1/
      anat/
        sub-02_ses-1_T1w.nii.gz
        sub-02_ses-1_T1w.json
```

### Recommended: Automatic Batch Processing

**For large datasets (50+ subjects):**

```powershell
docker run --rm `
  --security-opt seccomp=unconfined `
  --memory="8g" `
  -v "D:\Path\To\Data:/data" `
  -v "${PWD}/logs:/app/logs" `
  hippocampus-pipeline:latest `
  --batch-size 50 `
  --cores 4
```

**What this does:**
- Automatically discovers all subjects
- Processes them in batches of 50
- Runs all 6 pipeline steps for each batch
- Aggregates all results at the end

### Small Dataset (No Batching)

**For datasets <50 subjects:**

```powershell
docker run --rm `
  --security-opt seccomp=unconfined `
  --memory="8g" `
  -v "D:\Path\To\Data:/data" `
  -v "${PWD}/logs:/app/logs" `
  hippocampus-pipeline:latest `
  --batch-size 0 `
  --cores 4
```

### Linux Example

```bash
docker run --rm \
  --security-opt seccomp=unconfined \
  --memory="8g" \
  -v "/path/to/data:/data" \
  -v "$(pwd)/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --batch-size 50 \
  --cores 4
```

## Advanced Options

### Resume from Specific Batch

If processing was interrupted:

```powershell
docker run --rm `
  --security-opt seccomp=unconfined `
  --memory="8g" `
  -v "D:\Path\To\Data:/data" `
  -v "${PWD}/logs:/app/logs" `
  hippocampus-pipeline:latest `
  --batch-size 50 `
  --start-batch 5 `
  --cores 4
```

### Skip Final Aggregation

Process batches only, aggregate manually later:

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

### Adjust Memory and Cores

```powershell
# More memory, more cores
docker run --rm `
  --security-opt seccomp=unconfined `
  --memory="16g" `
  -v "D:\Path\To\Data:/data" `
  -v "${PWD}/logs:/app/logs" `
  hippocampus-pipeline:latest `
  --batch-size 100 `
  --cores 8
```

## Output Structure

### Directory Layout
```
dataset/
├── derivatives/
│   ├── sub-01/
│   │   └── ses-1/
│   │       ├── anat/                    # Step 1-2: Segmentations & masks
│   │       │   ├── *_desc-hsf_dseg.nii.gz
│   │       │   ├── *_hemi-L_seg_crop.nii.gz
│   │       │   ├── *_hemi-R_seg_crop.nii.gz
│   │       │   ├── *_hemi-{L|R}_label-{DG|CA1|CA2|CA3|SUB}_mask.nii.gz
│   │       │   └── *_hemi-{L|R}_mask.nii.gz (combined)
│   │       ├── meshes/                  # Step 3: 3D meshes + visualizations
│   │       │   ├── *_hemi-{L|R}_label-{DG|CA1|CA2|CA3|SUB}_mesh.vtk
│   │       │   ├── *_hemi-{L|R}_label-{DG|CA1|CA2|CA3|SUB}_mesh.png
│   │       │   ├── *_hemi-{L|R}_combined_mesh.vtk
│   │       │   └── *_hemi-{L|R}_combined_mesh.png
│   │       └── features/                # Steps 4-6: Extracted features
│   │           ├── *_hemi-{L|R}_label-{DG|CA1|CA2|CA3|SUB}_pyradiomics.csv
│   │           ├── *_hemi-{L|R}_combined_pyradiomics.csv
│   │           ├── *_hemi-{L|R}_label-{DG|CA1|CA2|CA3|SUB}_curvature.csv
│   │           ├── *_hemi-{L|R}_combined_curvature.csv
│   │           └── *_all_features.csv   # ⭐ Per-subject summary
│   ├── sub-02/
│   │   └── ... (same structure)
│   └── summary/
│       ├── all_features.csv             # ✅ FINAL OUTPUT: All subjects
│       └── processing_issues.txt        # Quality report
└── logs/
    ├── hsf/                             # Step 1 logs
    ├── data_processing/                 # Step 2 logs
    ├── mesh/                            # Step 3 logs
    └── feature_extraction/              # Steps 4-6 logs
```

### Output Files Explained

**Segmentations (Step 1):**
- `*_dseg.nii.gz`: Full HSF segmentation (all subfields labeled)
- `*_hemi-{L|R}_seg_crop.nii.gz`: Hemisphere-specific cropped segmentation

**Masks (Step 2):**
- `*_label-{DG|CA1|CA2|CA3|SUB}_mask.nii.gz`: Binary mask for each subfield
- `*_mask.nii.gz`: Combined whole-hippocampus mask

**Meshes (Step 3):**
- `.vtk`: 3D polygon mesh for curvature analysis
- `.png`: 2D rendering for visual inspection

**Features (Steps 4-6):**
- `*_pyradiomics.csv`: Shape features (volume, surface area, etc.)
- `*_curvature.csv`: Curvature metrics (mean, Gaussian)
- `*_all_features.csv`: Combined per-subject features
- `summary/all_features.csv`: **Final dataset** with all subjects

## Configuration Options

Edit `pipeline/config/config.yaml` to customize:

### Basic Settings
```yaml
bids_root: "/data"
derivatives_root: "/data/derivatives/"
cores: 4
memory_mb: 8000
```

### Batch Processing
```yaml
batch_size: 50      # Subjects per batch (0 = no batching)
batch_number: 0     # Starting batch number
```

### HSF Segmentation
```yaml
hsf_params:
  contrast: "t1"
  margin: "[8,8,8]"
  segmentation_mode: "single_fast"  # or single_accurate, bagging_fast, bagging_accurate
  ca_mode: "1/2/3"                   # Separate CA1, CA2, CA3
```

### Mesh Generation
```yaml
mesh_params:
  min_voxel_count: 20      # Minimum voxels for valid mesh
  smooth_iters: 50         # Smoothing iterations
  decimation_degree: 0.7   # Mesh reduction ratio
```

### Subfield Labels
```yaml
hemis: ["L", "R"]
labels:
  DG: 1    # Dentate Gyrus
  CA1: 2   # Cornu Ammonis 1
  CA2: 3   # Cornu Ammonis 2
  CA3: 4   # Cornu Ammonis 3
  SUB: 5   # Subiculum
```

## Troubleshooting

### Out of Memory (Exit Code -9)

**Symptom:** Container crashes during "Building DAG of jobs..."

**Solution:**
```powershell
# Reduce batch size
--batch-size 10

# Or increase Docker memory
--memory="12g"
```

### No Subjects Found

**Check:**
```powershell
# Wrapper shows discovered subjects
docker run --rm `
  -v "D:\Path\To\Data:/data" `
  hippocampus-pipeline:latest `
  --batch-size 1 `
  --cores 1
```

Look for: `[INFO] Found XXX subject-session pairs`

### Mesh Generation Warnings

VTK/EGL warnings are **expected and harmless**:
```
vtkXOpenGLRenderWindow: bad X server connection
Failed to load EGL! Please install the EGL library...
```

Pipeline uses OSMesa (software rendering). Meshes are generated correctly.

### Empty Masks / Processing Issues

Some subjects may have empty subregion masks (too small to segment). This is normal:
- Empty masks handled gracefully (empty VTK files created)
- Pipeline continues processing other subjects
- Issues logged in `derivatives/summary/processing_issues.txt`

Check the issues report:
```powershell
cat "D:\Path\To\Data\derivatives\summary\processing_issues.txt"
```

### Permission Issues (Linux)

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

## Performance Notes

### Timing per Subject
- Step 1 (Segmentation): ~5-10 minutes
- Step 2 (Data Processing): ~30 seconds
- Step 3 (Mesh Generation): ~1-2 minutes
- Step 4 (PyRadiomics): ~1-2 minutes
- Step 5 (Curvature): ~1 minute
- Step 6 (Aggregation): <10 seconds
- **Total: ~10-20 minutes per subject**

### Large Dataset Example
**300 subjects with 4 cores:**
- Sequential: ~50-100 hours
- With batching (batch_size=50): ~60-75 hours
- Faster processing: Use 8 cores, reduce to ~30-40 hours

### Resource Requirements
- **Docker image:** ~800MB
- **Memory per job:** ~3-4GB
- **Recommended:** 8GB RAM for batch_size=50, 16GB for batch_size=100

## Output Analysis

### Final Dataset

`derivatives/summary/all_features.csv` contains:
- **Subject/Session identifiers**
- **Radiomics features** per region/hemisphere:
  - MeshVolume, SurfaceArea, SurfaceVolumeRatio
  - Shape elongation, flatness, sphericity
- **Curvature features** per region/hemisphere:
  - Mean curvature (average, min, max, std)
  - Gaussian curvature (average, min, max, std)
- **Regions:** DG, CA1, CA2, CA3, SUB (left/right + combined)

### Analysis Tools

Use standard data analysis tools:
- **Python:** pandas, scikit-learn, matplotlib
- **R:** tidyverse, ggplot2, statistical tests
- **SPSS/SAS:** Import CSV directly

### Example Analysis

```python
import pandas as pd

# Load final results
df = pd.read_csv('derivatives/summary/all_features.csv')

# Check for processing issues
issues = pd.read_csv('derivatives/summary/processing_issues.txt', 
                     sep=':', names=['subject', 'issue'])

# Analyze hippocampus volumes
print(df[['Subject', 'L_Hippocampus_MeshVolume', 'R_Hippocampus_MeshVolume']].head())

# Statistical comparisons
from scipy.stats import ttest_ind
left_vol = df['L_Hippocampus_MeshVolume']
right_vol = df['R_Hippocampus_MeshVolume']
ttest_ind(left_vol, right_vol)
```
