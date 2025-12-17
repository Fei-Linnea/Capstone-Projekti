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


rule aggregate_subject_features:
    input:
        # All label features for BOTH hemispheres
        label_features_L = lambda wildcards: expand(
            os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                        "sub-{subject}_ses-{session}_hemi-L_label-{label}_pyradiomics.csv"),
            subject=wildcards.subject,
            session=wildcards.session,
            label=LABELS.keys()
        ),
        label_features_R = lambda wildcards: expand(
            os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                        "sub-{subject}_ses-{session}_hemi-R_label-{label}_pyradiomics.csv"),
            subject=wildcards.subject,
            session=wildcards.session,
            label=LABELS.keys()
        ),
        combined_features_L = lambda wildcards: os.path.join(DERIVATIVES_ROOT, 
            f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "features",
            f"sub-{wildcards.subject}_ses-{wildcards.session}_hemi-L_combined_pyradiomics.csv"),
        combined_features_R = lambda wildcards: os.path.join(DERIVATIVES_ROOT, 
            f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "features",
            f"sub-{wildcards.subject}_ses-{wildcards.session}_hemi-R_combined_pyradiomics.csv")
    output:
        aggregated = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                                 "sub-{subject}_ses-{session}_all_features.csv")
    log:
        os.path.join("logs", "feature_extraction", "sub-{subject}_ses-{session}_aggregate.log")
    run:
        # Read LEFT hemisphere features
        label_data_L = {}
        for csv_file in input.label_features_L:
            df = pd.read_csv(csv_file)
            label = df['label'].values[0]
            # Extract only the feature columns (remove metadata)
            feature_dict = {k: v for k, v in df.to_dict('records')[0].items() 
                          if k not in ['subject', 'session', 'hemisphere', 'label']}
            label_data_L[label] = feature_dict
        
        combined_df_L = pd.read_csv(input.combined_features_L)
        combined_data_L = {k: v for k, v in combined_df_L.to_dict('records')[0].items() 
                          if k not in ['subject', 'session', 'hemisphere', 'label']}
        
        # Read RIGHT hemisphere features
        label_data_R = {}
        for csv_file in input.label_features_R:
            df = pd.read_csv(csv_file)
            label = df['label'].values[0]
            feature_dict = {k: v for k, v in df.to_dict('records')[0].items() 
                          if k not in ['subject', 'session', 'hemisphere', 'label']}
            label_data_R[label] = feature_dict
        
        combined_df_R = pd.read_csv(input.combined_features_R)
        combined_data_R = {k: v for k, v in combined_df_R.to_dict('records')[0].items() 
                          if k not in ['subject', 'session', 'hemisphere', 'label']}
        
        # Use aggregate_region_data to organize data (empty dict for curvature data)
        radiomics_data = aggregate_region_data(
            combined_data_L, label_data_L.get('DG', {}), label_data_L.get('CA1', {}), 
            label_data_L.get('CA2', {}), label_data_L.get('CA3', {}), label_data_L.get('SUB', {}),
            combined_data_R, label_data_R.get('DG', {}), label_data_R.get('CA1', {}), 
            label_data_R.get('CA2', {}), label_data_R.get('CA3', {}), label_data_R.get('SUB', {})
        )
        
        # Build row with Subject and Session first
        row = {
            'Subject': wildcards.subject,
            'Session': wildcards.session
        }
        
        # Add radiomics features for each region and hemisphere
        for region in ['Hippocampus', 'DG', 'CA1', 'CA2', 'CA3', 'SUB']:
            for side in ['L', 'R']:
                for feature_name, value in radiomics_data.get(region, {}).get(side, {}).items():
                    # Remove "original_shape_" prefix from feature name
                    clean_feature_name = feature_name.replace("original_shape_", "")
                    row[f'Radiomics_{region}_{side}_{clean_feature_name}'] = value
        
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

