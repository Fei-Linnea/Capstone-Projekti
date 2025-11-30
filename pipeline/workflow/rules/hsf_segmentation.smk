# ============================================================================
# HSF Segmentation Rule
# ============================================================================
# Hippocampal segmentation using HSF (Hippocampal Segmentation Factory)
# Outputs separate left and right hippocampus segmentations
# ============================================================================

rule hsf_segmentation:
    input:
        t1w = lambda wildcards: get_input_path(wildcards.subject, wildcards.session)
    output:
        seg = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "anat",
                          "sub-{subject}_ses-{session}_space-T1w_desc-hsf_dseg.nii.gz")
    log:
        os.path.join("logs", "hsf", "sub-{subject}_ses-{session}.log")
    params:
        subject_anat_dir = lambda wildcards: os.path.join(BIDS_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "anat"),
        output_dir = lambda wildcards: os.path.join(DERIVATIVES_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "anat"),
        contrast = HSF_PARAMS["contrast"],
        margin = HSF_PARAMS["margin"],
        seg_mode = HSF_PARAMS["segmentation_mode"],
        ca_mode = HSF_PARAMS["ca_mode"],
        hsf_left = lambda wildcards: os.path.join(BIDS_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "anat", f"sub-{wildcards.subject}_ses-{wildcards.session}_T1w_left_hippocampus_seg.nii.gz"),
        hsf_right = lambda wildcards: os.path.join(BIDS_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "anat", f"sub-{wildcards.subject}_ses-{wildcards.session}_T1w_right_hippocampus_seg.nii.gz")
    shell:
        """
        set -euo pipefail
        
        # Log start
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting HSF segmentation" > {log}
        echo "Subject: {wildcards.subject}, Session: {wildcards.session}" >> {log}
        echo "Input: {input.t1w}" >> {log}
        
        # Verify input file exists
        if [ ! -f "{input.t1w}" ]; then
            echo "ERROR: Input file not found: {input.t1w}" >> {log}
            exit 1
        fi
        
        # Create output directory
        mkdir -p {params.output_dir}
        
        # Run HSF segmentation
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running HSF..." >> {log}
        echo "Command: hsf files.path={params.subject_anat_dir} files.pattern=*T1w.nii.gz roiloc.contrast={params.contrast} roiloc.margin={params.margin} segmentation={params.seg_mode} segmentation.ca_mode={params.ca_mode}" >> {log}
        
        hsf files.path="{params.subject_anat_dir}" \
            files.pattern="*T1w.nii.gz" \
            roiloc.contrast="{params.contrast}" \
            roiloc.margin="{params.margin}" \
            segmentation="{params.seg_mode}" \
            segmentation.ca_mode="{params.ca_mode}" 2>&1 | tee -a {log}
        
        # HSF creates left and right hippocampus segmentations separately
        # Move them to derivatives directory
        if [ -f "{params.hsf_left}" ] && [ -f "{params.hsf_right}" ]; then
            # Move both segmentations to output directory
            mv "{params.hsf_left}" "{params.output_dir}/sub-{wildcards.subject}_ses-{wildcards.session}_left_hippocampus_seg.nii.gz"
            mv "{params.hsf_right}" "{params.output_dir}/sub-{wildcards.subject}_ses-{wildcards.session}_right_hippocampus_seg.nii.gz"
            
            # Use one as the main output (or combine them if needed)
            cp "{params.output_dir}/sub-{wildcards.subject}_ses-{wildcards.session}_left_hippocampus_seg.nii.gz" {output.seg}
            
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Segmentation completed successfully" >> {log}
            echo "Output: {output.seg}" >> {log}
            echo "Left hippocampus: {params.output_dir}/sub-{wildcards.subject}_ses-{wildcards.session}_left_hippocampus_seg.nii.gz" >> {log}
            echo "Right hippocampus: {params.output_dir}/sub-{wildcards.subject}_ses-{wildcards.session}_right_hippocampus_seg.nii.gz" >> {log}
        else
            echo "ERROR: HSF outputs not found" >> {log}
            echo "Expected left: {params.hsf_left}" >> {log}
            echo "Expected right: {params.hsf_right}" >> {log}
            ls -la {params.subject_anat_dir} >> {log}
            exit 1
        fi
        """
