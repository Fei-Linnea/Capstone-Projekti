CSC Puhti Pipeline Runner
=========================

Overview
--------

``run_csc.py`` is the CSC-specific entry point for running the hippocampus
radiomic feature extraction pipeline on **Puhti** using **SLURM + Apptainer**.

It provides an interactive and automated interface for configuring and
launching large-scale cluster jobs while maintaining reproducibility.

This script extends the standard pipeline runner by adding:

- Interactive CSC project configuration
- Dynamic Snakemake profile generation
- SLURM integration
- Apptainer environment setup
- Real-time progress tracking
- Automatic prerequisite validation


Command-Line Interface
----------------------

The runner supports both interactive mode and full CLI-driven execution.

Key arguments:

- ``--project``  
  CSC project number (e.g., ``2001988``).  
  If omitted, the script prompts interactively.

- ``--bids-root``  
  Path to the BIDS dataset root (typically on ``/scratch/project_<ID>/...``).

- ``--bids-pattern``  
  Optional glob pattern to locate T1-weighted files.

- ``--sif``  
  Path to the Apptainer ``.sif`` container image.

- ``--partition``  
  SLURM partition (default: ``small``).

- ``--jobs`` (default: ``100``)  
  Maximum concurrent SLURM jobs.

- ``--latency-wait`` (default: ``120``)  
  Seconds to wait for output file availability on shared storage.

- ``--retries`` (default: ``1``)  
  Number of retries per failed job.

- ``--dry-run`` / ``-n``  
  Show planned jobs without executing.

- ``--force``  
  Force re-run of all rules.

- ``--clean``  
  Remove ``.snakemake/`` metadata before execution.

- ``--cleanup``  
  Remove intermediate outputs after successful completion.

- ``--yes`` / ``-y``  
  Skip confirmation prompt before execution.


Workflow
--------

1. **Prerequisite Check**
   
   - Verifies that Snakemake ≥ 8 is available.
   - Attempts ``module load snakemake`` if not found.
   - Aborts if version requirements are not met.

2. **Configuration Gathering**
   
   - Collects settings from CLI flags.
   - Prompts interactively if required values are missing.
   - Determines project-specific paths:
     
     - Scratch storage
     - TMPDIR
     - Container image
     - Derivatives directory

3. **Profile Generation**
   
   - Dynamically writes ``config/profiles/csc/config.yaml``.
   - Sets:
     
     - SLURM executor
     - Account and partition
     - Memory and runtime defaults
     - Apptainer bind mounts
     - Shared ``tmpdir``

4. **Environment Setup**
   
   - Creates project-specific TMPDIR on ``/scratch``.
   - Clears stale ``SINGULARITY_BIND`` / ``APPTAINER_BIND`` variables.
   - Exports required environment variables.

5. **Pipeline Execution**
   
   - Launches Snakemake with:

   .. code-block:: bash

      snakemake --profile config/profiles/csc

   - Logs are written to:

   .. code-block:: text

      derivatives/logs/run_csc_<timestamp>.log

6. **Real-Time Progress Tracking**
   
   - Parses Snakemake output.
   - Displays:
     
     - Completed steps vs total
     - Current rule
     - Current subject
     - SLURM submission count

7. **Summary Reporting**
   
   - Prints:
     
     - Total duration
     - Completed jobs
     - Failed rules (if any)
     - Output location (``summary/all_features.csv``)

   - Returns exit code:
     
     - ``0`` on success
     - ``1`` on failure

8. **Optional Cleanup**
   
   - Removes intermediate files if ``--cleanup`` is specified.
   - Preserves:
     
     - ``summary/all_features.csv``
     - ``summary/processing_issues.txt``


Examples
--------

Interactive execution:

.. code-block:: bash

   python run_csc.py

Full CLI execution:

.. code-block:: bash

   python run_csc.py \
       --project 2001988 \
       --bids-root /scratch/project_2001988/user/Dataset \
       --sif /scratch/project_2001988/user/Containers/hippocampus-pipeline.sif

Dry run:

.. code-block:: bash

   python run_csc.py --project 2001988 --dry-run

Force full re-run:

.. code-block:: bash

   python run_csc.py --project 2001988 --force --clean


Notes
-----

- Designed specifically for CSC Puhti.
- Requires Snakemake ≥ 8.
- Each rule is submitted as an individual SLURM job.
- Shared ``/scratch`` storage is required for ``tmpdir``.
- Automatically binds project scratch space inside the container.
- Logs are stored under the derivatives directory for traceability.
- Fully compatible with containerized execution.