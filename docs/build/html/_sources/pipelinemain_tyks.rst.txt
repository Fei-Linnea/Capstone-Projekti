TYKS Pipeline Runner
=========================


Overview
--------

`run_pipeline.py` is the **main entry point** for the hippocampus radiomic feature extraction pipeline. It handles:

- Batch processing of subjects
- Integration with Snakemake profiles (local or HPC)
- Progress tracking and logging
- Post-processing aggregation of features
- Optional cleanup of intermediate files

This script imports utility functions from the `run_utils` package for all internal operations.

Command-Line Interface
----------------------

The runner provides a **rich CLI** for flexible execution. Key arguments:

- **--profile** *(required)*  
  Path to the Snakemake profile configuration (e.g., `config/profiles/tyks/config.yaml`).  
  Supports both profile directories and direct `config.yaml` files.

- **--batch-size** *(default: 10)*  
  Number of subjects to process per batch.

- **--jobs / --cores**  
  Override the maximum number of Snakemake jobs or cores.

- **--set-threads**  
  Override threads for specific rules (e.g., `hsf_segmentation=4`).

- **--set-resources**  
  Override resources per rule (e.g., `hsf_segmentation:mem_mb=16000`).

- **--subjects**  
  Process specific subjects instead of auto-discovering from BIDS data.

- **--dry-run**  
  Show planned execution without running jobs.

- **--cleanup**  
  Remove intermediate files after successful completion, keeping only `all_features.csv`.

- **--pipeline-dir / --log-dir / --data-dir / --bids-pattern**  
  Paths for working directories, logs, data, and BIDS T1w file discovery.

Workflow
--------

1. **Initialization**
   - Parses CLI arguments.
   - Creates a timestamped log directory.
   - Loads the Snakemake profile to determine defaults for jobs, cores, and resources.

2. **Subject Discovery**
   - Uses either the `--subjects` list or auto-discovers subjects from the BIDS dataset directory.
   - Subjects are split into **batches** according to `--batch-size`.

3. **Batch Processing**
   - Calls `run_snakemake_batch()` for each batch.
   - Tracks failed batches for reporting.

4. **Feature Aggregation**
   - Runs `run_aggregation()` after all batches succeed.
   - Aggregates radiomic and curvature features across labels and hemispheres.

5. **Optional Cleanup**
   - Deletes intermediate files if `--cleanup` is specified and the pipeline completes successfully.

6. **Logging & Summary**
   - Prints per-batch progress, errors, and final summary.
   - Exits with non-zero status if any batch or aggregation failed.

Examples
--------

Full command example (run with defaults from profile):

.. code-block:: bash

    apptainer run --writable-tmpfs \
        --bind /path/to/bids:/data \
        --bind /path/to/logs:/app/logs \
        hippocampus-pipeline.sif \
        --profile config/profiles/tyks


Run with custom batch size:

.. code-block:: bash

    apptainer run --writable-tmpfs \
        --bind /path/to/bids:/data \
        --bind /path/to/logs:/app/logs \
        hippocampus-pipeline.sif \
        --profile config/profiles/tyks \
        --batch-size 20


Override cores at runtime:

.. code-block:: bash

    apptainer run --writable-tmpfs \
        --bind /path/to/bids:/data \
        --bind /path/to/logs:/app/logs \
        hippocampus-pipeline.sif \
        --profile config/profiles/tyks \
        --cores 32


Override rule threads for a specific rule:

.. code-block:: bash

    apptainer run --writable-tmpfs \
        --bind /path/to/bids:/data \
        --bind /path/to/logs:/app/logs \
        hippocampus-pipeline.sif \
        --profile config/profiles/tyks \
        --set-threads hsf_segmentation=4


Dry run (preview execution without running jobs):

.. code-block:: bash

    apptainer run --writable-tmpfs \
        --bind /path/to/bids:/data \
        --bind /path/to/logs:/app/logs \
        hippocampus-pipeline.sif \
        --profile config/profiles/tyks \
        --dry-run


Process specific subjects:

.. code-block:: bash

    apptainer run --writable-tmpfs \
        --bind /path/to/bids:/data \
        --bind /path/to/logs:/app/logs \
        hippocampus-pipeline.sif \
        --profile config/profiles/tyks \
        --subjects 01 02 03 04 05


Use a custom BIDS pattern:

.. code-block:: bash

    apptainer run --writable-tmpfs \
        --bind /path/to/bids:/data \
        --bind /path/to/logs:/app/logs \
        hippocampus-pipeline.sif \
        --profile config/profiles/tyks \
        --bids-pattern "sub-*/ses-1/anat/*_T1w.nii.gz"


Complete example with multiple overrides:

.. code-block:: bash

    apptainer run --writable-tmpfs \
        --bind /path/to/bids:/data \
        --bind /path/to/logs:/app/logs \
        hippocampus-pipeline.sif \
        --profile config/profiles/tyks \
        --batch-size 10 \
        --cores 16 \
        --set-threads hsf_segmentation=4

Notes
-----

- The pipeline automatically logs progress to a timestamped directory under `--log-dir`.
- Exit codes:
  - `0` — all batches and aggregation completed successfully
  - `1` — one or more batches or aggregation failed
- Thread and resource overrides allow flexible adaptation to HPC or local environments.
- Designed for reproducible, containerized execution (via Apptainer/Singularity in profiles).

