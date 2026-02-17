"""
HSF Segmentation Wrapper Script
Handles hippocampal segmentation using HSF (Hippocampal Segmentation Factory)
"""

import os, shutil, subprocess, sys
from datetime import datetime

def run_hsf_segmentation(
    input_t1w: str,
    output_seg: str,
    output_left_crop: str,
    output_right_crop: str,
    subject_anat_dir: str,
    output_dir: str,
    contrast: str,
    margin: int,
    seg_mode: str,
    ca_mode: str,
    hsf_left: str,
    hsf_right: str,
    hsf_left_crop: str,
    hsf_right_crop: str,
    subject: str,
    session: str,
    log_file: str
) -> None:
    """
    Run HSF segmentation with comprehensive logging and error handling.
    
    All parameters match the Snakemake rule params/wildcards exactly.
    """
    
    def log(message: str) -> None:
        """Write message to log file."""
        with open(log_file, 'a') as f:
            f.write(f"{message}\n")
    
    def log_timestamp(message: str) -> None:
        """Write timestamped message to log file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log(f"[{timestamp}] {message}")
    
    # Log start
    log_timestamp("Starting HSF segmentation")
    log(f"Subject: {subject}, Session: {session}")
    log(f"Input: {input_t1w}")
    
    # Verify input file exists
    if not os.path.isfile(input_t1w):
        log(f"ERROR: Input file not found: {input_t1w}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Run HSF segmentation
    log_timestamp("Running HSF...")
    hsf_command = [
        "hsf",
        f"files.path={subject_anat_dir}",
        "files.pattern=*T1w.nii.gz",
        f"roiloc.contrast={contrast}",
        f"roiloc.margin={margin}",
        f"segmentation={seg_mode}",
        f"segmentation.ca_mode={ca_mode}"
    ]
    log(f"Command: {' '.join(hsf_command)}")
    
    try:
        result = subprocess.run(
            hsf_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        log(result.stdout)
    except subprocess.CalledProcessError as e:
        log(f"ERROR: HSF command failed with exit code {e.returncode}")
        log(e.stdout)
        sys.exit(e.returncode)
    
    # HSF creates left and right hippocampus segmentations separately
    # Move them to derivatives directory
    if os.path.isfile(hsf_left) and os.path.isfile(hsf_right):
        # Move both segmentations to output directory
        left_target = os.path.join(output_dir, f"sub-{subject}_ses-{session}_left_hippocampus_seg.nii.gz")
        right_target = os.path.join(output_dir, f"sub-{subject}_ses-{session}_right_hippocampus_seg.nii.gz")
        
        os.rename(hsf_left, left_target)
        os.rename(hsf_right, right_target)
        
        # Copy cropped outputs if HSF produced them (stored under hsf_outputs by default)
        if os.path.isfile(hsf_left_crop):
            shutil.copy2(hsf_left_crop, output_left_crop)
            log(f"Saved left cropped segmentation: {output_left_crop}")
        else:
            log(f"ERROR: Left cropped segmentation not found: {hsf_left_crop}")
            sys.exit(1)
        
        if os.path.isfile(hsf_right_crop):
            shutil.copy2(hsf_right_crop, output_right_crop)
            log(f"Saved right cropped segmentation: {output_right_crop}")
        else:
            log(f"ERROR: Right cropped segmentation not found: {hsf_right_crop}")
            sys.exit(1)
        
        # Use one as the main output (or combine them if needed)
        shutil.copy2(left_target, output_seg)
        
        # Clean up hsf_outputs folder created by HSF in the input directory
        hsf_outputs_dir = os.path.join(subject_anat_dir, "hsf_outputs")
        if os.path.isdir(hsf_outputs_dir):
            try:
                shutil.rmtree(hsf_outputs_dir)
                log(f"Cleaned up temporary folder: {hsf_outputs_dir}")
            except Exception as e:
                log(f"WARNING: Could not remove hsf_outputs folder: {e}")
        
        log_timestamp("Segmentation completed successfully")
        log(f"Output: {output_seg}")
        log(f"Left hippocampus: {left_target}")
        log(f"Right hippocampus: {right_target}")
    else:
        log("ERROR: HSF outputs not found")
        log(f"Expected left: {hsf_left}")
        log(f"Expected right: {hsf_right}")
        
        # List directory contents for debugging
        try:
            dir_contents = subprocess.run(
                ["ls", "-la", subject_anat_dir],
                capture_output=True,
                text=True
            )
            log(dir_contents.stdout)
        except Exception as e:
            log(f"Could not list directory: {e}")
        
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="HSF Segmentation Wrapper")
    parser.add_argument("--input-t1w", required=True)
    parser.add_argument("--output-seg", required=True)
    parser.add_argument("--output-left-crop", required=True)
    parser.add_argument("--output-right-crop", required=True)
    parser.add_argument("--subject-anat-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--contrast", required=True)
    parser.add_argument("--margin", type=str, required=True)
    parser.add_argument("--seg-mode", required=True)
    parser.add_argument("--ca-mode", required=True)
    parser.add_argument("--hsf-left", required=True)
    parser.add_argument("--hsf-right", required=True)
    parser.add_argument("--hsf-left-crop", required=True)
    parser.add_argument("--hsf-right-crop", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--log-file", required=True)

    args = parser.parse_args()
    os.makedirs(os.path.dirname(args.log_file), exist_ok=True)

    run_hsf_segmentation(
        input_t1w=args.input_t1w,
        output_seg=args.output_seg,
        output_left_crop=args.output_left_crop,
        output_right_crop=args.output_right_crop,
        subject_anat_dir=args.subject_anat_dir,
        output_dir=args.output_dir,
        contrast=args.contrast,
        margin=args.margin,
        seg_mode=args.seg_mode,
        ca_mode=args.ca_mode,
        hsf_left=args.hsf_left,
        hsf_right=args.hsf_right,
        hsf_left_crop=args.hsf_left_crop,
        hsf_right_crop=args.hsf_right_crop,
        subject=args.subject,
        session=args.session,
        log_file=args.log_file,
    )
