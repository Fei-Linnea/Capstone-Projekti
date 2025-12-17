# Radiomic Feature Extraction Pipeline - Complete Guide

## Pipeline Overview

This pipeline performs comprehensive radiomics and morphometric analysis of the hippocampus:

### Step 1: HSF Segmentation
- Uses HSF (Hippocampal Segmentation Factory) to segment hippocampal subfields
- Outputs: Full segmentation + cropped hemispheres + separate hemisphere labels (DG, CA1, CA2, CA3, SUB)

### Step 2: Data Processing
- Splits segmentations into individual subfield labels (5 labels each hemisphere)
- Combines all labels into whole-hippocampus masks
- Outputs: 12 label masks per subject-session (5 labels × 2 hemispheres + 2 combined)

### Step 3: Mesh Generation
- Converts segmentation masks to 3D VTK mesh files
- Generates PNG visualizations for each mesh
- Applies smoothing, decimation, and mesh optimization
- Outputs: 12 VTK meshes + 12 PNG previews (for future curvature analysis and reporting)

### Step 4: PyRadiomics Feature Extraction
- Extracts shape-based radiomics features from each label mask
- Features: MeshVolume, SurfaceVolumeRatio
- Outputs: CSV files for each label and combined mask

### Step 5: Curvature Feature Extraction
- Uses 3D meshes from Step 3 for curvature calculations
- Outputs: Mean curvature, Gaussian curvature metrics

### Step 6: Data Aggregation
- Combines radiomics and curvature features
- Merges all hemispheres and labels into per-subject summary rows
- Outputs: Final CSV with all features per subject-session

## Build Instructions

### Step 1: Build Docker Image
```bash
cd /path/to/home/radiomic-feature-extraction-hippocampus-morphometry

docker build -f pipeline/Dockerfile -t hippocampus-pipeline:latest .
```

**Expected output:**
- Image size: ~800MB
- Build time: 5-10 minutes
- Contains: HSF, PyRadiomics, PyVista, Snakemake

### Step 2: Verify Installation
```bash
# Check pipeline is ready
docker run --rm hippocampus-pipeline:latest --version
```

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

### Dry Run (Check Pipeline)
```bash
docker run --rm \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --snakefile /app/pipeline/workflow/Snakefile \
  --cores 4 \
  --dry-run
```

### Full Pipeline Run (All Steps)
```bash
docker run --rm \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --snakefile /app/pipeline/workflow/Snakefile \
  --cores 4
```

### Run Specific Steps Only

**Steps 1-2 (Segmentation + Data Processing):**
```bash
docker run --rm \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --snakefile /app/pipeline/workflow/Snakefile \
  --cores 4 \
  --until split_label combine_labels
```

**Steps 1-3 (Up to Mesh Generation):**
```bash
docker run --rm \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --snakefile /app/pipeline/workflow/Snakefile \
  --cores 4 \
  --until mesh_per_label mesh_combined
```

**Step 4 Only (PyRadiomics Features):**
```bash
docker run --rm \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --snakefile /app/pipeline/workflow/Snakefile \
  --cores 4 \
  --until extract_pyradiomics_per_label extract_pyradiomics_combined
```

### Interactive Shell (Debugging)
```bash
docker run --rm -it \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  bash
```

## Output Structure

### Directory Layout
```
dataset/
├── derivatives/
│   ├── sub-01/
│   │   └── ses-1/
│   │       ├── anat/                    # Step 1-2: Segmentations & masks
│   │       │   ├── *_space-T1w_desc-hsf_dseg.nii.gz
│   │       │   ├── *_space-T1w_desc-hsf_hemi-L_seg_crop.nii.gz
│   │       │   ├── *_space-T1w_desc-hsf_hemi-R_seg_crop.nii.gz
│   │       │   ├── *_space-T1w_desc-hsf_hemi-{L|R}_label-{DG|CA1|CA2|CA3|SUB}_mask.nii.gz
│   │       │   └── *_space-T1w_desc-hsf_hemi-{L|R}_mask.nii.gz
│   │       ├── meshes/                  # Step 3: 3D mesh files
│   │       │   ├── *_space-T1w_desc-hsf_hemi-{L|R}_label-{DG|CA1|CA2|CA3|SUB}_mesh.vtk
│   │       │   ├── *_space-T1w_desc-hsf_hemi-{L|R}_label-{DG|CA1|CA2|CA3|SUB}_mesh.png
│   │       │   ├── *_space-T1w_desc-hsf_hemi-{L|R}_combined_mesh.vtk
│   │       │   └── *_space-T1w_desc-hsf_hemi-{L|R}_combined_mesh.png
│   │       └── features/                # Step 4-6: Extracted features
│   │           ├── *_hemi-{L|R}_label-{DG|CA1|CA2|CA3|SUB}_pyradiomics.csv
│   │           ├── *_hemi-{L|R}_combined_pyradiomics.csv
│   │           └── *_all_features.csv
│   ├── sub-02/
│   │   └── ... (same structure)
│   └── summary/
│       └── all_features.csv             # Aggregated features for all subjects
└── logs/
    ├── hsf/                             # Step 1 logs
    ├── data_processing/                 # Step 2 logs
    ├── mesh/                            # Step 3 logs
    └── feature_extraction/              # Step 4-6 logs
```

