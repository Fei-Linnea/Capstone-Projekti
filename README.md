# Radiomic Feature Extraction Pipeline - Hippocampus Morphometry

[![Pipeline Status](https://img.shields.io/badge/status-active-success.svg)]()
[![BIDS Compliant](https://img.shields.io/badge/BIDS-compliant-brightgreen.svg)](https://bids.neuroimaging.io/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

This pipeline has been designed to automatically analyze morphometric data about the hippocampus region of the brain from large datasets of MRI images. It transforms raw image data into numeric features that are useful for medical research, such as studying diseases related to the hippocampus and the brain as a whole.

**Key capabilities:** Deep learning–based segmentation, fully automated execution both locally and on the Finnish CSC supercomputing environment, containerized via Apptainer for platform independence, and comprehensive logging for quality control.

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



## Architecture & Workflow Control (2 versions: TYKS/CSC)

The pipeline follows a rule-based workflow using Snakemake, which manages dependencies and parallelization.


**Execution Flow (Threads & Parallelization)**

1. **Entry Points:** 
  - **Local execution**: The user runs the command `apptainer run ...`, specifying dataset and log paths.  
  - **CSC execution**: The user runs `python3 run_csc.py` command.
2. **Job Orchestration:** Snakemake recognizes and distributes subjects into batches, manages jobs, and dispatches jobs to Slurm as containers (CSC environment).  
3. **Job Execution:** Batches are processed one at a time using multiple threads for maximum parallelization. For each subject in a batch, segmentation, feature extraction, and data aggregation are performed.  


## Data Analysis

The pipeline segments and extracts features for 12 different hippocampal regions: Dentate Gyrus (DG), Subiculum (SUB), CA1, CA2, and CA3, as well as all combined — **for each side of the brain separately**.

**Data analysis steps:**

1. **Segmentation:** Uses the Hippocampal Segmentation Factory (HSF) model to segment subfields from raw MRI images.  
2. **Segmentation Processing:** Splits segmentations into masks for individual labels (regions) and creates a combined segmentation mask.  
3. **Mesh Generation:** Converts segmentation masks into 3D mesh `.vtk` files using the marching cubes algorithm.  
4. **Radiomics Feature Extraction:** Extracts radiomics features (e.g., volume, surface area per volume) from segmentation masks using the PyRadiomics library.  
5. **Curvature Feature Extraction:** Calculates multiple curvature metrics from 3D mesh `.vtk` files.  
6. **Data Aggregation:** Collects all radiomics and curvature metrics from all regions into a single-row summary per input image (subject/session) and appends it to the final `.csv` file containing all processed images.  


## Output Structure

The pipeline produces two primary output folders: `derivatives/`, containing results, and `logs/`, containing execution information.

### A. Results (`derivatives/`)

Data relevant to the end user:

- **summary/all_features.csv:** Main table where each subject/session (input image) is one row.  
  - Columns: Patient ID | Session ID | {each calculated metric as its own column}  
- **{subject}/{session}/meshes/:** 3D meshes (`.vtk`) for visual inspection  
- **{subject}/{session}/features/:** All features for a particular subject  

### B. Execution Information (`logs/`)

Information critical for maintenance and detecting abnormalities:

- **Per-step logs:** Stored in `hsf/`, `data_processing/`, `mesh/`, and `feature_extraction/` folders
- **Batch logs:** `snakemake_batch_*.log` — Execution logs for each subject batch processed
- **Aggregation log:** `snakemake_aggregation.log` — Final aggregation step combining all results  
- **Benchmarks:** `benchmarks/` — Performance metrics (CPU, memory, I/O, runtime) per rule and subject  
- **Workflow diagram:** `rulegraph.svg` — Automatically generated Snakemake dependency rule graph showing all pipeline rules and their relationships  


## Customization & Runtime Tuning

The pipeline is fully automated and ready to use with sensible defaults. Users can customize execution via **command-line flags**.

**Pipeline Parameters:** Advanced users can edit `pipeline/config/config.yaml` to adjust e.g. HSF segmentation_mode and margin (of the cropped image), mesh smoothing iterations, and other processing details.


---

## Complete Guides and Documentations

- [Local Guide](docs/source/guides/guide_local.md) & [CSC Guide](docs/source/guides/guide_csc.md) - Step-by-step guides for running the pipeline
- [Pipeline Documentation](docs/source/guides/pipeline_doc.md) - Pipeline architecture and workflow details
- [Pipeline Cluster Implementation](docs/source/guides/pipeline_doc_csc.md) - Pipeline Cluster implementation details



## GitLab Pages

The full Sphinx HTML documentation is published via GitLab Pages.

**How it is built:**
- The Pages job runs on the `main` and `development` branch only.
- It installs dependencies from `requirements.txt`, builds the docs with `make -C docs html`, and publishes `docs/build/html`.

**Where to access it:**
- Direct URL: https://radiomic-feature-extraction-hippocampus-morphometry-cb41a9.utugit.fi/
- You can also open the public project page at https://gitlab.utu.fi/capstone_group_7/radiomic-feature-extraction-hippocampus-morphometry and click the GitLab Pages link.

**Local preview (optional):**
```bash
pip install -r requirements.txt
make -C docs html
```
Then open `docs/build/html/index.html` in a browser.



## Authors

- **BigBrain Team / Capstone Group 7**
- University of Turku

## References

**Core Dependencies:**
- [HSF (Hippocampal Segmentation Factory)](https://hsf.readthedocs.io/en/latest/) — Deep learning segmentation
- [PyRadiomics](https://pyradiomics.readthedocs.io/en/latest/) — Radiomic feature extraction
- [Snakemake](https://snakemake.readthedocs.io/en/stable/) — Workflow orchestration
- [BIDS (Brain Imaging Data Structure)](https://bids.neuroimaging.io/) — Data organization standard

**Supporting Libraries:**
- [Apptainer/Singularity](https://apptainer.org/) — Container runtime
- [Docker](https://www.docker.com/) — Container images
- [ONNX Runtime](https://onnxruntime.ai/) — HSF model inference
- [nibabel](https://nipy.org/nibabel/) — NIfTI file I/O
- [VTK / PyVista](https://www.vtk.org/) — 3D mesh generation and visualization



## License