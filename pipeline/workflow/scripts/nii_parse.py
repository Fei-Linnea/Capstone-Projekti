"""
Mask processing utilities for hippocampal segmentation outputs.

This module provides functions for:

1. Converting fuzzy/probabilistic segmentation masks into binary masks.
2. Combining multiple labeled regions into a whole-hippocampus mask.
3. Splitting multi-label masks into individual label masks.

These utilities are typically used after HSF segmentation and before
mesh generation or feature extraction steps in the pipeline.
"""

import os
import SimpleITK as sitk
import numpy as np
import nibabel as nib


def binarify_hd_mask(input_path, output_path):
    """
    Convert a fuzzy or probabilistic mask into a binary mask.

    The function thresholds the input mask at a fixed value (> 128),
    converting it into a binary (0/1) mask. Spatial metadata from the
    original image is preserved.

    Args:
        input_path (str): Path to the input mask image (e.g., NIfTI file).
        output_path (str): Path where the binary mask will be saved.

    Returns:
        None

    Notes:
        - Threshold is currently fixed at 128.
        - Output image is saved as unsigned 8-bit integer (uint8).
        - Spatial information (origin, spacing, direction) is preserved.
    """
    mask = sitk.ReadImage(input_path)
    mask_array = sitk.GetArrayFromImage(mask)

    binary_mask_array = (mask_array > 128).astype(np.uint8)
    binary_mask = sitk.GetImageFromArray(binary_mask_array)
    binary_mask.CopyInformation(mask)

    sitk.WriteImage(binary_mask, output_path)
    print(f"Saved binary mask into: {output_path}")


def combine_labels(input_path, output_path):
    """
    Combine all non-zero labels from a multi-label mask into a single mask.

    Any voxel with a value greater than zero is set to 1, resulting in a
    whole-structure binary mask. This is typically used to create a
    whole-hippocampus mask from subfield segmentations.

    Args:
        input_path (str): Path to the multi-label NIfTI mask file.
        output_path (str): Path where the combined binary mask will be saved.

    Returns:
        None

    Notes:
        - All labels > 0 are merged into a single region.
        - Output mask is stored as uint8.
        - Original affine and header information are preserved.
    """
    mask_nii = nib.load(input_path)
    mask_data = mask_nii.get_fdata()

    combined_mask = (mask_data > 0).astype(np.uint8)
    combined_nii = nib.Nifti1Image(
        combined_mask,
        affine=mask_nii.affine,
        header=mask_nii.header
    )

    nib.save(combined_nii, output_path)
    print(f"Combined mask saved to {output_path}")


def split_one_label(input_path, output_path, label):
    """
    Extract a single label from a multi-label mask.

    The function creates a binary mask where voxels matching the specified
    label are set to 1 and all others to 0.

    Args:
        input_path (str): Path to the multi-label NIfTI mask file.
        output_path (str): Path where the extracted binary mask will be saved.
        label (int or float): Label value to extract from the mask.

    Returns:
        None

    Notes:
        - Output mask is stored as uint8.
        - Affine and header information from the original image are preserved.
        - Useful for isolating specific hippocampal subfields
          (e.g., DG, CA1, CA2, CA3, SUB).
    """
    img = nib.load(input_path)
    data = img.get_fdata()

    mask = (data == label).astype(np.uint8)
    out_img = nib.Nifti1Image(mask, img.affine, img.header)

    nib.save(out_img, output_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NIfTI mask processing utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    split_parser = subparsers.add_parser("split", help="Extract a single label")
    split_parser.add_argument("--input", required=True, help="Input multi-label mask")
    split_parser.add_argument("--output", required=True, help="Output binary mask")
    split_parser.add_argument("--label", type=int, required=True, help="Label value")

    combine_parser = subparsers.add_parser("combine", help="Combine all labels")
    combine_parser.add_argument("--input", required=True, help="Input multi-label mask")
    combine_parser.add_argument("--output", required=True, help="Output combined mask")

    args = parser.parse_args()

    if args.command == "split":
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        split_one_label(args.input, args.output, args.label)
    elif args.command == "combine":
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        combine_labels(args.input, args.output)
