
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

- Define **dataset locations** (BIDS root, derivatives, logs)
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
      ca_mode: "1/2/3"

    # Hemispheres and labels
    hemis: ["L", "R"]
    labels:
      DG: 1
      CA1: 2
      CA2: 3
      CA3: 4
      SUB: 5

    # Mesh generation parameters
    mesh_params:
      min_voxel_count: 20
      smooth_iters: 50
      decimation_degree: 0.7

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


Snakemake Profile: CSC Cluster Execution (Slurm + Apptainer)
============================================================

This Snakemake profile is designed for running the hippocampus pipeline
on the **CSC HPC cluster** using **Slurm** for job scheduling and
**Apptainer** for containerized execution.

Purpose
-------

- Submit pipeline rules as **Slurm jobs** with per-rule resources.
- Support containerized execution inside Apptainer/Singularity.
- Allow large-scale parallel execution (up to 100 concurrent jobs).
- Continue execution on individual job failures (`keep-going: true`).
- Automatically rerun failed or incomplete jobs (`restart-times: 1`).

Example configuration
---------------------

.. code-block:: yaml

    jobs: 100
    keep-going: true
    latency-wait: 60
    restart-times: 1
    printshellcmds: true

    # Slurm cluster submission
    cluster: >
      sbatch
      -J {rule}
      -A {resources.account}
      -p {resources.partition}
      -t {resources.time}
      -c {threads}
      --mem={resources.mem_mb}
      --output=logs/slurm/%x-%j.out
      --error=logs/slurm/%x-%j.err

    # Default resources
    default-resources:
      mem_mb: 4000
      time: "01:00:00"
      partition: "serial"
      account: "project_2001234"

    # Container settings
    use-conda: false
    use-singularity: true
    apptainer-args: "--bind=/users,/projappl,/scratch"

Usage
-----

- Execute the pipeline on CSC via Slurm:

  .. code-block:: bash

      snakemake --profile csc --cores 16

- The `cluster` command automatically submits each rule to Slurm
  with the specified resources.
- Modify `default-resources` to set fallback memory, time, partition,
  or account if not specified in individual rules.
- Apptainer arguments (`apptainer-args`) bind necessary directories
  for containerized execution on the HPC cluster.

Notes
-----

- Adjust `jobs` and `cores` according to your allocation and
  cluster policies.
- The profile ensures reproducibility and isolation using Apptainer.
- Always monitor `logs/slurm` for per-job outputs and errors.
- Use `latency-wait` to handle filesystem delays typical on HPC systems.
