# ============================================================================
# Feature Extraction Rules (Step 3)
# ----------------------------------------------------------------------------
# - Extract PyRadiomics features from original T1w images
# - Extract for each label (DG, CA1, CA2, CA3, SUB) AND combined mask
# - Features: VoxelVolume, SurfaceVolumeRatio
# ============================================================================

rule extract_pyradiomics_per_label:
    input:
        image = lambda wildcards: get_seg_crop_output(wildcards.subject, wildcards.session, wildcards.hemi),
        mask = lambda wildcards: label_mask_output(wildcards.subject, wildcards.session, wildcards.hemi, wildcards.label)
    output:
        features = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                               "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}_pyradiomics.csv")
    params:
        features = ['original_shape_MeshVolume', 'original_shape_SurfaceVolumeRatio']
    log:
        os.path.join("logs", "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}.log")
    run:
        # Create output directory
        Path(output.features).parent.mkdir(parents=True, exist_ok=True)
        
        # Extract features
        features_dict = extract_pyradiomics_features(
            input.image,
            input.mask,
            params.features
        )
        
        # Add metadata
        features_dict['subject'] = wildcards.subject
        features_dict['session'] = wildcards.session
        features_dict['hemisphere'] = wildcards.hemi
        features_dict['label'] = wildcards.label
        
        # Convert to DataFrame and save
        df = pd.DataFrame([features_dict])
        df.to_csv(output.features, index=False)
        
        # Write log
        Path(log[0]).write_text(
            f"Extracted PyRadiomics features\n"
            f"Subject: {wildcards.subject}, Session: {wildcards.session}\n"
            f"Hemisphere: {wildcards.hemi}, Label: {wildcards.label}\n"
            f"Image: {input.image}\n"
            f"Mask: {input.mask}\n"
            f"Output: {output.features}\n"
        )


rule extract_pyradiomics_combined:
    input:
        image = lambda wildcards: get_seg_crop_output(wildcards.subject, wildcards.session, wildcards.hemi),
        mask = lambda wildcards: combined_mask_output(wildcards.subject, wildcards.session, wildcards.hemi)
    output:
        features = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                               "sub-{subject}_ses-{session}_hemi-{hemi}_combined_pyradiomics.csv")
    params:
        features = ['original_shape_MeshVolume', 'original_shape_SurfaceVolumeRatio']
    log:
        os.path.join("logs", "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_combined.log")
    run:
        # Create output directory
        Path(output.features).parent.mkdir(parents=True, exist_ok=True)
        
        # Extract features
        features_dict = extract_pyradiomics_features(
            input.image,
            input.mask,
            params.features
        )
        
        # Add metadata
        features_dict['subject'] = wildcards.subject
        features_dict['session'] = wildcards.session
        features_dict['hemisphere'] = wildcards.hemi
        features_dict['label'] = 'combined'
        
        # Convert to DataFrame and save
        df = pd.DataFrame([features_dict])
        df.to_csv(output.features, index=False)
        
        # Write log
        Path(log[0]).write_text(
            f"Extracted PyRadiomics features (combined)\n"
            f"Subject: {wildcards.subject}, Session: {wildcards.session}\n"
            f"Hemisphere: {wildcards.hemi}\n"
            f"Image: {input.image}\n"
            f"Mask: {input.mask}\n"
            f"Output: {output.features}\n"
        )


# ============================================================================
# Curvature Feature Extraction (Step 5)
# ============================================================================

