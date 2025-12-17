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
        min_voxel_count = config["mesh_params"]["min_voxel_count"],
        smooth_iters = config["mesh_params"]["smooth_iters"],
        decimation_degree = config["mesh_params"]["decimation_degree"],
        html_path = lambda wildcards: os.path.join(DERIVATIVES_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "meshes",
                                                    f"sub-{wildcards.subject}_ses-{wildcards.session}_space-T1w_desc-hsf_hemi-{wildcards.hemi}_label-{wildcards.label}_mesh.html")
    log:
        os.path.join("logs", "mesh", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}.log")
    run:
        Path(output.vtk).parent.mkdir(parents=True, exist_ok=True)
        nii_to_vtk(
            input.mask,
            output.vtk,
            min_voxel_count=params.min_voxel_count,
            smooth_iters=params.smooth_iters,
            decimation_degree=params.decimation_degree,
            plot_png_path=output.png,
            # plot_html_path=params.html_path,
            enable_interactive_plot=False,
        )
        Path(log[0]).write_text(
            f"Generated mesh for label {wildcards.label} from {input.mask}\n"
            f"VTK: {output.vtk}\nPNG: {output.png}\nHTML: {params.html_path}\n"
        )

rule mesh_combined:
    input:
        mask = lambda wildcards: combined_mask_output(wildcards.subject, wildcards.session, wildcards.hemi)
    output:
        vtk = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                           "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_combined_mesh.vtk"),
        png = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                           "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_combined_mesh.png")
    params:
        min_voxel_count = config["mesh_params"]["min_voxel_count"],
        smooth_iters = config["mesh_params"]["smooth_iters"],
        decimation_degree = config["mesh_params"]["decimation_degree"],
        # html_path = lambda wildcards: os.path.join(DERIVATIVES_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "meshes",
        #             f"sub-{wildcards.subject}_ses-{wildcards.session}_space-T1w_desc-hsf_hemi-{wildcards.hemi}_combined_mesh.html")
    log:
        os.path.join("logs", "mesh", "sub-{subject}_ses-{session}_hemi-{hemi}_combined.log")
    run:
        Path(output.vtk).parent.mkdir(parents=True, exist_ok=True)
        nii_to_vtk(
            input.mask,
            output.vtk,
            min_voxel_count=params.min_voxel_count,
            smooth_iters=params.smooth_iters,
            decimation_degree=params.decimation_degree,
            plot_png_path=output.png,
            # plot_html_path=params.html_path,
            enable_interactive_plot=False,
        )
        Path(log[0]).write_text(
            f"Generated combined mesh from {input.mask}\n"
            f"VTK: {output.vtk}\nPNG: {output.png}\n"
        )
