# Copyright (c) 2026 Team Big Brain
#
# This file is part of radiomic-feature-extraction-hippocampus-morphometry.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-3.0-or-later


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
        scripts_dir = os.path.join(workflow.basedir, "scripts"),
        feature_list = "original_shape_MeshVolume original_shape_SurfaceVolumeRatio"
    log:
        os.path.join(LOG_DIR, "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}.txt")
    threads: 1
    shell:
        """
        python {params.scripts_dir}/feature_extraction.py pyradiomics \
            --image {input.image} \
            --mask {input.mask} \
            --features {params.feature_list} \
            --subject {wildcards.subject} \
            --session {wildcards.session} \
            --hemisphere {wildcards.hemi} \
            --label {wildcards.label} \
            --output {output.features} \
            > {log} 2>&1
        """


rule extract_pyradiomics_combined:
    input:
        image = lambda wildcards: get_seg_crop_output(wildcards.subject, wildcards.session, wildcards.hemi),
        mask = lambda wildcards: combined_mask_output(wildcards.subject, wildcards.session, wildcards.hemi)
    output:
        features = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                               "sub-{subject}_ses-{session}_hemi-{hemi}_combined_pyradiomics.csv")
    params:
        scripts_dir = os.path.join(workflow.basedir, "scripts"),
        feature_list = "original_shape_MeshVolume original_shape_SurfaceVolumeRatio"
    log:
        os.path.join(LOG_DIR, "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_combined.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_combined.txt")
    threads: 1
    shell:
        """
        python {params.scripts_dir}/feature_extraction.py pyradiomics \
            --image {input.image} \
            --mask {input.mask} \
            --features {params.feature_list} \
            --subject {wildcards.subject} \
            --session {wildcards.session} \
            --hemisphere {wildcards.hemi} \
            --label combined \
            --output {output.features} \
            > {log} 2>&1
        """


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
    params:
        scripts_dir = os.path.join(workflow.basedir, "scripts")
    log:
        os.path.join(LOG_DIR, "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}_curvature.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_label-{label}_curvature.txt")
    threads: 1
    shell:
        """
        python {params.scripts_dir}/feature_extraction.py curvature \
            --vtk {input.vtk} \
            --subject {wildcards.subject} \
            --session {wildcards.session} \
            --hemisphere {wildcards.hemi} \
            --label {wildcards.label} \
            --output {output.features} \
            > {log} 2>&1
        """


rule extract_curvature_combined:
    input:
        vtk = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "meshes",
                          "sub-{subject}_ses-{session}_space-T1w_desc-hsf_hemi-{hemi}_combined_mesh.vtk")
    output:
        features = os.path.join(DERIVATIVES_ROOT, "sub-{subject}", "ses-{session}", "features",
                               "sub-{subject}_ses-{session}_hemi-{hemi}_combined_curvature.csv")
    params:
        scripts_dir = os.path.join(workflow.basedir, "scripts")
    log:
        os.path.join(LOG_DIR, "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_combined_curvature.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "feature_extraction", "sub-{subject}_ses-{session}_hemi-{hemi}_combined_curvature.txt")
    threads: 1
    shell:
        """
        python {params.scripts_dir}/feature_extraction.py curvature \
            --vtk {input.vtk} \
            --subject {wildcards.subject} \
            --session {wildcards.session} \
            --hemisphere {wildcards.hemi} \
            --label combined \
            --output {output.features} \
            > {log} 2>&1
        """


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
    params:
        scripts_dir = os.path.join(workflow.basedir, "scripts")
    log:
        os.path.join(LOG_DIR, "feature_extraction", "sub-{subject}_ses-{session}_aggregate.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "feature_extraction", "sub-{subject}_ses-{session}_aggregate.txt")
    threads: 1
    shell:
        """
        python {params.scripts_dir}/cli_aggregate.py subject \
            --label-radiomics-L {input.label_radiomics_L} \
            --label-radiomics-R {input.label_radiomics_R} \
            --combined-radiomics-L {input.combined_radiomics_L} \
            --combined-radiomics-R {input.combined_radiomics_R} \
            --label-curvature-L {input.label_curvature_L} \
            --label-curvature-R {input.label_curvature_R} \
            --combined-curvature-L {input.combined_curvature_L} \
            --combined-curvature-R {input.combined_curvature_R} \
            --t1w-image {input.t1w_image} \
            --output {output.aggregated} \
            > {log} 2>&1
        """


rule aggregate_all_subjects:
    input:
        subject_features = [os.path.join(DERIVATIVES_ROOT, f"sub-{subject}", f"ses-{session}", "features",
                                        f"sub-{subject}_ses-{session}_all_features.csv")
                           for subject, session in SUBJECT_SESSION_PAIRS]
    output:
        summary = os.path.join(DERIVATIVES_ROOT, "summary", "all_features.csv"),
        issues = os.path.join(DERIVATIVES_ROOT, "summary", "processing_issues.txt")
    params:
        scripts_dir = os.path.join(workflow.basedir, "scripts")
    log:
        os.path.join(LOG_DIR, "feature_extraction", "aggregate_all.log")
    benchmark:
        os.path.join(LOG_DIR, "benchmarks", "feature_extraction", "aggregate_all.txt")
    threads: 1
    shell:
        """
        python {params.scripts_dir}/cli_aggregate.py all \
            --input-files {input.subject_features} \
            --output-summary {output.summary} \
            --output-issues {output.issues} \
            > {log} 2>&1
        """