rule extract_curvature_per_label:
    input:
        vtk = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                          "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_label-{label}_mesh.vtk")
    output:
        features = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                               "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}_curvature.csv")
    log:
        os.path.join("logs", "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}_curvature.log")
    run:
        import sys
        from pathlib import Path
        sys.path.insert(0, "/app/pipeline/workflow/scripts")
        from feature_extraction import extract_curvatures, calculate_curv_metrics
        import pandas as pd
        
        # Create output directory
        Path(output.features).parent.mkdir(parents=True, exist_ok=True)
        
        # Extract curvatures from VTK mesh
        curvature_df = extract_curvatures(input.vtk)
        
        # Calculate curvature metrics (statistics)
        metrics_dict = calculate_curv_metrics(curvature_df)
        
        # Flatten the nested dict for CSV storage
        # From {'Mean': {'median': 0.5, ...}, ...} to {'Mean_median': 0.5, ...}
        flat_metrics = {}
        for curv_type, stats in metrics_dict.items():
            for stat_name, value in stats.items():
                # Convert numpy types to Python float
                flat_metrics[f'{curv_type}_{stat_name}'] = float(value)
        
        # Add metadata
        flat_metrics['subject'] = wildcards.subject
        flat_metrics['session'] = wildcards.session
        flat_metrics['hemisphere'] = wildcards.hemi
        flat_metrics['label'] = wildcards.label
        
        # Convert to DataFrame and save
        df = pd.DataFrame([flat_metrics])
        df.to_csv(output.features, index=False)
        
        # Write log
        Path(log[0]).write_text(
            f"Extracted curvature features\n"
            f"Subject: {wildcards.subject}, Session: {wildcards.session}\n"
            f"Hemisphere: {wildcards.hemi}, Label: {wildcards.label}\n"
            f"VTK: {input.vtk}\n"
            f"Output: {output.features}\n"
        )


rule extract_curvature_combined:
    input:
        vtk = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                          "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_combined_mesh.vtk")
    output:
        features = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                               "sub-{subject}_ses-{session}_hemi-{hemi}_combined_curvature.csv")
    log:
        os.path.join("logs", "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_combined_curvature.log")
    run:
        import sys
        from pathlib import Path
        sys.path.insert(0, "/app/pipeline/workflow/scripts")
        from feature_extraction import extract_curvatures, calculate_curv_metrics
        import pandas as pd
        
        # Create output directory
        Path(output.features).parent.mkdir(parents=True, exist_ok=True)
        
        # Extract curvatures from VTK mesh
        curvature_df = extract_curvatures(input.vtk)
        
        # Calculate curvature metrics (statistics)
        metrics_dict = calculate_curv_metrics(curvature_df)
        
        # Flatten the nested dict for CSV storage
        # From {'Mean': {'median': 0.5, ...}, ...} to {'Mean_median': 0.5, ...}
        flat_metrics = {}
        for curv_type, stats in metrics_dict.items():
            for stat_name, value in stats.items():
                # Convert numpy types to Python float
                flat_metrics[f'{curv_type}_{stat_name}'] = float(value)
        
        # Add metadata
        flat_metrics['subject'] = wildcards.subject
        flat_metrics['session'] = wildcards.session
        flat_metrics['hemisphere'] = wildcards.hemi
        flat_metrics['label'] = 'combined'
        
        # Convert to DataFrame and save
        df = pd.DataFrame([flat_metrics])
        df.to_csv(output.features, index=False)
        
        # Write log
        Path(log[0]).write_text(
            f"Extracted curvature features (combined)\n"
            f"Subject: {wildcards.subject}, Session: {wildcards.session}\n"
            f"Hemisphere: {wildcards.hemi}\n"
            f"VTK: {input.vtk}\n"
            f"Output: {output.features}\n"
        )


# ============================================================================
# Data Aggregation (Step 6)
# ============================================================================

