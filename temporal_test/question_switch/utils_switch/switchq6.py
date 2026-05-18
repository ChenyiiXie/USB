#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert temporal Q6 into front-only history multiple-choice format."""

import re
import random
from camera_utils import generate_camera_view_template


random.seed(42)


def parse_speed_path_answer(answer):
    """ Q6 """
    match = re.search(r"<SPEED PATH PLAN>(\w+),\s*(\w+)", answer)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


def extract_navigation_and_speed(question):
    """"""
    speed_match = re.search(r"current speed is (\d+) m/s", question)
    speed = int(speed_match.group(1)) if speed_match else 0

    nav_match = re.search(r"navigation command is '([^']+)'", question)
    navigation = nav_match.group(1) if nav_match else "go straight"

    return speed, navigation


def generate_distractor_options(correct_speed, correct_path, navigation):
    """Generate"""
    all_speeds = ["KEEP", "ACCELERATE", "DECELERATE", "STOP"]
    distractors = []

    for speed in all_speeds:
        if speed != correct_speed:
            distractors.append((speed, correct_path))
        if len(distractors) >= 2:
            break

    if "left" in navigation.lower():
        preferred_paths = ["LEFT_TURN", "LEFT_CHANGE", "STRAIGHT", "RIGHT_CHANGE"]
    elif "right" in navigation.lower():
        preferred_paths = ["RIGHT_TURN", "RIGHT_CHANGE", "STRAIGHT", "LEFT_CHANGE"]
    else:
        preferred_paths = ["STRAIGHT", "LEFT_CHANGE", "RIGHT_CHANGE", "LEFT_TURN"]

    for path in preferred_paths:
        if path != correct_path:
            distractors.append((correct_speed, path))
            break

    while len(distractors) < 3:
        candidate = (random.choice(all_speeds), random.choice(preferred_paths))
        if candidate != (correct_speed, correct_path) and candidate not in distractors:
            distractors.append(candidate)

    return distractors[:3]


def convert_q6_temporal_to_multiple_choice(entry):
    """ temporal Q6 """
    if entry.get("question_type") != "q6":
        return entry

    correct_speed, correct_path = parse_speed_path_answer(entry.get("answer", ""))
    if not correct_speed or not correct_path:
        return entry

    current_speed, navigation = extract_navigation_and_speed(entry.get("question", ""))
    distractors = generate_distractor_options(correct_speed, correct_path, navigation)
    options = [(correct_speed, correct_path)] + distractors
    random.shuffle(options)

    correct_index = options.index((correct_speed, correct_path))
    correct_letter = chr(65 + correct_index)

    image_paths = entry.get("image_path", {})
    camera_template = generate_camera_view_template(image_paths)
    frame_count = entry.get("frame_count", 1)

    question_parts = [
        camera_template,
        "",
        (
            f"You are driving. The provided front-view image sequence corresponds to a controlled temporal "
            f"setting with {frame_count} frame(s), ordered from older frames to the latest observed frame t-1."
        ),
        f"Your current speed in the latest observed frame t-1 is {current_speed} m/s, and the navigation command is '{navigation}'.",
        "Based on the temporal visual context and the latest-observed-frame driving state, what is your plan for the next three seconds?",
        "Please answer your SPEED plan and your PATH plan.",
        "SPEED includes KEEP, ACCELERATE, DECELERATE, and STOP.",
        "PATH includes STRAIGHT, RIGHT_CHANGE, LEFT_CHANGE, RIGHT_TURN, and LEFT_TURN.",
        "",
        "Please select the most appropriate SPEED and PATH plan for your vehicle:",
        "",
    ]

    for index, (speed, path) in enumerate(options):
        letter = chr(65 + index)
        question_parts.append(f"{letter}. {speed}, {path}")

    question_parts.extend(
        [
            "",
            "Instructions:",
            "- Use the temporal image sequence as supporting context",
            "- Consider the latest observed speed, navigation command, and traffic conditions",
            "- Select the most appropriate driving plan for the next few seconds",
            "- Provide only the letter of your choice",
            "Your answer (provide only the letter):",
        ]
    )

    new_entry = entry.copy()
    new_entry["question"] = "\n".join(question_parts).strip()
    new_entry["answer"] = correct_letter
    new_entry["correct_answer"] = f"{correct_speed}, {correct_path}"
    return new_entry
