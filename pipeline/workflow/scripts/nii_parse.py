import os
import SimpleITK as sitk
import numpy as np
import nibabel as nib

#turns the fuzzy mask into a binary mask
def binarify_hd_mask(input_path, output_path):
    mask = sitk.ReadImage(input_path)
    mask_array = sitk.GetArrayFromImage(mask)
    #probably we should do some experimentation with this number, maybe with the test-retest method?
    binary_mask_array = (mask_array > 128).astype(np.uint8)
    binary_mask = sitk.GetImageFromArray(binary_mask_array)
    binary_mask.CopyInformation(mask)
    sitk.WriteImage(binary_mask, output_path)
    print(f"Saved binary mask into: {output_path}")

#combines all the labels from a hsf nii mask into a single mask for whole hippocampus analysis
def combine_labels(input_path, output_path):
    mask_nii = nib.load(input_path)
    mask_data = mask_nii.get_fdata()
    combined_mask = (mask_data > 0).astype(np.uint8)
    combined_nii = nib.Nifti1Image(combined_mask, affine=mask_nii.affine, header=mask_nii.header)
    nib.save(combined_nii, output_path)
    print(f"Combined mask saved to {output_path}")

#splits label from masks into separe one label masks
def split_one_label(input_path, output_path, label):
    img = nib.load(input_path)
    data = img.get_fdata()
    mask = (data == label).astype(np.uint8)
    out_img = nib.Nifti1Image(mask, img.affine, img.header)
    nib.save(out_img, output_path)
