"""This module defines helper functions used by the Snakefile workflow. These functions
standardize file path construction, subject/session discovery, and
batch handling for BIDS-compliant datasets."""


def discover_subjects():
    """
    Discover subjects and sessions from a BIDS dataset.

    Uses a BIDS glob pattern to locate T1-weighted files, extracts
    subject and session identifiers, applies optional filtering
    by subject, and optionally slices the dataset for batch processing.

    Returns
    -------
    subjects : list[str]
        List of subject IDs to process.
    sessions : list[str]
        Corresponding list of session IDs.
    subject_session_pairs : list[tuple[str, str]]
        List of (subject, session) pairs selected for processing.

    Raises
    ------
    ValueError
        If subject filtering is applied but no matches are found.
    """
    ...


def get_input_path(subject, session):
    """
    Construct the input T1-weighted file path for a given subject and session.

    Parameters
    ----------
    subject : str
        Subject identifier (e.g., "01").
    session : str
        Session identifier (e.g., "ses-1").

    Returns
    -------
    str
        Full path to the T1w NIfTI file in the BIDS dataset.
    """
    ...


def hsf_output(subject, session):
    """
    Path to the combined HSF segmentation output.

    Parameters
    ----------
    subject : str
        Subject identifier.
    session : str
        Session identifier.

    Returns
    -------
    str
        Full path to the combined hippocampal segmentation NIfTI.
    """
    ...


def hsf_left_crop_output(subject, session):
    """
    Path to the left hemisphere cropped HSF segmentation.

    Parameters
    ----------
    subject : str
        Subject identifier.
    session : str
        Session identifier.

    Returns
    -------
    str
        Full path to the left hemisphere cropped segmentation NIfTI.
    """
    ...


def hsf_right_crop_output(subject, session):
    """
    Path to the right hemisphere cropped HSF segmentation.

    Parameters
    ----------
    subject : str
        Subject identifier.
    session : str
        Session identifier.

    Returns
    -------
    str
        Full path to the right hemisphere cropped segmentation NIfTI.
    """
    ...


def get_seg_crop_output(subject, session, hemi):
    """
    Path to a hemisphere-specific cropped segmentation.

    Parameters
    ----------
    subject : str
        Subject identifier.
    session : str
        Session identifier.
    hemi : str
        Hemisphere code, typically 'L' or 'R'.

    Returns
    -------
    str
        Full path to the cropped segmentation NIfTI for the given hemisphere.
    """
    ...


def label_mask_output(subject, session, hemi, label):
    """
    Path to the per-label hippocampus mask for a given hemisphere.

    Parameters
    ----------
    subject : str
        Subject identifier.
    session : str
        Session identifier.
    hemi : str
        Hemisphere code ('L' or 'R').
    label : str
        Label name or number.

    Returns
    -------
    str
        Full path to the per-label mask NIfTI file.
    """
    ...


def combined_mask_output(subject, session, hemi):
    """
    Path to the combined hippocampus mask for a given hemisphere.

    Parameters
    ----------
    subject : str
        Subject identifier.
    session : str
        Session identifier.
    hemi : str
        Hemisphere code ('L' or 'R').

    Returns
    -------
    str
        Full path to the combined hippocampus mask NIfTI file.
    """
