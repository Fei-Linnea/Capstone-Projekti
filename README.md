# Radiomic Feature Extraction Pipeline - Hippocampus Morphometry

[![Pipeline Status](https://img.shields.io/badge/status-active-success.svg)]()
[![BIDS Compliant](https://img.shields.io/badge/BIDS-compliant-brightgreen.svg)](https://bids.neuroimaging.io/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

Automated pipeline for comprehensive hippocampal subfield segmentation, 3D mesh generation, and radiomics/morphometry feature extraction from T1-weighted MRI images using HSF (Hippocampal Segmentation Factory).

## Features

- 🧠 **Hippocampal Subfield Segmentation** using HSF (Hippocampal Segmentation Factory)
  - Segments 5 hippocampal subfields: DG, CA1, CA2, CA3, SUB
  - Fast and accurate ONNX-based deep learning models
- 📊 **Comprehensive Feature Extraction**
  - PyRadiomics: Shape features (volume, surface area, etc.)
  - Curvature analysis from 3D meshes
  - Per-subfield and combined hemisphere measurements
- 🎯 **3D Mesh Generation** with VTK visualization
- 📦 **BIDS Compliant** input and output structures
- 🐍 **Snakemake** workflow management for reproducible processing
- 🐳 **Docker** containerized for complete reproducibility
- 🔄 **Batch Processing** with automatic subject discovery
- 📊 **Performance Benchmarking** for all pipeline steps
- ✅ **Comprehensive Logging** and error handling
- 📈 **Final Aggregated CSV** with all subjects and features

## Quick Start

### 1. Build Docker Image

```bash
docker build -f pipeline/Dockerfile -t hippocampus-pipeline:latest .
```

### 2. Run Pipeline

```bash
docker run --rm \
  --security-opt seccomp=unconfined \
  --memory="8g" \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --batch-size 20 \
  --cores 4
```

The pipeline will:
- Automatically discover all subjects in your dataset
- Process them in batches
- Extract radiomics and morphometry features
- Generate performance benchmarks
- Create a final aggregated CSV with all subjects

## Input Structure

Your dataset should be BIDS-formatted with T1w images:

```
dataset/
├── sub-01/
│   └── ses-1/
│       └── anat/
│           ├── sub-01_ses-1_T1w.nii.gz
│           ├── sub-01_ses-1_T1w.json
│           ├── sub-01_ses-1_FLAIR.nii.gz
│           └── sub-01_ses-1_FLAIR.json
├── sub-02/
│   └── ses-1/
│       └── anat/
│           └── ...
```

## Output Structure

Segmentation and feature results are saved as BIDS derivatives with this structure:

```
SampleDataset/
├── derivatives/
│   ├── sub-01/
│   │   └── ses-1/
│   │       ├── anat/
│   │       │   ├── *_desc-hsf_dseg.nii.gz          # Full segmentation
│   │       │   ├── *_hemi-L_seg_crop.nii.gz        # Left hemisphere crop
│   │       │   ├── *_hemi-R_seg_crop.nii.gz        # Right hemisphere crop
│   │       │   ├── *_label-DG_mask.nii.gz          # Individual subfield masks
│   │       │   └── *_mask.nii.gz                   # Combined whole-hippocampus mask
│   │       ├── meshes/
│   │       │   ├── *_mesh.vtk                      # 3D polygon meshes
│   │       │   └── *_mesh.png                      # 2D visualizations
│   │       └── features/
│   │           ├── *_pyradiomics.csv               # Shape features
│   │           ├── *_curvature.csv                 # Curvature metrics
│   │           └── *_all_features.csv              # Per-subject summary
│   └── summary/
│       ├── all_features.csv                        # ✅ FINAL DATASET
│       └── processing_issues.txt                   # Quality report
└── logs/
    ├── <timestamp>/
    │   ├── hsf/                                    # Step 1 logs
    │   ├── data_processing/                        # Step 2 logs
    │   ├── mesh/                                   # Step 3 logs
    │   ├── feature_extraction/                     # Steps 4-6 logs
    │   └── benchmarks/                             # Performance metrics
    └── latest/ → <timestamp>/                      # Symlink to latest run
```

## Configuration

Edit `pipeline/config/config.yaml` to customize the pipeline:

```yaml
# Paths
bids_root: "/data"
derivatives_root: "/data/derivatives/"

# Batch processing
batch_size: 50          # Subjects per batch (0 = no batching)
batch_number: 0         # Starting batch

# Computation
cores: 4
memory_mb: 8000

# HSF Segmentation parameters
hsf_params:
  contrast: "t1"
  margin: "[8,8,8]"
  segmentation_mode: "single_fast"  # or single_accurate, bagging_fast, bagging_accurate
  ca_mode: "1/2/3"                  # Separate CA1, CA2, CA3

# Mesh generation
mesh_params:
  min_voxel_count: 20
  smooth_iters: 50
  decimation_degree: 0.7

# Subfield definitions
hemis: ["L", "R"]
labels:
  DG: 1    # Dentate Gyrus
  CA1: 2   # Cornu Ammonis 1
  CA2: 3   # Cornu Ammonis 2
  CA3: 4   # Cornu Ammonis 3
  SUB: 5   # Subiculum
```

## Documentation

- [Local Guide](docs/guide_local.md) & [CSC Guide](docs/guide_csc.md)
- [Pipeline Guide](docs/pipeline_doc.md) - Pipeline architecture and workflow details
- [Planning](docs/planning.md) - Snakemake practices 

## Requirements

- Docker
- BIDS-formatted MRI dataset with T1w images
- **Recommended:** 8GB+ RAM, 4+ CPU cores
- ~10-20 minutes processing time per subject
- ~800MB Docker image size


## Pipeline Overview

The pipeline consists of 6 main steps:

1. **HSF Segmentation** - Deep learning-based hippocampal subfield segmentation
2. **Data Processing** - Split segmentations into individual labels and combined masks
3. **Mesh Generation** - Convert masks to 3D VTK meshes with smoothing/decimation
4. **PyRadiomics Features** - Extract shape-based radiomics features
5. **Curvature Analysis** - Calculate curvature metrics from 3D meshes
6. **Data Aggregation** - Combine all features into final subject-level and group-level CSVs

**Output:** `derivatives/summary/all_features.csv` contains radiomics and morphometry features for all subjects

## Advanced Usage

### Skip aggregation step

```bash
docker run --rm \
  --security-opt seccomp=unconfined \
  --memory="8g" \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --batch-size 20 \
  --cores 4 \
  --skip-aggregation
```

### Increase resources

```bash
docker run --rm \
  --security-opt seccomp=unconfined \
  --memory="16g" \
  -v "${PWD}/SampleDataset:/data" \
  -v "${PWD}/logs:/app/logs" \
  hippocampus-pipeline:latest \
  --batch-size 50 \
  --cores 8
```

## Logging & Benchmarking

- **Logs:** Stored in `logs/<timestamp>/` with per-step subdirectories
- **Benchmarks:** Performance metrics in `logs/<timestamp>/benchmarks/`
  - Runtime (seconds, h:m:s format)
  - Memory usage (resident, virtual, USS, PSS)
  - I/O statistics (read/write in MB)
  - CPU load averages

## Troubleshooting

### Container exits with code 1

Check logs in `logs/<latest>/snakemake_batch_*.log` for error details.

### Out of memory

Reduce `--batch-size` or increase `--memory`:
```bash
docker run --memory="12g" ... --batch-size 10
```

### Empty mask warnings

Some subjects may have subregions too small to segment. This is normal and handled gracefully. Check `derivatives/summary/processing_issues.txt` for details.

### VTK/EGL warnings

These are expected in headless environments. Pipeline uses OSMesa for off-screen rendering and generates meshes correctly.

## Performance Notes

- **Per-subject time:** 10-20 minutes (all 6 steps)
- **300 subjects with 4 cores:** ~60-75 hours
- **Batch processing:** Optimal batch_size = 50 for 8GB RAM

## Citation



## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Authors

- **BigBrain Team / Capstone Group 7**
- University of Turku

## Acknowledgments

- [HSF](https://hsf.readthedocs.io/en/latest/)
- [PyRadiomics](https://pyradiomics.readthedocs.io/en/latest/)
- [Snakemake](https://snakemake.readthedocs.io/en/stable/) 
- [BIDS](https://bids.neuroimaging.io/)

## Project Status

🔧 **Active Development** - Currently in beta with continuous improvements and testing

## License
