#!/usr/bin/env python3
"""Helper to get camera index from symlink."""

import os
import re


def get_camera_index_from_symlink(symlink_path="/dev/videostereo"):
    """
    Get the camera index number from a video device symlink.
    
    Args:
        symlink_path: Path to the symlink (default: /dev/videostereo)
        
    Returns:
        int: Camera index number, or None if not found
        
    Example:
        >>> get_camera_index_from_symlink("/dev/videostereo")
        4  # if /dev/videostereo -> video4
    """
    try:
        # Read the symlink target
        target = os.readlink(symlink_path)
        
        # Extract number from videoN format
        match = re.search(r'video(\d+)', target)
        if match:
            return int(match.group(1))
        
        # If target is absolute path like /dev/video4
        match = re.search(r'/dev/video(\d+)', target)
        if match:
            return int(match.group(1))
            
    except (OSError, FileNotFoundError) as e:
        print(f"Error reading symlink {symlink_path}: {e}")
        
    return None


if __name__ == "__main__":
    index = get_camera_index_from_symlink()
    if index is not None:
        print(f"Camera index: {index}")
        print(f"Use cv2.VideoCapture({index})")
    else:
        print("Could not determine camera index")
