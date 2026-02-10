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
        label_value = lambda wildcards: LABELS[wildcards.label]
    log:
        os.path.join(LOG_DIR, "data_processing", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "data_processing", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}.txt")
    threads: 1
    resources:
        mem_mb=200
    run:
        Path(output.label_mask).parent.mkdir(parents=True, exist_ok=True)
        split_one_label(input.seg_crop, output.label_mask, params.label_value)
        Path(log[0]).write_text(f"Split label {wildcards.label} (value {params.label_value}) from {input.seg_crop}\nOutput: {output.label_mask}\n")


rule combine_labels:
    input:
        seg_crop = lambda wildcards: get_seg_crop_output(wildcards.subject, wildcards.session, wildcards.hemi)
    output:
        combined_mask = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "anat",
                                    "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_mask.nii.gz")
    log:
        os.path.join(LOG_DIR, "data_processing", "sub-{subject}_ses-{session}_hemi-{hemi}_combined.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "data_processing", "sub-{subject}_ses-{session}_hemi-{hemi}_combined.txt")
    threads: 1
    resources:
        mem_mb=2000
    run:
        Path(output.combined_mask).parent.mkdir(parents=True, exist_ok=True)
        combine_labels(input.seg_crop, output.combined_mask)
        Path(log[0]).write_text(f"Combined labels from {input.seg_crop}\nOutput: {output.combined_mask}\n")
