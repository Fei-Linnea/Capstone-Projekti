
The workflow consists of four main stages:

HSF Segmentation Rule (Step 1)
==============================

This rule performs **hippocampal segmentation** using HSF (Hippocampal Segmentation Factory).  

- Generates **left and right hippocampus segmentations** for each subject/session.
- Outputs:
  - Full hippocampus segmentation (`*_dseg.nii.gz`)
  - Cropped left hemisphere segmentation (`*_hemi-L_seg_crop.nii.gz`)
  - Cropped right hemisphere segmentation (`*_hemi-R_seg_crop.nii.gz`)
- Uses `hsf_wrapper.py` script to execute segmentation.
- Logs operations and benchmarks execution time.

.. code-block:: python

    rule hsf_segmentation:
        input:
            t1w = lambda wildcards: get_input_path(wildcards.subject, wildcards.session)
        output:
            seg = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "anat",
                              "sub-{subject}_ses-{session}_space-T1w_desc-hsf_dseg.nii.gz"),
            left_crop = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "anat",
                                    "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-L_seg_crop.nii.gz"),
            right_crop = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "anat",
                                     "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-R_seg_crop.nii.gz")
        script:
            "../scripts/hsf_wrapper.py"


Data Processing Rules (Step 2)
==============================

These rules process HSF hippocampal segmentations:

- **split_label**: Splits a cropped hippocampal segmentation into individual labels
  (DG, CA1, CA2, CA3, SUB) and saves each label as a separate mask.

- **combine_labels**: Combines all individual labels into a single hippocampus
  mask for each hemisphere.

Each rule logs its operations and benchmarks execution time.

.. code-block:: python

    rule split_label:
        input:
            seg_crop = lambda wildcards: get_seg_crop_output(wildcards.subject, wildcards.session, wildcards.hemi)
        output:
            label_mask = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "anat",
                                      "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_label-{label}_mask.nii.gz")
        run:
            split_one_label(input.seg_crop, output.label_mask, LABELS[wildcards.label])


    rule combine_labels:
        input:
            seg_crop = lambda wildcards: get_seg_crop_output(wildcards.subject, wildcards.session, wildcards.hemi)
        output:
            combined_mask = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "anat",
                                        "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_mask.nii.gz")
        run:
            combine_labels(input.seg_crop, output.combined_mask)


Mesh Generation Rules (Step 3)
==============================

These rules generate **VTK meshes** from hippocampal segmentation masks and
produce PNG visualizations for inclusion in reports:

- **mesh_per_label**: Generates meshes for each individual label (DG, CA1, CA2, CA3, SUB)
  and outputs corresponding VTK and PNG files.
- **mesh_combined**: Generates a single mesh combining all labels for each hemisphere.
- Both rules log operations and support benchmarking.


.. code-block:: python

    rule mesh_per_label:
        input:
            mask = lambda wildcards: label_mask_output(wildcards.subject, wildcards.session, wildcards.hemi)
        output:
            vtk = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                               "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_label-{label}_mesh.vtk"),
            png = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                               "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_label-{label}_mesh.png")
        run:
            Path(output.vtk).parent.mkdir(parents=True, exist_ok=True)
            nii_to_vtk(
                input.mask,
                output.vtk,
                min_voxel_count=params.min_voxel_count,
                smooth_iters=params.smooth_iters,
                plot_png_path=output.png,
                enable_interactive_plot=False,
            )

    rule mesh_combined:
        input:
            mask = lambda wildcards: combined_mask_output(wildcards.subject, wildcards.session, wildcards.hemi)
        output:
            vtk = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                               "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_combined_mesh.vtk"),
            png = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                               "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_combined_mesh.png")
        run:
            Path(output.vtk).parent.mkdir(parents=True, exist_ok=True)
            nii_to_vtk(
                input.mask,
                output.vtk,
                min_voxel_count=params.min_voxel_count,
                smooth_iters=params.smooth_iters,
                plot_png_path=output.png,
                enable_interactive_plot=False,
            )


Feature Extraction and Aggregation Rules (Steps 4–6)
====================================================

These rules extract **radiomic and curvature features** from hippocampal segmentations
and aggregate them across regions and subjects.

- **extract_pyradiomics_per_label**: Extracts PyRadiomics features (e.g., MeshVolume,
  SurfaceVolumeRatio) for each individual label (DG, CA1, CA2, CA3, SUB).  
