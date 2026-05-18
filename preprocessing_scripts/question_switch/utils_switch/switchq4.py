#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q4question
Q4question
"""

import os
import sys
import json
import argparse
import random
from typing import List, Dict, Any
from camera_utils import generate_camera_view_template


def generate_q4_question(image_paths: Dict[str, str]) -> str:
    """
    GenerateQ4question，imageGenerate
    """
    # Generate（<image>）
    camera_template = generate_camera_view_template(image_paths)
    
    return (
        f"{camera_template}\n\n"
        "Question: Given the provided multi-view camera images from a car's perspective, "
        "identify if there is a traffic light that affects the car's behavior.\n\n"
        "Please select the most likely traffic light state:\n\n"
        "A. Red\n"
        "B. Green\n"
        "C. Yellow\n"
        "D. None\n\n"
        "Instructions:\n"
        "- Look carefully at the front view and surrounding camera views\n"
        "- Identify any traffic lights visible in the images\n"
        "- Determine the current state of the traffic light\n"
        "- If no traffic light is visible, select \"D\"\n"
        "- Provide only the letter of your choice\n"
        "Your answer (provide only the letter):"
    )

WORD_TO_OPTION = {
    "red": "A",
    "green": "B",
    "yellow": "C",
    "none": "D",
}


def normalize_answer(text: str) -> str:
    if text is None:
        return ""
    return str(text).strip().lower()


def convert_q4_item(item: Dict) -> bool:
    """ q4 sample；success。"""
    original_answer = item.get("answer", "")
    norm = normalize_answer(original_answer)

    option = WORD_TO_OPTION.get(norm)
    if not option:
        # （）
        if "red" in norm:
            option = "A"
        elif "green" in norm:
            option = "B"
        elif "yellow" in norm:
            option = "C"
        elif "none" in norm:
            option = "D"
        else:
            return False

    # imageGeneratequestion
    image_paths = item.get('image_path', {})
    item["question"] = generate_q4_question(image_paths)
    item["answer"] = option
    return True

def convert_q4_to_multiple_choice(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Q4question
    main_converter.py
    """
    converted_data = data.copy()

    # to
    original_answer = (data.get('answer', '') or '').lower()
    if 'red' in original_answer:
        correct_text = 'Red'
    elif 'green' in original_answer:
        correct_text = 'Green'
    elif 'yellow' in original_answer:
        correct_text = 'Yellow'
    else:
        correct_text = 'None'

    # ，
    option_texts = ['Red', 'Green', 'Yellow', 'None']
    random.shuffle(option_texts)
    correct_index = option_texts.index(correct_text)
    correct_letter = chr(65 + correct_index)

    # Generatequestion
    image_paths = data.get('image_path', {})
    camera_template = generate_camera_view_template(image_paths)
    question = (
        f"{camera_template}\n\n"
        "Question: Given the provided multi-view camera images from a car's perspective, "
        "identify if there is a traffic light that affects the car's behavior.\n\n"
        "Please select the most likely traffic light state:\n\n"
    )

    # 
    for i, text in enumerate(option_texts):
        question += f"{chr(65 + i)}. {text}\n"
    question += (
        "\nInstructions:\n"
        "- Look carefully at the front view and surrounding camera views\n"
        "- Identify any traffic lights visible in the images\n"
        "- Determine the current state of the traffic light\n"
        "- If no traffic light is visible, select the option meaning \"None\"\n"
        "- Provide only the letter of your choice\n"
        "Your answer (provide only the letter):"
    )

    converted_data['question'] = question
    converted_data['answer'] = correct_letter
    converted_data['correct_answer'] = correct_text

    return converted_data


def process_file(input_path: str, output_path: str) -> None:
    if not os.path.exists(input_path):
        print(f"：not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("：JSON ")
        sys.exit(1)

    total = len(data)
    q4_total = 0
    q4_updated = 0
    q4_failed = 0

    for item in data:
        if isinstance(item, dict) and item.get("question_type") == "q4":
            q4_total += 1
            ok = convert_q4_item(item)
            if ok:
                q4_updated += 1
            else:
                q4_failed += 1

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("ProcessingDone：")
    print(f"  sample: {total}")
    print(f"  q4 sample: {q4_total}")
    print(f"  success: {q4_updated}")
    print(f"  （Skip）: {q4_failed}")
    print(f"  : {output_path}")


def main():
    # ，main_converter.py
    print("：main_converter.py，")
    print(": python3 preprocessing_scripts/question_switch/utils_switch/main_converter.py")


if __name__ == "__main__":
    main()


