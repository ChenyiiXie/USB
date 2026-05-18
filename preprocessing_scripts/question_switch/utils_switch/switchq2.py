#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q2question
Q2questionq2.1（Object 1）
switchq6.py
"""

import json
import re
import random
from camera_utils import generate_camera_view_template

def parse_speed_path_answer(answer):
    """，Object 1SPEEDPATH"""
    # 
    if not answer or answer.strip() == "":
        return None, None
    
    # ：Object 1: SPEED, PATH (types)
    patterns = [
        r'Object 1:\s*(\w+),\s*(\w+)',  # 
        r'<DYNAMIC OBJECTS>Object 1:\s*(\w+),\s*(\w+)',  # 
        r'Object 1:\s*(\w+),\s*(\w+)\n',  # 
    ]
    
    for pattern in patterns:
        match = re.search(pattern, answer, re.MULTILINE)
        if match:
            speed = match.group(1).strip()
            path = match.group(2).strip()
            return speed, path
    
    return None, None

def extract_object1_from_question(question):
    """questionObject 1"""
    # : Object 1: type, distance meters ahead, offset meters to the direction, speed of X m/s
    pattern = r'Object 1:\s*([^,]+),\s*(\d+)\s*meters\s*ahead,\s*(\d+)\s*meters\s*to\s*the\s*(left|right),\s*speed\s*of\s*(\d+)\s*m/s\.'
    
    match = re.search(pattern, question, re.IGNORECASE)
    if match:
        obj_type, distance, offset, direction, speed = match.groups()
        return {
            'type': obj_type.strip(),
            'distance': int(distance),
            'offset': int(offset),
            'direction': direction.strip(),
            'speed': int(speed)
        }
    return None

def generate_distractor_options(correct_speed, correct_path):
    """Generate3"""
    all_speeds = ['KEEP', 'ACCELERATE', 'DECELERATE', 'STOP']
    all_paths = ['STRAIGHT', 'RIGHT_CHANGE', 'LEFT_CHANGE', 'RIGHT_TURN', 'LEFT_TURN']
    
    distractors = []
    
    # 1: PATH，SPEED
    if correct_speed in all_speeds:
        other_speeds = [s for s in all_speeds if s != correct_speed]
        for speed in other_speeds[:2]:  # 2
            distractors.append((speed, correct_path))
    
    # 2: SPEED，PATH
    if correct_path in all_paths:
        other_paths = [p for p in all_paths if p != correct_path]
        for path in other_paths[:1]:  # 1
            distractors.append((correct_speed, path))
    
    # 3: 
    if len(distractors) < 3:
        combinations = [
            ('STOP', 'STRAIGHT'),
            ('DECELERATE', 'STRAIGHT'),
            ('KEEP', 'LEFT_TURN'),
            ('ACCELERATE', 'RIGHT_TURN'),
        ]
        for combo in combinations:
            if combo != (correct_speed, correct_path) and combo not in distractors:
                distractors.append(combo)
                if len(distractors) >= 3:
                    break
    
    # 3
    while len(distractors) < 3:
        speed = random.choice(all_speeds)
        path = random.choice(all_paths)
        if (speed, path) != (correct_speed, correct_path) and (speed, path) not in distractors:
            distractors.append((speed, path))
    
    return distractors[:3]

def convert_q2_to_q2_1(entry):
    """q2q2.1，Object 1，object"""
    if entry.get('question_type') != 'q2':
        return entry
    
    # empty question
    if not entry.get('question') or not entry.get('answer') or entry.get('question').strip() == "" or entry.get('answer').strip() == "":
        print(f": Skipempty question")
        return entry
    
    # ，Object 1
    original_answer = entry['answer']
    correct_speed, correct_path = parse_speed_path_answer(original_answer)
    
    if not correct_speed or not correct_path:
        print(f": Object 1 - {original_answer}")
        return entry
    
    # Object 1
    obj1_info = extract_object1_from_question(entry['question'])
    if not obj1_info:
        print(f": Object 1")
        return entry
    
    # Generate
    distractors = generate_distractor_options(correct_speed, correct_path)
    
    # 4（）
    options = [(correct_speed, correct_path)] + distractors
    random.shuffle(options)  # 
    
    # Found
    correct_index = options.index((correct_speed, correct_path))
    correct_letter = chr(65 + correct_index)  # A=65, B=66, C=67, D=68
    
    # questionobject，Object 1
    original_question = entry['question']
    
    # image
    image_paths = entry.get('image_path', {})
    
    # Generate
    camera_template = generate_camera_view_template(image_paths)
    
    # question，objectObject 1
    new_question = (
        camera_template + "\n"
        "You are driving, and I will now provide you with the location and velocity information of dynamic objects in the front view image. "
        "Please predict the future driving behavior of Object 1 only, which can be divided into SPEED decisions and PATH decisions. "
        "SPEED includes KEEP, ACCELERATE, DECELERATE, and STOP, while PATH includes STRAIGHT, RIGHT_CHANGE, LEFT_CHANGE, RIGHT_TURN, and LEFT_TURN.\n\n"
        "I will now provide you with the position and velocity information of the dynamic objects:\n"
    )
    
    # object
    object_lines = []
    lines = original_question.split('\n')
    for line in lines:
        if line.strip().startswith('Object ') and 'meters ahead' in line:
            object_lines.append(line.strip())
    
    # object
    for obj_line in object_lines:
        new_question += obj_line + "\n"
    
    # 
    new_question += "\nPlease predict the future driving behavior of Object 1 only. Please select the most likely behavior:\n\n"
    for i, (speed, path) in enumerate(options):
        letter = chr(65 + i)
        new_question += f"{letter}. {speed}, {path}\n"
    new_question += (
        "\nInstructions:\n"
        "- Analyze the current situation and Object 1's position, speed, and trajectory\n"
        "- Consider traffic rules, road conditions, and other vehicles\n"
        "- Select the most appropriate SPEED and PATH combination for Object 1\n"
        "- Provide only the letter of your choice\n"
        "Your answer (provide only the letter):"
    )
    
    # 
    new_entry = entry.copy()
    new_entry['question'] = new_question
    new_entry['answer'] = correct_letter
    new_entry['question_type'] = 'q2.1'
    new_entry['object_info'] = obj1_info
    new_entry['correct_answer'] = f"{correct_speed}, {correct_path}"
    
    return new_entry

def main():
    # ，main_converter.py
    print("：main_converter.py，")
    print(": python3 preprocessing_scripts/question_switch/utils_switch/main_converter.py")

if __name__ == "__main__":
    main()