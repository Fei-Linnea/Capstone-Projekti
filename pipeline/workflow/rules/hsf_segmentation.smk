# ============================================================================
# HSF Segmentation Rule (Step 1)
# ============================================================================
# Hippocampal segmentation using HSF (Hippocampal Segmentation Factory)
# Outputs separate left and right hippocampus segmentations
# ============================================================================

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
    log:
        os.path.join(LOG_DIR, "hsf", "sub-{subject}_ses-{session}.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "hsf", "sub-{subject}_ses-{session}.txt")
    threads: 2
    params:
        scripts_dir = os.path.join(workflow.basedir, "scripts"),
        subject_anat_dir = lambda wildcards: os.path.join(BIDS_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "anat"),
        output_dir = lambda wildcards: os.path.join(DERIVATIVES_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "anat"),
        contrast = HSF_PARAMS["contrast"],
        margin = HSF_PARAMS["margin"],
        seg_mode = HSF_PARAMS["segmentation_mode"],
        ca_mode = HSF_PARAMS["ca_mode"],
        hsf_left = lambda wildcards: os.path.join(BIDS_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "anat", f"sub-{wildcards.subject}_ses-{wildcards.session}_T1w_left_hippocampus_seg.nii.gz"),
        hsf_right = lambda wildcards: os.path.join(BIDS_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "anat", f"sub-{wildcards.subject}_ses-{wildcards.session}_T1w_right_hippocampus_seg.nii.gz"),
        hsf_left_crop = lambda wildcards: os.path.join(BIDS_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "anat", "hsf_outputs", f"sub-{wildcards.subject}_ses-{wildcards.session}_T1w_left_hippocampus_seg_crop.nii.gz"),
        hsf_right_crop = lambda wildcards: os.path.join(BIDS_ROOT, f"sub-{wildcards.subject}", f"ses-{wildcards.session}", "anat", "hsf_outputs", f"sub-{wildcards.subject}_ses-{wildcards.session}_T1w_right_hippocampus_seg_crop.nii.gz")
    shell:
        """
        python {params.scripts_dir}/hsf_wrapper.py \
            --input-t1w {input.t1w} \
            --output-seg {output.seg} \
            --output-left-crop {output.left_crop} \
            --output-right-crop {output.right_crop} \
            --subject-anat-dir {params.subject_anat_dir} \
            --output-dir {params.output_dir} \
            --contrast {params.contrast} \
            --margin '{params.margin}' \
            --seg-mode {params.seg_mode} \
            --ca-mode '{params.ca_mode}' \
            --hsf-left {params.hsf_left} \
            --hsf-right {params.hsf_right} \
            --hsf-left-crop {params.hsf_left_crop} \
            --hsf-right-crop {params.hsf_right_crop} \
            --subject {wildcards.subject} \
            --session {wildcards.session} \
            --log-file {log}
        """
