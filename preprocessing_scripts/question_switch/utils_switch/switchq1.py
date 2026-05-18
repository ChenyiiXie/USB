#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q1question
Q1question：
1. （）
2. 
"""

import re
import random
from typing import Dict, List, Any
from camera_utils import generate_camera_view_template

def extract_vru_info(answer: str) -> Dict[str, Any]:
    """
    Q1VRU
    """
    vru_info = {
        'bicycles': False,
        'motorcycles': False,
        'pedestrians': False,
        'locations': [],
        'has_vru': False
    }
    
    # 
    answer_lower = answer.lower()
    
    # "No"
    if answer_lower.startswith('no') or 'no,' in answer_lower or 'don\'t see' in answer_lower:
        return vru_info  # VRU
    
    # VRU
    if 'bicycle' in answer_lower or 'cyclist' in answer_lower:
        vru_info['bicycles'] = True
        vru_info['has_vru'] = True
    if 'motorcycle' in answer_lower or 'motorcyclist' in answer_lower:
        vru_info['motorcycles'] = True
        vru_info['has_vru'] = True
    if 'pedestrian' in answer_lower:
        vru_info['pedestrians'] = True
        vru_info['has_vru'] = True
    
    # 
    if 'left' in answer_lower:
        vru_info['locations'].append('left')
    if 'right' in answer_lower:
        vru_info['locations'].append('right')
    if 'front' in answer_lower or 'ahead' in answer_lower:
        vru_info['locations'].append('front')
    if 'back' in answer_lower or 'behind' in answer_lower:
        vru_info['locations'].append('back')
    
    return vru_info

def create_q1_type_question(original_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Q1
    """
    # image
    image_paths = original_data.get('image_path', {})
    
    # Generate（<image>）
    camera_template = generate_camera_view_template(image_paths)
    
    # 
    option_texts = [
        'Bicycles/Cyclists',
        'Motorcycles/Motorcyclists',
        'Pedestrians',
        'No VRU detected',
    ]
    random.shuffle(option_texts)
    
    # 
    original_answer = original_data.get('answer', '')
    vru_info = extract_vru_info(original_answer)
    
    # 
    correct_option_texts = set()
    if vru_info['has_vru']:
        if vru_info['bicycles']:
            correct_option_texts.add('Bicycles/Cyclists')
        if vru_info['motorcycles']:
            correct_option_texts.add('Motorcycles/Motorcyclists')
        if vru_info['pedestrians']:
            correct_option_texts.add('Pedestrians')
    else:
        correct_option_texts.add('No VRU detected')

    # 
    correct_letters = []
    for i, text in enumerate(option_texts):
        if text in correct_option_texts:
            correct_letters.append(chr(65 + i))
    answer = ', '.join(correct_letters)

    # question（）
    question = (
        f"{camera_template}\n\n"
        "Question: Do you see any vulnerable road users (VRUs) within 20 meters ahead of the vehicle?\n\n"
        "Please select ALL applicable options from the following choices:\n\n"
    )
    for i, text in enumerate(option_texts):
        question += f"{chr(65 + i)}. {text}\n"
    question += (
        "\nInstructions:\n"
        "- Look carefully at each camera view\n"
        "- Identify any vulnerable road users within 20 meters\n"
        "Your answer (provide only the letter(s)):"
    )
    
    # 
    converted_data = original_data.copy()
    converted_data.update({
        'question': question,
        'answer': answer,
        'correct_answer': answer,
        'question_type': 'q1.1',  # Q1question
        'original_question_type': 'q1'
    })
    
    return converted_data

def create_q1_location_question(original_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Q1
    """
    # image
    image_paths = original_data.get('image_path', {})
    
    # Generate（<image>）
    camera_template = generate_camera_view_template(image_paths)
    
    # 
    option_texts = [
        'Left side (left front, left, left back)',
        'Right side (right front, right, right back)',
        'Directly ahead/center',
        'Multiple locations',
        'No VRU detected',
    ]
    random.shuffle(option_texts)
    
    # （，“left front”）
    original_answer = original_data.get('answer', '')
    vru_info = extract_vru_info(original_answer)

    if not vru_info['has_vru']:
        correct_text = 'No VRU detected'
    else:
        ans_lower = original_answer.lower()
        has_left = 'left' in ans_lower
        has_right = 'right' in ans_lower
        # not found，front/center
        has_center = ('front' in ans_lower or 'ahead' in ans_lower or 'center' in ans_lower) and not (has_left or has_right)
        # VRU（pedestrian/cyclist/bicyclist/motorcyclist/motorcycle）
        vru_mentions = re.findall(r"\b(pedestrian|pedestrians|cyclist|cyclists|bicyclist|bicyclists|bicycle|bicycles|motorcyclist|motorcyclists|motorcycle|motorcycles)\b", ans_lower)
        vru_count = len(vru_mentions)

        presence_count = sum([has_left, has_right, has_center])
        if presence_count == 0:
            correct_text = 'No VRU detected'
        elif presence_count > 1:
            correct_text = 'Multiple locations'
        else:
            # ，toVRU，“”
            if vru_count >= 2:
                correct_text = 'Multiple locations'
            else:
                if has_left:
                    correct_text = 'Left side (left front, left, left back)'
                elif has_right:
                    correct_text = 'Right side (right front, right, right back)'
                else:
                    correct_text = 'Directly ahead/center'

    # 
    correct_index = option_texts.index(correct_text)
    answer = chr(65 + correct_index)

    # question（）
    question = (
        f"{camera_template}\n\n"
        "Question: Where are the vulnerable road users (pedestrians/cyclists/motorcyclists) "
        "located relative to your vehicle?\n\n"
        "Please select the most appropriate option:\n\n"
    )
    for i, text in enumerate(option_texts):
        question += f"{chr(65 + i)}. {text}\n"
    question += (
        "\nInstructions:\n"
        "- Look carefully at each camera view\n"
        "- Determine the primary location of vulnerable road users\n"
        "- If VRUs are in multiple distinct areas, select \"Multiple locations\"\n"
        "- If no VRUs are visible, select \"No VRU detected\"\n\n"
        "Your answer (provide only the letter):"
    )
    
    # 
    converted_data = original_data.copy()
    converted_data.update({
        'question': question,
        'answer': answer,
        'correct_answer': correct_text,
        'question_type': 'q1.2',  # Q1question
        'original_question_type': 'q1'
    })
    
    return converted_data

def convert_q1_questions(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Q1question
    """
    converted_questions = []
    
    # question
    type_question = create_q1_type_question(data)
    converted_questions.append(type_question)
    
    # question
    location_question = create_q1_location_question(data)
    converted_questions.append(location_question)
    
    return converted_questions

def test_q1_conversion():
    """
    Q1
    """
    # 
    test_data = {
        'question': 'Do you see any vulnerable road users within 20 meters ahead?',
        'answer': 'Yes, I can see pedestrians on the left side and cyclists ahead.',
        'question_type': 'q1',
        'scene_token': 'test_scene',
        'frame_token': 'test_frame'
    }
    
    print("=== Q1 ===")
    print(f"question: {test_data['question']}")
    print(f": {test_data['answer']}")
    print()
    
    converted_questions = convert_q1_questions(test_data)
    
    for i, question in enumerate(converted_questions, 1):
        print(f"question {i}:")
        print(f"question: {question['question_type']}")
        print(f"question: {question['question']}")
        print(f": {question['answer']}")
        print(f": {question['correct_answer']}")
        print()

if __name__ == '__main__':
    test_q1_conversion()
