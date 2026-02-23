# Radiomic Feature Extraction Pipeline - Complete General Guide

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

### 1. Local Execution

For step-by-step run instructions, see [User Guide](user_guide.md).

### 2. CSC Execution

For step-by-step run instructions, see [CSC User Guide](csc_user_guide.md). For more technical detail, see [CSC Cluster Pipeline](csc_cluster_pipeline.md).


**What the pipeline does:**
- Provides different customizable command-line options (flags) to override default values
- Automatically discovers all subjects
- Processes them in batches
- Runs all 6 pipeline steps for each batch
- Aggregates all results at the end
- Produces the final CSV summary file and log information


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
│   │           └── *_all_features.csv   # Per-subject summary
│   ├── sub-02/
│   │   └── ... (same structure)
│   └── summary/
│       ├── all_features.csv             # FINAL OUTPUT: All subjects
│       └── processing_issues.txt        # Quality report
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

**Benchmarks:**
- `logs/<timestamp>/benchmarks/`: Performance metrics for each job
- Tab-delimited files with columns:
  - `s`: Runtime in seconds
  - `h:m:s`: Formatted time (hours:minutes:seconds)
  - `max_rss`: Maximum resident set size (memory)
  - `max_vms`: Maximum virtual memory size
  - `max_uss`, `max_pss`: Memory usage details
  - `io_in`, `io_out`: I/O read/write in MB
  - `mean_load`: Average CPU load
- Use these files to identify bottlenecks and optimize batch sizes

## Configuration Settings

The pipeline uses following default settings (not editable by the users):


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
  segmentation_mode: "single_fast" 
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

## Output Analysis

### Final Dataset

#### Explanations of each feature:

`derivatives/summary/all_features.csv` contains:

**Subject / Session identifiers** These are as they appear in the BIDS format file name

The actual features are divided into regions and hemispheres (Left / Right side of the brain):

**Radiomics features**:
- MeshVolume: Simply the volume (mm^3)
- SurfaceVolumeRatio: The ratio of surface area to volume (mm^2/mm^3 = 1/mm)

**Curvature features**:
- Mean_curvature: average of the two principal curvatures k1 and k2, measures how much the surface bends overall with higher values meaning more and more convex
  - median: median of all sample points (from around the current region)
  - mean: mean of all sample points
  - std: standard deviation of all sample points
  - 25th_percentile: the value below which 25% of all sample points' values fall
  - 75th_percentile the value below which 75% of all sample points' values fall
- Gaussian_curvature: product of the two principal curvatures k1 and k2, determines the intrinsic shape type, if value > 0, shape is dome or bowl like (elliptic), if value < 0, shape is saddle like (hyperbolic)
  - median: see above
  - mean: see above
  - std: see above
  - 25th_percentile: see above
  - 75th_percentile: see above
- k1_curvature: maximum normal curvature at the sample points (most positive bending/least negative bending)
  - median: see above
  - mean: see above
  - std: see above
  - 25th_percentile: see above
  - 75th_percentile: see above

- k2_curvature: minimum normal curvature at the sample points (most negative bending/least positive bending)
  - median: see above
  - mean: see above
  - std: see above
  - 25th_percentile: see above
  - 75th_percentile: see above
    
  **All curvature features' units are 1/mm**

#### How the features are ordered / laid out in the .csv file:

- First two columns are Subject ID and Session ID
- Next come the actual features ordered...
  - first by region (whole hippocampus, DG, SUB, CA1, CA2, CA3)
  - then by hemisphere (Left / Right side of the brain)
  - then by the order of the actual features for that region-hemisphere combination, in the order they are explained above.

- Example (vertical for easier visualization):
  - Hippocampus_L_MeshVolume &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**First region, left hemisphere**
  - Hippocampus_L_SurfaceVolumeRatio
  - Hippocampus_L_Mean_curvature_median
  - Hippocampus_L_Mean_curvature_mean
  - Hippocampus_L_Mean_curvature_std
  - Hippocampus_L_Mean_curvature_25th_percentile
  - Hippocampus_L_Mean_curvature_75th_percentile
  - Hippocampus_L_Gaussian_curvature_median
  - Hippocampus_L_Gaussian_curvature_mean
  - Hippocampus_L_Gaussian_curvature_std
  - Hippocampus_L_Gaussian_curvature_25th_percentile
  - Hippocampus_L_Gaussian_curvature_75th_percentile
  - Hippocampus_L_k1_curvature_median
  - Hippocampus_L_k1_curvature_mean
  - Hippocampus_L_k1_curvature_std
  - Hippocampus_L_k1_curvature_25th_percentile
  - Hippocampus_L_k1_curvature_75th_percentile
  - Hippocampus_L_k2_curvature_median
  - Hippocampus_L_k2_curvature_mean
  - Hippocampus_L_k2_curvature_std
  - Hippocampus_L_k2_curvature_25th_percentile
  - Hippocampus_L_k2_curvature_75th_percentile
  - Hippocampus_R_MeshVolume &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;**First region, right hemisphere**
  - Hippocampus_R_SurfaceVolumeRatio
  - Hippocampus_R_Mean_curvature_median
  - Hippocampus_R_Mean_curvature_mean
  - Hippocampus_R_Mean_curvature_std
  - Hippocampus_R_Mean_curvature_25th_percentile
  - Hippocampus_R_Mean_curvature_75th_percentile
  - Hippocampus_R_Gaussian_curvature_median
  - Hippocampus_R_Gaussian_curvature_mean
  - Hippocampus_R_Gaussian_curvature_std
  - Hippocampus_R_Gaussian_curvature_25th_percentile
  - Hippocampus_R_Gaussian_curvature_75th_percentile
  - Hippocampus_R_k1_curvature_median
  - Hippocampus_R_k1_curvature_mean
  - Hippocampus_R_k1_curvature_std
  - Hippocampus_R_k1_curvature_25th_percentile
  - Hippocampus_R_k1_curvature_75th_percentile
  - Hippocampus_R_k2_curvature_median
  - Hippocampus_R_k2_curvature_mean
  - Hippocampus_R_k2_curvature_std
  - Hippocampus_R_k2_curvature_25th_percentile
  - Hippocampus_R_k2_curvature_75th_percentile
  - DG_L_MeshVolume &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&nbsp;**Second region, left hemisphere**
  - DG_L_SurfaceVolumeRatio
  - DG_L_Mean_curvature_median
  - DG_L_Mean_curvature_mean <br>
      ...and so on

### Analysis Tools

Use standard data analysis tools, for example:
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


## Workflow Visualization

### Rule Graph (dag.svg)

After pipeline completion, a workflow rule graph is automatically generated and saved to:
```
logs/<timestamp>/rulegraph.svg
```

**What it shows:**
- Complete pipeline structure showing all rules and their dependencies
- Visual representation of workflow stages: HSF Segmentation → Data Processing → Mesh Generation → Feature Extraction → Aggregation
- Scalable diagram optimized for large datasets (shows rule relationships, not individual subject jobs)

**Note:** The rule graph generates after aggregation completes, ensuring it represents the entire pipeline execution across all batches.


## Technical Documentation Guide

Add instructions here how to access technical HTML doc.

## References:

- [Snakemake Documentation](https://snakemake.readthedocs.io/en/stable/index.html)
