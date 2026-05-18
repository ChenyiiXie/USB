#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

question
"""

import json
import os
import shutil
import random
from typing import Dict, List, Any
from pathlib import Path

# q7
from switchq7 import convert_q7_to_structured_format_for_main as switchq7_convert

# typesresult
random.seed(42)

def convert_q1_to_multiple_choice(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Q1question：
    1. （）
    2. 
    """
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from switchq1 import convert_q1_questions
    
    return convert_q1_questions(data)

def convert_q2_to_multiple_choice(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Q2questionq2.1（Object 1）
    """
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from switchq2 import convert_q2_to_q2_1
    
    # 
    converted = convert_q2_to_q2_1(data)
    return [converted] if converted else []

def convert_q3_to_open_ended(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Q3，
    """
    # Q3，
    converted_data = data.copy()
    
    # （<...><image>）
    from camera_utils import generate_camera_view_template
    import re
    image_paths = converted_data.get('image_path', {})
    camera_template = generate_camera_view_template(image_paths)

    question = converted_data.get('question', '') or ''
    question = question.strip()

    # （ <FRONT VIEW>:\n<image> ）
    camera_block_pattern = r'^(?:<[^>]+>:\n<image>\n?)+'
    question = re.sub(camera_block_pattern, '', question, flags=re.MULTILINE).lstrip()

    # 
    if camera_template:
        question = f"{camera_template}\n\n{question}".strip()

    # 
    if question and not question.endswith('?'):
        question = question.rstrip('.') + '?'

    converted_data['question'] = question
    return converted_data

def convert_q4_to_multiple_choice(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Q4
    """
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from switchq4 import convert_q4_to_multiple_choice as switchq4_convert
    
    return switchq4_convert(data)

def convert_q5_to_multiple_choice(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Q5（3question）
    """
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from switchq5 import convert_q5_to_multiple_choice as switchq5_convert
    
    return switchq5_convert(data)

def convert_q6_to_multiple_choice(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Q6
    """
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from switchq6 import convert_q6_to_multiple_choice_for_main as switchq6_convert
    
    return switchq6_convert(data)

def convert_q7_to_structured_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Q7questionquestion
    """
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from switchq7 import convert_q7_to_structured_format_for_main as switchq7_convert
    
    return switchq7_convert(data)

def convert_question_by_type(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    questionquestion
    """
    question_type = data.get('question_type', '')
    converted_questions = []
    
    if question_type == 'q1':
        # Q1
        converted_questions = convert_q1_to_multiple_choice(data)
    elif question_type == 'q2':
        # Q2
        converted_questions = convert_q2_to_multiple_choice(data)
    elif question_type == 'q3':
        # Q3
        converted_questions = [convert_q3_to_open_ended(data)]
    elif question_type == 'q4':
        # Q4
        converted_questions = [convert_q4_to_multiple_choice(data)]
    elif question_type == 'q5':
        # Q5（3question）
        converted_questions = convert_q5_to_multiple_choice(data)
    elif question_type == 'q6':
        # Q6
        converted_questions = [convert_q6_to_multiple_choice(data)]
    elif question_type == 'q7':
        # Q7question
        converted_questions = [switchq7_convert(data)]
    else:
        # ，
        converted_questions = [data]
    
    return converted_questions

def process_data_file(input_file: str, output_file: str):
    """
    Processing
    """
    print(f"Processing file: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    converted_data = []
    
    for item in data:
        try:
            converted_items = convert_question_by_type(item)
            converted_data.extend(converted_items)
        except Exception as e:
            print(f"Error while converting question: {e}")
            # failed，
            converted_data.append(item)
    
    # output directory
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=2)
    
    print(f"Done，to: {output_file}")
    print(f"question: {len(data)}, question: {len(converted_data)}")

def process_directory(input_dir: str, output_dir: str, overwrite: bool = False):
    """
    Processing
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"Input directory not found: {input_dir}")
        return
    
    # output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # JSON
    for json_file in input_path.rglob('*.json'):
        # 
        relative_path = json_file.relative_to(input_path)
        output_file = output_path / relative_path
        
        # Check output files
        if output_file.exists() and not overwrite:
            print(f"skip existing: {output_file}")
            continue
        
        # Processing file
        process_data_file(str(json_file), str(output_file))

def main():
    """
    
    """
    import argparse
    
    #  preprocessing_scripts/question_switch/utils_switch/，Project root
    project_root = Path(__file__).resolve().parents[3]
    default_input = project_root / "nuscenes_variants_by_shard_impromptu_full"
    default_output = project_root / "nuscenes_switch"
    
    parser = argparse.ArgumentParser(description='question')
    parser.add_argument('--input_path', default=str(default_input), help=f'（），: {default_input}')
    parser.add_argument('--output_path', default=str(default_output), help=f'（），: {default_output}')
    parser.add_argument('--overwrite', action='store_true', help='')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)
    
    print(f": {input_path}")
    print(f": {output_path}")
    print(f"mode: {'' if args.overwrite else ''}")
    print("-" * 50)
    
    if input_path.is_file():
        # Processing
        process_data_file(str(input_path), str(output_path))
    elif input_path.is_dir():
        # Processing directory
        process_directory(str(input_path), str(output_path), args.overwrite)
    else:
        print(f"not found: {input_path}")

if __name__ == '__main__':
    main()
