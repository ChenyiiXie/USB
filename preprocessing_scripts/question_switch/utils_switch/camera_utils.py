#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

imageGenerate
"""

from typing import Dict, List, Optional

# 
CAMERA_VIEW_MAPPING = {
    'CAM_FRONT': 'FRONT VIEW',
    'CAM_FRONT_LEFT': 'FRONT LEFT VIEW', 
    'CAM_FRONT_RIGHT': 'FRONT RIGHT VIEW',
    'CAM_BACK_LEFT': 'BACK LEFT VIEW',
    'CAM_BACK_RIGHT': 'BACK RIGHT VIEW',
    'CAM_BACK': 'BACK VIEW'
}

# （：→→，→→）
CAMERA_ORDER = [
    'CAM_FRONT',
    'CAM_FRONT_RIGHT',
    'CAM_FRONT_LEFT',
    'CAM_BACK',
    'CAM_BACK_RIGHT',
    'CAM_BACK_LEFT'
]

def get_available_cameras(image_paths: Dict[str, str]) -> List[str]:
    """
    image_paths
    
    Args:
        image_paths: image
        
    Returns:
        
    """
    if not image_paths:
        return []
    
    available_cameras = []
    for camera in CAMERA_ORDER:
        if camera in image_paths and image_paths[camera]:
            available_cameras.append(camera)
    
    return available_cameras

def generate_camera_view_template(image_paths: Dict[str, str], 
                                prefix: str = "") -> str:
    """
    imageGenerate
    
    Args:
        image_paths: image
        prefix: 
        
    Returns:
        Generate
    """
    if not image_paths:
        return ""
    
    available_cameras = get_available_cameras(image_paths)
    
    if not available_cameras:
        return ""
    
    # image，：
    # <CAM_FRONT>:
    # <image>
    template_parts = []
    for camera in available_cameras:
        template_parts.append(f"<{camera}>:")
        template_parts.append("<image>")
    
    return "\n".join(template_parts)

def generate_camera_view_template_for_waypoints(image_paths: Dict[str, str], 
                                               prefix: str = "") -> str:
    """
    questionGenerate
    
    Args:
        image_paths: image
        prefix: 
        
    Returns:
        Generate
    """
    return generate_camera_view_template(image_paths, prefix)

def generate_camera_view_template_for_traffic_lights(image_paths: Dict[str, str], 
                                                   prefix: str = "") -> str:
    """
    questionGenerate
    
    Args:
        image_paths: image
        prefix: 
        
    Returns:
        Generate
    """
    return generate_camera_view_template(image_paths, prefix)

def has_camera_view(image_paths: Dict[str, str], camera: str) -> bool:
    """
    
    
    Args:
        image_paths: image
        camera: 
        
    Returns:
        
    """
    return camera in image_paths and image_paths[camera]

def get_camera_count(image_paths: Dict[str, str]) -> int:
    """
    
    
    Args:
        image_paths: image
        
    Returns:
        
    """
    return len(get_available_cameras(image_paths))
