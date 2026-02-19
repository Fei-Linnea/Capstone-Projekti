# ============================================================================
# Data Processing Rules (Step 2)
# ----------------------------------------------------------------------------
# - Split HSF cropped segmentations into individual labels (DG, CA1, CA2, CA3, SUB)
# - Combine all labels into a single hippocampus mask per hemisphere
# ============================================================================

rule split_label:
    input:
        seg_crop = lambda wildcards: get_seg_crop_output(wildcards.subject, wildcards.session, wildcards.hemi)
    output:
        label_mask = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "anat",
                                  "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_label-{label}_mask.nii.gz")
    params:
        scripts_dir = os.path.join(workflow.basedir, "scripts"),
        label_value = lambda wildcards: LABELS[wildcards.label]
    log:
        os.path.join(LOG_DIR, "data_processing", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "data_processing", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}.txt")
    threads: 1
    resources:
        mem_mb=200
    shell:
        """
        python {params.scripts_dir}/nii_parse.py split \
            --input {input.seg_crop} \
            --output {output.label_mask} \
            --label {params.label_value} \
            > {log} 2>&1
        """


rule combine_labels:
    input:
        seg_crop = lambda wildcards: get_seg_crop_output(wildcards.subject, wildcards.session, wildcards.hemi)
    output:
        combined_mask = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "anat",
                                    "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_mask.nii.gz")
    params:
        scripts_dir = os.path.join(workflow.basedir, "scripts")
    log:
        os.path.join(LOG_DIR, "data_processing", "sub-{subject}_ses-{session}_hemi-{hemi}_combined.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "data_processing", "sub-{subject}_ses-{session}_hemi-{hemi}_combined.txt")
    threads: 1
    shell:
        """
        python {params.scripts_dir}/nii_parse.py combine \
            --input {input.seg_crop} \
            --output {output.combined_mask} \
            > {log} 2>&1
        """
