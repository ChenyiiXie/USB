import json
import re
import random
from typing import Dict, List, Any
from camera_utils import generate_camera_view_template

def parse_speed_path_answer(answer):
    """，SPEEDPATH"""
    # ：<SPEED PATH PLAN>SPEED, PATH</SPEED PATH PLAN>
    match = re.search(r'<SPEED PATH PLAN>(\w+),\s*(\w+)', answer)
    if match:
        speed = match.group(1).strip()
        path = match.group(2).strip()
        return speed, path
    return None, None

def extract_navigation_and_speed(question):
    """question"""
    # 
    speed_match = re.search(r'current speed is (\d+) m/s', question)
    speed = int(speed_match.group(1)) if speed_match else 0
    
    # 
    nav_match = re.search(r"navigation command is '([^']+)'", question)
    navigation = nav_match.group(1) if nav_match else 'go straight'
    
    return speed, navigation

def generate_distractor_options(correct_speed, correct_path, current_speed, navigation):
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
        # PATH
        if 'left' in navigation.lower():
            preferred_paths = ['LEFT_TURN', 'LEFT_CHANGE', 'STRAIGHT']
        elif 'right' in navigation.lower():
            preferred_paths = ['RIGHT_TURN', 'RIGHT_CHANGE', 'STRAIGHT']
        else:
            preferred_paths = ['STRAIGHT', 'LEFT_CHANGE', 'RIGHT_CHANGE']
        
        for path in preferred_paths:
            if path != correct_path and path in other_paths:
                distractors.append((correct_speed, path))
                break
    
    # 3: 
    if len(distractors) < 3:
        # 
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

def convert_q6_to_multiple_choice(entry):
    """q6"""
    if entry.get('question_type') != 'q6':
        return entry
    
    # 
    original_answer = entry['answer']
    correct_speed, correct_path = parse_speed_path_answer(original_answer)
    
    if not correct_speed or not correct_path:
        print(f":  - {original_answer}")
        return entry
    
    # question
    current_speed, navigation = extract_navigation_and_speed(entry['question'])
    
    # Generate
    distractors = generate_distractor_options(correct_speed, correct_path, current_speed, navigation)
    
    # 4（）
    options = [(correct_speed, correct_path)] + distractors
    random.shuffle(options)  # 
    
    # Found
    correct_index = options.index((correct_speed, correct_path))
    correct_letter = chr(65 + correct_index)  # A=65, B=66, C=67, D=68
    
    # question
    question_base = entry['question']
    # 
    question_base = re.sub(r'For example.*?</SPEED PATH PLAN>\.', '', question_base, flags=re.DOTALL)
    question_base = question_base.strip()
    
    # questionimage
    if not question_base.startswith('<FRONT VIEW>'):
        # image
        image_paths = entry.get('image_path', {})
        
        # Generate
        camera_template = generate_camera_view_template(image_paths)
        
        question_base = camera_template + "\n" + question_base
    
    # 
    options_text = "\n\nPlease select the most appropriate SPEED and PATH plan for your vehicle:\n\n"
    for i, (speed, path) in enumerate(options):
        letter = chr(65 + i)
        options_text += f"{letter}. {speed}, {path}\n"
    options_text += (
        "\nInstructions:\n"
        "- Consider your current speed, navigation command, and traffic conditions\n"
        "- Analyze the road layout, other vehicles, and potential obstacles\n"
        "- Select the most appropriate driving plan for the next few seconds\n"
        "- Provide only the letter of your choice\n"
        "Your answer (provide only the letter):"
    )
    
    new_question = question_base + options_text
    
    # 
    new_entry = entry.copy()
    new_entry['question'] = new_question
    new_entry['answer'] = correct_letter
    
    return new_entry

def convert_q6_to_multiple_choice_for_main(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Q6question
    main_converter.py
    """
    converted_data = data.copy()
    
    # 
    original_answer = data.get('answer', '')
    correct_speed, correct_path = parse_speed_path_answer(original_answer)
    
    if not correct_speed or not correct_path:
        # ，
        correct_speed = 'KEEP'
        correct_path = 'STRAIGHT'
    
    # question
    current_speed, navigation = extract_navigation_and_speed(data.get('question', ''))
    
    # Generate
    distractors = generate_distractor_options(correct_speed, correct_path, current_speed, navigation)
    
    # 4（）
    options = [(correct_speed, correct_path)] + distractors
    random.shuffle(options)  # 
    
    # Found
    correct_index = options.index((correct_speed, correct_path))
    correct_letter = chr(65 + correct_index)  # A=65, B=66, C=67, D=68
    
    # question
    question_base = data.get('question', '')
    # 
    question_base = re.sub(r'For example.*?</SPEED PATH PLAN>\.', '', question_base, flags=re.DOTALL)
    question_base = question_base.strip()
    
    # （）
    image_paths = data.get('image_path', {})
    camera_template = generate_camera_view_template(image_paths)
    camera_block_pattern = r'^(?:<[^>]+>:\n<image>\n?)+'
    question_base = re.sub(camera_block_pattern, '', question_base, flags=re.MULTILINE).lstrip()
    if camera_template:
        question_base = camera_template + "\n\n" + question_base
    
    # 
    options_text = "\n\nPlease select the most appropriate SPEED and PATH plan for your vehicle:\n\n"
    for i, (speed, path) in enumerate(options):
        letter = chr(65 + i)
        options_text += f"{letter}. {speed}, {path}\n"
    options_text += (
        "\nInstructions:\n"
        "- Consider your current speed, navigation command, and traffic conditions\n"
        "- Analyze the road layout, other vehicles, and potential obstacles\n"
        "- Select the most appropriate driving plan for the next few seconds\n"
        "- Provide only the letter of your choice\n"
        "Your answer (provide only the letter):"
    )
    
    new_question = question_base + options_text
    
    # 
    converted_data['question'] = new_question
    converted_data['answer'] = correct_letter
    converted_data['correct_answer'] = f"{correct_speed}, {correct_path}"
    
    return converted_data

def main():
    # ，main_converter.py
    print("：main_converter.py，")
    print(": python3 preprocessing_scripts/question_switch/utils_switch/main_converter.py")

if __name__ == "__main__":
    main()