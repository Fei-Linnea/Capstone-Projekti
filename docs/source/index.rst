Hippocampus Radiomic Feature Extraction Pipeline
================================================

Welcome to the official documentation for the **Hippocampus Radiomic Feature Extraction Pipeline**.  
This pipeline is designed to automate robust, reproducible extraction of radiomic and geometric features
from hippocampal MRI data organized in BIDS format.

Whether you are running locally or on an HPC system, this guide will walk you through configuring,
executing, and extending the pipeline.

**Features include:**

-  **HSF segmentation** of hippocampal subregions (DG, CA1, CA2, CA3, SUB)  
-  **Containerized execution** with Apptainer/Singularity  
-  **Batch processing** with Snakemake profiles  
-  **Mesh Generation** 3D meshes from voxel maps
-  **Feature extraction** (PyRadiomics and curvature-based metrics)  
-  **Aggregation of results per subject and across cohorts**  



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules





