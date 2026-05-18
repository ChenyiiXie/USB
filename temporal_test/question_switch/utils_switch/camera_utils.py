#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Temporal camera utilities for front-only history prompts."""

import re
from typing import Dict, List, Tuple


CAMERA_ORDER = ["CAM_FRONT"]


def parse_temporal_camera_key(camera_key: str) -> Tuple[int, str]:
    """
     temporal 

    Example:
    - T_MINUS_1_CAM_FRONT -> (-1, CAM_FRONT)
    - T_MINUS_10_CAM_FRONT -> (-10, CAM_FRONT)
    """
    if camera_key.startswith("T_MINUS_"):
        match = re.match(r"T_MINUS_(\d+)_(CAM_[A-Z_]+)$", camera_key)
        if match:
            return -int(match.group(1)), match.group(2)
    return 0, camera_key


def get_available_cameras(image_paths: Dict[str, str]) -> List[str]:
    """、"""
    if not image_paths:
        return []

    sorted_keys = sorted(
        image_paths.keys(),
        key=lambda key: (
            parse_temporal_camera_key(key)[0],
            CAMERA_ORDER.index(parse_temporal_camera_key(key)[1])
            if parse_temporal_camera_key(key)[1] in CAMERA_ORDER else len(CAMERA_ORDER),
            key,
        ),
    )
    return [key for key in sorted_keys if image_paths.get(key)]


def format_camera_label(camera_key: str) -> str:
    """ temporal """
    return f"<{camera_key}>:"


def generate_camera_view_template(image_paths: Dict[str, str], prefix: str = "") -> str:
    """Generate temporal """
    if not image_paths:
        return ""

    available_cameras = get_available_cameras(image_paths)
    if not available_cameras:
        return ""

    template_parts: List[str] = []
    for camera_key in available_cameras:
        template_parts.append(format_camera_label(camera_key))
        template_parts.append("<image>")
    return "\n".join(template_parts)