### Output Files Explained

**Segmentations (Step 1):**
- `*_dseg.nii.gz`: Full HSF segmentation
- `*_hemi-{L|R}_seg_crop.nii.gz`: Cropped hemisphere-specific segmentation

**Masks (Step 2):**
- `*_label-{DG|CA1|CA2|CA3|SUB}_mask.nii.gz`: Binary mask for each subfield
- `*_mask.nii.gz`: Combined whole-hippocampus mask

**Meshes (Step 3):**
- `.vtk`: 3D polygon mesh (for curvature analysis)
- `.png`: 2D rendering for visual inspection

**Features (Step 4-6):**
- CSV files with MeshVolume, SurfaceVolumeRatio per region
- `all_features.csv`: Final aggregated summary (one row per subject-session)

## Configuration Options

Edit `pipeline/config/config.yaml` to customize:

### Paths
```yaml
bids_root: "/data"                    # Input dataset location
derivatives_root: "/data/derivatives/"  # Output location
```

### HSF Segmentation (Step 1)
```yaml
hsf_params:
  contrast: "t1"                      # MRI contrast type
  margin: "[8,8,8]"                   # ROI localization margin (voxels)
  segmentation_mode: "single_fast"    # Options: single_fast, single_accurate, bagging_fast, bagging_accurate
  ca_mode: "1/2/3"                    # CA subfield mode: "", "123", "1/23", or "1/2/3"
```

### Mesh Generation (Step 3)
```yaml
mesh_params:
  min_voxel_count: 20                 # Minimum component size for small object removal
  smooth_iters: 50                    # Number of smoothing iterations
  decimation_degree: 0.7              # Mesh decimation ratio (0-1)
```

### Hemisphere and Labels
```yaml
hemis: ["L", "R"]
labels:
  DG: 1
  CA1: 2
  CA2: 3
  CA3: 4
  SUB: 5
```

## Useful Commands

### Dry Run (See What Will Execute)
```bash
docker run --rm \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --snakefile /app/pipeline/workflow/Snakefile \
  --cores 4 \
  --dry-run
```

### Generate DAG Visualization
```bash
docker run --rm \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  -v "${PWD}:/out" \
  hippocampus-pipeline:latest \
  --snakefile /app/pipeline/workflow/Snakefile \
  --dag | grep -v "^Building" > /out/dag.dot

# Convert to PNG
dot -Tpng dag.dot > dag.png
```

### Generate Snakemake Report (NOT YET READY !!)
```bash
docker run --rm \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  -v "${PWD}:/out" \
  hippocampus-pipeline:latest \
  --snakefile /app/pipeline/workflow/Snakefile \
  --report /out/pipeline_report.html \
  --cores 1
```

### Clean Up Results (Careful!)
```bash
docker run --rm \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --snakefile /app/pipeline/workflow/Snakefile \
  --delete-all-output
```


## Troubleshooting

### No subjects found
- Check BIDS structure: `sub-*/ses-*/anat/*_T1w.nii.gz`
- Verify dataset is mounted at `/data`
- Run dry-run to see discovered subjects

### Mesh generation fails with graphics errors
- These are expected warnings; mesh files (.vtk and .png) are still generated
- OSMesa (software rendering) is being used as fallback

### Permission issues on Linux
```bash
docker run --rm \
  --user $(id -u):$(id -g) \
  -v "${PWD}/SampleDataset:/data" \
  hippocampus-pipeline:latest \
  --snakefile /app/pipeline/workflow/Snakefile \
  --cores 4
```

### Check discovered subjects
```bash
docker run --rm \
  -v "${PWD}/SampleDataset:/data" \
  hippocampus-pipeline:latest \
  --snakefile /app/pipeline/workflow/Snakefile \
  --dry-run 2>&1 | grep "sub-"
```

## Performance Notes

- **Build time**: 5-10 minutes (first time only)
- **Per-subject processing**:
  - Step 1 (Segmentation): ~5-10 minutes
  - Step 2 (Data Processing): ~1 minute
  - Step 3 (Mesh Generation): ~1-2 minutes
  - Step 4 (Features): ~2-3 minutes
  - **Total per subject: ~10-20 minutes**
- **Docker image size**: ~800MB
- **Memory usage**: ~3-4GB per parallel job

## Next Steps

### Future Enhancements
- Step 5: Curvature feature extraction from meshes
- HTML mesh visualization embedding in Snakemake reports
- Statistical analysis templates for radiomics features
- Integration with statistical computing frameworks (R/Python)

### Output Analysis
The final `all_features.csv` contains:
- Subject and session identifiers
- Radiomics features (MeshVolume, SurfaceVolumeRatio) per region/hemisphere
- All 12 label combinations per subject

Use standard data analysis tools (pandas, R, SPSS) to analyze correlations, group comparisons, etc.
