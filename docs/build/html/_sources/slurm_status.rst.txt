slurm_status.py
===============

SLURM Job Status Checker for Snakemake
--------------------------------------

This script provides a SLURM job status checker designed for use with
Snakemake cluster execution.

Snakemake calls this script with a job ID to determine whether a job is:

- ``running`` — Job is pending, running, or completing
- ``success`` — Job completed successfully
- ``failed`` — Job failed, was cancelled, or timed out


Usage
-----

Configured in a Snakemake profile:

.. code-block:: yaml

   cluster-status: "slurm_status.py"

Command-line usage:

.. code-block:: bash

   slurm_status.py <jobid>


Overview
--------

The script works as follows:

1. Queries SLURM using ``sacct`` (preferred method).
2. If necessary, falls back to ``squeue``.
3. Maps SLURM job states to one of three standardized outputs:
   ``running``, ``success``, or ``failed``.
4. Handles missing commands and timeouts gracefully.


Functions
---------


get_job_status(jobid)
~~~~~~~~~~~~~~~~~~~~~

Query SLURM for the status of a given job.

:param jobid: SLURM job ID
:type jobid: str
:return: One of ``running``, ``success``, or ``failed``
:rtype: str


**Behavior**

- Uses ``sacct`` to retrieve job state (more reliable for completed jobs).
- If ``sacct`` fails or returns no result, attempts ``squeue``.
- Retries ``sacct`` if a job disappears from the queue.
- Returns ``running`` if the state cannot be determined.


Recognized SLURM States
-----------------------

Running States:

- PENDING (PD)
- RUNNING (R)
- COMPLETING (CG)
- CONFIGURING (CF)
- SUSPENDED (S)
- REQUEUED (RQ)
- RESIZING (RS)

Success States:

- COMPLETED (CD)

Failure States:

- BOOT_FAIL (BF)
- CANCELLED (CA)
- DEADLINE (DL)
- FAILED (F)
- NODE_FAIL (NF)
- OUT_OF_MEMORY (OOM)
- PREEMPTED (PR)
- TIMEOUT (TO)


main()
~~~~~~

Command-line entry point.

- Expects exactly one argument: ``<jobid>``
- Prints the job status to standard output
- Exits with code 1 if incorrect arguments are provided


Example
-------

.. code-block:: bash

   $ python slurm_status.py 123456
   running