- **extract_pyradiomics_combined**: Extracts PyRadiomics features for combined hippocampal masks.  
- **extract_curvature_per_label**: Computes curvature metrics from VTK meshes per label.  
- **extract_curvature_combined**: Computes curvature metrics for combined meshes.  
- **aggregate_subject_features**: Aggregates radiomics and curvature features for a
  single subject/session into a single CSV.  
- **aggregate_all_subjects**: Combines all subjects’ aggregated features into a summary CSV
  and creates a processing issues report.


.. code-block:: python

    # Radiomics per label
    rule extract_pyradiomics_per_label:
        input:
            image = lambda w: get_seg_crop_output(w.subject, w.session, w.hemi),
            mask = lambda w: label_mask_output(w.subject, w.session, w.hemi, w.label)
        output:
            features = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                                   "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}_pyradiomics.csv")
        run:
            Path(output.features).parent.mkdir(parents=True, exist_ok=True)
            features_dict = extract_pyradiomics_features(input.image, input.mask,
                                                         ['original_shape_MeshVolume', 'original_shape_SurfaceVolumeRatio'])
            df = pd.DataFrame([features_dict])
            df.to_csv(output.features, index=False)

    # Radiomics combined
    rule extract_pyradiomics_combined:
        input:
            image = lambda w: get_seg_crop_output(w.subject, w.session, w.hemi),
            mask = lambda w: combined_mask_output(w.subject, w.session, w.hemi)
        output:
            features = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                                   "sub-{subject}_ses-{session}_hemi-{hemi}_combined_pyradiomics.csv")
        run:
            Path(output.features).parent.mkdir(parents=True, exist_ok=True)
            features_dict = extract_pyradiomics_features(input.image, input.mask,
                                                         ['original_shape_MeshVolume', 'original_shape_SurfaceVolumeRatio'])
            df = pd.DataFrame([features_dict])
            df.to_csv(output.features, index=False)

    # Curvature per label
    rule extract_curvature_per_label:
        input:
            vtk = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                              "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_label-{label}_mesh.vtk")
        output:
            features = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                                   "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}_curvature.csv")
        run:
            Path(output.features).parent.mkdir(parents=True, exist_ok=True)
            curvature_df = extract_curvatures(input.vtk)
            metrics = calculate_curv_metrics(curvature_df)
            df = pd.DataFrame([metrics])
            df.to_csv(output.features, index=False)

    # Curvature combined
    rule extract_curvature_combined:
        input:
            vtk = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                              "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_combined_mesh.vtk")
        output:
            features = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                                   "sub-{subject}_ses-{session}_hemi-{hemi}_combined_curvature.csv")
        run:
            Path(output.features).parent.mkdir(parents=True, exist_ok=True)
            curvature_df = extract_curvatures(input.vtk)
            metrics = calculate_curv_metrics(curvature_df)
            df = pd.DataFrame([metrics])
            df.to_csv(output.features, index=False)

    # Aggregate per subject
    rule aggregate_subject_features:
        input:
            label_radiomics_L = ..., label_radiomics_R = ...,
            combined_radiomics_L = ..., combined_radiomics_R = ...,
            label_curvature_L = ..., label_curvature_R = ...,
            combined_curvature_L = ..., combined_curvature_R = ...,
            t1w_image = lambda w: get_input_path(w.subject, w.session)
        output:
            aggregated = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                                     "sub-{subject}_ses-{session}_all_features.csv")
        run:
            row = form_row_from_data(input.t1w_image, radiomics_data, curvature_data)
            Path(output.aggregated).parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame([row]).to_csv(output.aggregated, index=False)

    # Aggregate across all subjects
    rule aggregate_all_subjects:
        input:
            subject_features = [os.path.join(DERIVATIVES_ROOT, f"sub-{subject}", f"ses-{session}", "features",
                                             f"sub-{subject}_ses-{session}_all_features.csv")
                               for subject, session in SUBJECT_SESSION_PAIRS]
        output:
            summary = os.path.join(DERIVATIVES_ROOT, "summary", "all_features.csv"),
            issues = os.path.join(DERIVATIVES_ROOT, "summary", "processing_issues.txt")
        run:
            Path(output.summary).parent.mkdir(parents=True, exist_ok=True)
            combined_df = pd.concat([pd.read_csv(f) for f in input.subject_features], ignore_index=True)
            combined_df.to_csv(output.summary, index=False)

