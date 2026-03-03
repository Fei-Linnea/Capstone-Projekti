
The pipeline uses YAML configuration files to define **parameters, paths, and settings** for
different steps. These files allow the workflow to be flexible and reproducible without
modifying the code itself.

Key purposes:
- Define **subjects, sessions, and input paths**
- Configure **processing parameters** (e.g., smoothing, voxel count)
- Set **feature extraction options** (e.g., PyRadiomics features, curvature metrics)
- Control **logging and output locations**

Pipeline Configuration File
===========================

The pipeline uses a YAML configuration file to define **paths, parameters, and options**
for all processing steps. Editing this file allows users to **customize the workflow**
without modifying the Python or Snakemake code.

Purpose
-------

- Define **dataset locations** (BIDS root, derivatives, logs) inside the container
- Set **HSF segmentation parameters** (contrast, margins, subfield modes)
- Configure **meshes, feature extraction, and labels**
- Specify **hemispheres and label IDs** for downstream processing

Example configuration
---------------------

.. code-block:: yaml

    # Dataset paths
    bids_root: "/data"
    derivatives_root: "/data/derivatives/"
    log_dir: "/app/logs"

    # HSF segmentation parameters
    hsf_params:
      contrast: "t1"
      margin: "[8,8,8]"
      segmentation_mode: "single_fast"
      ca_mode: "1/2/3"        # Separate CA1, CA2, CA3

    # Hemispheres and labels
    hemis: ["L", "R"]
    labels:
      DG: 1       # Dentate Gyrus
      CA1: 2      # Cornu Ammonis 1
      CA2: 3      # Cornu Ammonis 2
      CA3: 4      # Cornu Ammonis 3
      SUB: 5      # Subiculum

    # Mesh generation parameters
    mesh_params:
      min_voxel_count: 20         # Minimum voxels for valid mesh
      smooth_iters: 50            # Smoothing iterations
      decimation_degree: 0.7      # Mesh reduction ratio


During pipeline execution, any errors encountered while processing are logged in the processing issues file. And can be found at '\derivatives\summary\processing_issues.txt'

Usage
-----

- Specify the config file when running Snakemake:

  .. code-block:: bash

      snakemake --configfile config.yaml

- Modify parameters to adjust processing behavior:
  - Add/remove subjects or sessions
  - Change HSF segmentation settings
  - Adjust mesh generation parameters
  - Update label definitions for new datasets

Best Practices
--------------

- Keep the YAML **under version control** to track changes.
- Validate syntax before running:

  .. code-block:: bash

      yamllint config.yaml

- Avoid modifying pipeline scripts directly; use the YAML to control behavior.
- Comment sections clearly to document parameter choices.

Snakemake Profile: TYKS Single-Machine Execution
================================================

This Snakemake profile is configured for running the hippocampus pipeline
on a **single, high-performance machine** with **Apptainer**. It allows
containerized execution without a cluster scheduler (e.g., Slurm or PBS).

Purpose
-------

- Run the pipeline locally using multiple cores and jobs.
- Execute rules **inside the Apptainer container** with proper bindings.
- Provide resource defaults (memory, cores) for reliable execution.
- Allow interrupted jobs to be rerun automatically.

Example configuration
---------------------

.. code-block:: yaml

    # Local execution settings
    jobs: 8
    cores: 16
    keep-going: true
    printshellcmds: true
    rerun-incomplete: true

    # Latency settings for local filesystem
    latency-wait: 5

    # Default resource allocation per job
    default-resources:
      - mem_mb=4000

    # Container settings
    use-conda: false
    use-singularity: false

    # Restart failed jobs once
    restart-times: 1

Usage
-----

- Execute the pipeline **inside the Apptainer container**:

  .. code-block:: bash

      apptainer run \
        --writable-tmpfs \
        --bind /path/to/data:/data \
        --bind ./logs:/app/logs \
        hippocampus-pipeline.sif \
        --cores 16 --batch-size 20

- Adjust the `jobs` and `cores` settings based on your machine's RAM and CPU count.
- The pipeline will continue running other rules if individual rules fail (`keep-going: true`).
- Reruns incomplete or failed jobs automatically (`rerun-incomplete: true` and `restart-times: 1`).

Notes
-----

- Memory management is handled in `run_pipeline.py` via the `--batch-size` parameter.
- No cluster submission is configured; all rules execute **locally**.
- This profile is optimized for the TYKS environment but can be adapted for
  other single-machine systems with Apptainer.


Snakemake Profile: CSC Puhti (SLURM + Apptainer)
=================================================

This Snakemake profile is configured for running the hippocampus pipeline
on **CSC Puhti** using the **SLURM workload manager** and **Apptainer**
for containerized execution.

It enables distributed execution across compute nodes while ensuring
reproducibility through container-based software deployment.


Purpose
-------

- Submit pipeline rules as individual SLURM jobs.
- Execute rules inside an Apptainer container.
- Use shared `/scratch` storage for temporary files.
- Provide default resource allocations (memory, runtime, partition).
- Support large-scale batch processing.


Example configuration
---------------------

.. code-block:: yaml

    # SLURM executor
    executor: slurm

    # Job settings
    jobs: 100
    keep-going: true
    latency-wait: 120
    retries: 1
    printshellcmds: true
    rerun-incomplete: true
    local-cores: 1

    # Default SLURM resources
    default-resources:
      - slurm_account=project_2001988
      - slurm_partition=small
      - mem_mb=8000
      - runtime=120
      - tmpdir='/scratch/project_2001988/tarizw/tmp'

    # Apptainer deployment
    software-deployment-method:
      - apptainer

    # Explicit scratch binding and environment variable
    apptainer-args: "--bind /scratch/project_2001988:/scratch/project_2001988:rw \
                     --env HSF_HOME=/users/$USER/.hsf"


Usage
-----

Run Snakemake using the CSC profile:

.. code-block:: bash

    snakemake --profile config/profiles/csc \
      --config bids_root=/path/to/data \
               derivatives_root=/path/to/output \
               container_image=/path/to/image.sif

Adjust resource parameters (`jobs`, `mem_mb`, `runtime`, and `slurm_partition`)
according to your CSC allocation and dataset size.


Notes
-----

- The `tmpdir` must be located on shared storage (e.g., `/scratch`).
  Using `/tmp` may cause Apptainer mount failures on compute nodes.
- Replace `project_2001988` with your own CSC project ID.
- Each Snakemake rule is submitted as a separate SLURM job.
- Job status can be monitored using:

  .. code-block:: bash

      squeue -u $USER