rule aggregate_subject_features:
    input:
        # Radiomics features for BOTH hemispheres
        label_radiomics_L = lambda wildcards: expand(
            os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                        "sub-{subject}_ses-{session}_hemi-L_label-{label}_pyradiomics.csv"),
            subject=wildcards.subject,
            session=wildcards.session,
            label=LABELS.keys()
        ),
        label_radiomics_R = lambda wildcards: expand(
            os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                        "sub-{subject}_ses-{session}_hemi-R_label-{label}_pyradiomics.csv"),
            subject=wildcards.subject,
            session=wildcards.session,
            label=LABELS.keys()
        ),
        combined_radiomics_L = lambda wildcards: os.path.join(DERIVATIVES_ROOT, 
            f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "features",
            f"sub-{wildcards.subject}_ses-{wildcards.session}_hemi-L_combined_pyradiomics.csv"),
        combined_radiomics_R = lambda wildcards: os.path.join(DERIVATIVES_ROOT, 
            f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "features",
            f"sub-{wildcards.subject}_ses-{wildcards.session}_hemi-R_combined_pyradiomics.csv"),
        # Curvature features for BOTH hemispheres
        label_curvature_L = lambda wildcards: expand(
            os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                        "sub-{subject}_ses-{session}_hemi-L_label-{label}_curvature.csv"),
            subject=wildcards.subject,
            session=wildcards.session,
            label=LABELS.keys()
        ),
        label_curvature_R = lambda wildcards: expand(
            os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                        "sub-{subject}_ses-{session}_hemi-R_label-{label}_curvature.csv"),
            subject=wildcards.subject,
            session=wildcards.session,
            label=LABELS.keys()
        ),
        combined_curvature_L = lambda wildcards: os.path.join(DERIVATIVES_ROOT, 
            f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "features",
            f"sub-{wildcards.subject}_ses-{wildcards.session}_hemi-L_combined_curvature.csv"),
        combined_curvature_R = lambda wildcards: os.path.join(DERIVATIVES_ROOT, 
            f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "features",
            f"sub-{wildcards.subject}_ses-{wildcards.session}_hemi-R_combined_curvature.csv"),
        # Original T1w image (for BIDS metadata extraction)
        t1w_image = lambda wildcards: get_input_path(wildcards.subject, wildcards.session)
    output:
        aggregated = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                                 "sub-{subject}_ses-{session}_all_features.csv")
    log:
        os.path.join("logs", "feature_extraction", "sub-{subject}_ses-{session}_aggregate.log")
    run:
        import sys
        from pathlib import Path
        sys.path.insert(0, "/app/pipeline/workflow/scripts")
        from aggregate_data import aggregate_region_data, form_row_from_data
        import pandas as pd
        
        # ===== Read RADIOMICS features =====
        # Left hemisphere
        label_radiomics_L = {}
        for csv_file in input.label_radiomics_L:
            df = pd.read_csv(csv_file)
            label = df['label'].values[0]
            feature_dict = {k: v for k, v in df.to_dict('records')[0].items() 
                          if k not in ['subject', 'session', 'hemisphere', 'label']}
            label_radiomics_L[label] = feature_dict
        
        combined_rad_df_L = pd.read_csv(input.combined_radiomics_L)
        combined_radiomics_L = {k: v for k, v in combined_rad_df_L.to_dict('records')[0].items() 
                               if k not in ['subject', 'session', 'hemisphere', 'label']}
        
        # Right hemisphere
        label_radiomics_R = {}
        for csv_file in input.label_radiomics_R:
            df = pd.read_csv(csv_file)
            label = df['label'].values[0]
            feature_dict = {k: v for k, v in df.to_dict('records')[0].items() 
                          if k not in ['subject', 'session', 'hemisphere', 'label']}
            label_radiomics_R[label] = feature_dict
        
        combined_rad_df_R = pd.read_csv(input.combined_radiomics_R)
        combined_radiomics_R = {k: v for k, v in combined_rad_df_R.to_dict('records')[0].items() 
                               if k not in ['subject', 'session', 'hemisphere', 'label']}
        
        # ===== Read CURVATURE features =====
        # Helper function to restructure curvature data from flat CSV to nested dict
        def restructure_curvature_dict(flat_dict):
            """
            Convert flat dict like {'Mean_median': 0.5, 'Mean_mean': 0.6, ...}
            to nested dict like {'Mean': {'median': 0.5, 'mean': 0.6, ...}, ...}
            """
            nested = {}
            for key, value in flat_dict.items():
                # Split on first underscore: 'Mean_median' -> ['Mean', 'median']
                parts = key.split('_', 1)
                if len(parts) == 2:
                    curv_type, stat_name = parts
                    if curv_type not in nested:
                        nested[curv_type] = {}
                    nested[curv_type][stat_name] = value
            return nested
        
        # Left hemisphere
        label_curvature_L = {}
        for csv_file in input.label_curvature_L:
            df = pd.read_csv(csv_file)
            label = df['label'].values[0]
            flat_dict = {k: v for k, v in df.to_dict('records')[0].items() 
                        if k not in ['subject', 'session', 'hemisphere', 'label']}
            label_curvature_L[label] = restructure_curvature_dict(flat_dict)
        
        combined_curv_df_L = pd.read_csv(input.combined_curvature_L)
        flat_combined_L = {k: v for k, v in combined_curv_df_L.to_dict('records')[0].items() 
                          if k not in ['subject', 'session', 'hemisphere', 'label']}
        combined_curvature_L = restructure_curvature_dict(flat_combined_L)
        
        # Right hemisphere
        label_curvature_R = {}
        for csv_file in input.label_curvature_R:
            df = pd.read_csv(csv_file)
            label = df['label'].values[0]
            flat_dict = {k: v for k, v in df.to_dict('records')[0].items() 
                        if k not in ['subject', 'session', 'hemisphere', 'label']}
            label_curvature_R[label] = restructure_curvature_dict(flat_dict)
        
        combined_curv_df_R = pd.read_csv(input.combined_curvature_R)
        flat_combined_R = {k: v for k, v in combined_curv_df_R.to_dict('records')[0].items() 
                          if k not in ['subject', 'session', 'hemisphere', 'label']}
        combined_curvature_R = restructure_curvature_dict(flat_combined_R)
        
        # ===== Aggregate using aggregate_region_data function =====
        # Aggregate radiomics data
        radiomics_data = aggregate_region_data(
            combined_radiomics_L, 
            label_radiomics_L.get('DG', {}), 
            label_radiomics_L.get('CA1', {}), 
            label_radiomics_L.get('CA2', {}), 
            label_radiomics_L.get('CA3', {}), 
            label_radiomics_L.get('SUB', {}),
            combined_radiomics_R, 
            label_radiomics_R.get('DG', {}), 
            label_radiomics_R.get('CA1', {}), 
            label_radiomics_R.get('CA2', {}), 
            label_radiomics_R.get('CA3', {}), 
            label_radiomics_R.get('SUB', {})
        )
        
        # Aggregate curvature data
        curvature_data = aggregate_region_data(
            combined_curvature_L, 
            label_curvature_L.get('DG', {}), 
            label_curvature_L.get('CA1', {}), 
            label_curvature_L.get('CA2', {}), 
            label_curvature_L.get('CA3', {}), 
            label_curvature_L.get('SUB', {}),
            combined_curvature_R, 
            label_curvature_R.get('DG', {}), 
            label_curvature_R.get('CA1', {}), 
            label_curvature_R.get('CA2', {}), 
            label_curvature_R.get('CA3', {}), 
            label_curvature_R.get('SUB', {})
        )
        
        # ===== Use form_row_from_data to create the final row =====
        row = form_row_from_data(input.t1w_image, radiomics_data, curvature_data)
        
        # Create output directory
        Path(output.aggregated).parent.mkdir(parents=True, exist_ok=True)
        
        # Save aggregated features
        df_out = pd.DataFrame([row])
        df_out.to_csv(output.aggregated, index=False)
        
        # Write log
        Path(log[0]).write_text(
            f"Aggregated features for sub-{wildcards.subject}_ses-{wildcards.session}\n"
            f"Regions: Hippocampus, DG, CA1, CA2, CA3, SUB\n"
            f"Hemispheres: L, R\n"
            f"Features: Radiomics + Curvature\n"
            f"Output: {output.aggregated}\n"
        )


rule aggregate_all_subjects:
    input:
        subject_features = [os.path.join(DERIVATIVES_ROOT, f"sub-{subject}", f"ses-{session}", "features",
                                        f"sub-{subject}_ses-{session}_all_features.csv")
                           for subject, session in SUBJECT_SESSION_PAIRS]
    output:
        summary = os.path.join(DERIVATIVES_ROOT, "summary", "all_features.csv")
    log:
        os.path.join("logs", "feature_extraction", "aggregate_all.log")
    run:
        # Create output directory
        Path(output.summary).parent.mkdir(parents=True, exist_ok=True)
        
        # Read all subject feature files
        all_dfs = []
        for csv_file in input.subject_features:
            df = pd.read_csv(csv_file)
            all_dfs.append(df)
        
        # Concatenate all dataframes
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Sort by Subject, Session
        combined_df = combined_df.sort_values(['Subject', 'Session'])
        
        # Save combined CSV
        combined_df.to_csv(output.summary, index=False)
        
        # Write log
        Path(log[0]).write_text(
            f"Aggregated {len(all_dfs)} subject feature files\n"
            f"Total rows: {len(combined_df)}\n"
            f"Output: {output.summary}\n"
        )

