#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert temporal Q2 into front-only history multiple-choice format."""

import re
import random
from camera_utils import generate_camera_view_template


random.seed(42)


def parse_speed_path_answer(answer):
    """ Q2 ， Object 1 SPEED / PATH"""
    patterns = [
        r"Object 1:\s*(\w+),\s*(\w+)",
        r"<DYNAMIC OBJECTS>Object 1:\s*(\w+),\s*(\w+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, answer, re.MULTILINE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
    return None, None


def extract_object1_from_question(question):
    """question Object 1 """
    pattern = (
        r"Object 1:\s*([^,]+),\s*(\d+)\s*meters\s*ahead,\s*(\d+)\s*meters\s*to\s*the\s*"
        r"(left|right),\s*speed\s*of\s*(\d+)\s*m/s\."
    )
    match = re.search(pattern, question, re.IGNORECASE)
    if not match:
        return None
    obj_type, distance, offset, direction, speed = match.groups()
    return {
        "type": obj_type.strip(),
        "distance": int(distance),
        "offset": int(offset),
        "direction": direction.strip(),
        "speed": int(speed),
    }


def generate_distractor_options(correct_speed, correct_path):
    """Generate"""
    all_speeds = ["KEEP", "ACCELERATE", "DECELERATE", "STOP"]
    all_paths = ["STRAIGHT", "RIGHT_CHANGE", "LEFT_CHANGE", "RIGHT_TURN", "LEFT_TURN"]

    distractors = []

    for speed in all_speeds:
        if speed != correct_speed:
            distractors.append((speed, correct_path))
        if len(distractors) >= 2:
            break

    for path in all_paths:
        if path != correct_path:
            distractors.append((correct_speed, path))
            break

    while len(distractors) < 3:
        speed = random.choice(all_speeds)
        path = random.choice(all_paths)
        candidate = (speed, path)
        if candidate != (correct_speed, correct_path) and candidate not in distractors:
            distractors.append(candidate)

    return distractors[:3]


def convert_q2_temporal_to_multiple_choice(entry):
    """ temporal Q2 """
    if entry.get("question_type") != "q2":
        return entry

    correct_speed, correct_path = parse_speed_path_answer(entry.get("answer", ""))
    object_info = extract_object1_from_question(entry.get("question", ""))
    if not correct_speed or not correct_path or not object_info:
        return entry

    distractors = generate_distractor_options(correct_speed, correct_path)
    options = [(correct_speed, correct_path)] + distractors
    random.shuffle(options)

    correct_index = options.index((correct_speed, correct_path))
    correct_letter = chr(65 + correct_index)

    image_paths = entry.get("image_path", {})
    camera_template = generate_camera_view_template(image_paths)

    object_lines = []
    for line in entry.get("question", "").split("\n"):
        if line.strip().startswith("Object ") and "meters ahead" in line:
            object_lines.append(line.strip())

    frame_count = entry.get("frame_count", 1)

    question_parts = [
        camera_template,
        "",
        (
            f"You are driving. The provided front-view image sequence corresponds to a controlled temporal "
            f"setting with {frame_count} frame(s), ordered from older frames to the latest observed frame t-1."
        ),
        "Please predict the future driving behavior of Object 1 only, which can be divided into SPEED decisions and PATH decisions.",
        "SPEED includes KEEP, ACCELERATE, DECELERATE, and STOP, while PATH includes STRAIGHT, RIGHT_CHANGE, LEFT_CHANGE, RIGHT_TURN, and LEFT_TURN.",
        "",
        "I will now provide you with the position and velocity information of the dynamic objects in the latest observed frame t-1:",
    ]

    question_parts.extend(object_lines)
    question_parts.append("")
    question_parts.append("Please predict the future driving behavior of Object 1 only. Please select the most likely behavior:")
    question_parts.append("")

    for index, (speed, path) in enumerate(options):
        letter = chr(65 + index)
        question_parts.append(f"{letter}. {speed}, {path}")

    question_parts.extend(
        [
            "",
            "Instructions:",
            "- Use the temporal image sequence as supporting context",
            "- Focus on Object 1 in the latest observed frame t-1",
            "- Select the most appropriate SPEED and PATH combination for Object 1",
            "- Provide only the letter of your choice",
            "Your answer (provide only the letter):",
        ]
    )

    new_entry = entry.copy()
    new_entry["question"] = "\n".join(question_parts).strip()
    new_entry["answer"] = correct_letter
    new_entry["question_type"] = "q2.1"
    new_entry["correct_answer"] = f"{correct_speed}, {correct_path}"
    return new_entry
