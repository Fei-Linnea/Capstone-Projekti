# ============================================================================
# Mesh Generation Rules (Step 3)
# ----------------------------------------------------------------------------
# - Generate VTK meshes from segmentation masks (per label and combined)
# - Emit PNG and HTML visualizations for Snakemake report
# ============================================================================

rule mesh_per_label:
    input:
        mask = lambda wildcards: label_mask_output(wildcards.subject, wildcards.session, wildcards.hemi, wildcards.label)
    output:
        vtk = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                           "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_label-{label}_mesh.vtk"),
        png = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                           "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_label-{label}_mesh.png")
    params:
        scripts_dir = os.path.join(workflow.basedir, "scripts"),
        min_voxel_count = config["mesh_params"]["min_voxel_count"],
        smooth_iters = config["mesh_params"]["smooth_iters"],
        decimation_degree = config["mesh_params"]["decimation_degree"]
    log:
        os.path.join(LOG_DIR, "mesh", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "mesh", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}.txt")
    threads: 1
    shell:
        """
        python {params.scripts_dir}/voxelToMesh.py \
            --input {input.mask} \
            --output {output.vtk} \
            --min-voxel-count {params.min_voxel_count} \
            --smooth-iters {params.smooth_iters} \
            --plot-png {output.png} \
            > {log} 2>&1
        """

rule mesh_combined:
    input:
        mask = lambda wildcards: combined_mask_output(wildcards.subject, wildcards.session, wildcards.hemi)
    output:
        vtk = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                           "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_combined_mesh.vtk"),
        png = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                           "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_combined_mesh.png")
    params:
        scripts_dir = os.path.join(workflow.basedir, "scripts"),
        min_voxel_count = config["mesh_params"]["min_voxel_count"],
        smooth_iters = config["mesh_params"]["smooth_iters"],
        decimation_degree = config["mesh_params"]["decimation_degree"]
    log:
        os.path.join(LOG_DIR, "mesh", "sub-{subject}_ses-{session}_hemi-{hemi}_combined.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "mesh", "sub-{subject}_ses-{session}_hemi-{hemi}_combined.txt")
    threads: 1
    shell:
        """
        python {params.scripts_dir}/voxelToMesh.py \
            --input {input.mask} \
            --output {output.vtk} \
            --min-voxel-count {params.min_voxel_count} \
            --smooth-iters {params.smooth_iters} \
            --plot-png {output.png} \
            > {log} 2>&1
        """
