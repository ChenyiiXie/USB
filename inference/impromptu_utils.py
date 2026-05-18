#!/usr/bin/env python3
"""
Impromptu
ProcessingImpromptu
"""

import os
import re
import json
from typing import List, Dict, Any
from PIL import Image
import numpy as np


def replace_system_prompt_impromptu(prompt: str, image_paths) -> str:
    """
    Impromptu
    
    Args:
        prompt (str): 
        image_paths: image，List[str]Dict[str, str]
        
    Returns:
        str: 
    """
    # 
    camera_order = [
        "CAM_FRONT",
        "CAM_FRONT_LEFT",
        "CAM_FRONT_RIGHT",
        "CAM_BACK",
        "CAM_BACK_LEFT",
        "CAM_BACK_RIGHT"
    ]
    
    # Processing
    if isinstance(image_paths, dict):
        # ，
        ordered_cameras = []
        for camera in camera_order:
            if camera in image_paths and image_paths[camera] is not None:
                ordered_cameras.append(camera)
    elif isinstance(image_paths, list):
        # ，
        camera_pattern = r'(?:\.|__)(CAM_[A-Z_]+)(?:_[^.]*)?(?:\.|__)'
        
        extracted_cameras = []
        for path in image_paths:
            if path is not None:
                match = re.search(camera_pattern, str(path))
                if match:
                    camera_name = match.group(1)
                    if camera_name in camera_order:
                        extracted_cameras.append(camera_name)
                    else:
                        print(f"Warning: Unrecognized camera name '{camera_name}' in path '{path}'")
                else:
                    print(f"Warning: Unable to extract camera name from path '{path}'")
        
        # 
        unique_cameras = []
        seen = set()
        for cam in extracted_cameras:
            if cam not in seen:
                unique_cameras.append(cam)
                seen.add(cam)
        
        ordered_cameras = [cam for cam in camera_order if cam in unique_cameras]
    else:
        print(f"Warning: Unexpected image_paths format: {type(image_paths)}")
        return prompt
    
    if not ordered_cameras:
        print("Warning: No valid camera images provided, using default prompt")
        return prompt
    else:
        cameras_str = ", ".join(ordered_cameras)
        if len(ordered_cameras) == 1:
            new_sentence = f"You are provided with a single camera image: [{cameras_str}]."
        else:
            new_sentence = f"You are provided with {len(ordered_cameras)} camera images in the sequence [{cameras_str}]."
    
    # 
    original_sentence_pattern = r"You are provided with up to six camera images in the sequence \[CAM_FRONT, CAM_FRONT_LEFT, CAM_FRONT_RIGHT, CAM_BACK, CAM_BACK_LEFT, CAM_BACK_RIGHT\]\."
    
    updated_prompt, num_subs = re.subn(original_sentence_pattern, new_sentence, prompt)
    
    if num_subs == 0:
        # Found，
        if "You are an autonomous driving expert" in prompt:
            # "autonomous driving expert"
            updated_prompt = re.sub(
                r"(You are an autonomous driving expert)(.*?)(Analyze multi-view camera images)",
                r"\1. " + new_sentence + r"\2\3",
                prompt
            )
            if updated_prompt == prompt:
                # to，
                updated_prompt = f"You are an autonomous driving expert. {new_sentence}\n\n{prompt}"
        else:
            # ，
            updated_prompt = f"{new_sentence}\n\n{prompt}"
        print(f"Added camera information to prompt: {new_sentence}")
    
    return updated_prompt


def process_impromptu_question(question: str) -> str:
    """
    ProcessingImpromptuquestion
    <image>，
    
    Args:
        question (str): question
        
    Returns:
        str: Processingquestion，questionNone
    """
    processed_question = question
    
    # ，<image>
    view_patterns = [
        (r'<FRONT VIEW>:\s*', ''),        # ，<image>
        (r'<FRONT LEFT VIEW>:\s*', ''),
        (r'<FRONT RIGHT VIEW>:\s*', ''),
        (r'<BACK VIEW>:\s*', ''),
        (r'<BACK LEFT VIEW>:\s*', ''),
        (r'<BACK RIGHT VIEW>:\s*', ''),
    ]
    
    for pattern, replacement in view_patterns:
        processed_question = re.sub(pattern, replacement, processed_question)
    
    # （<image>）
    processed_question = re.sub(r'\n+', '\n', processed_question).strip()
    
    # empty question（）
    if not processed_question or processed_question.isspace():
        return None
    
    return processed_question


def validate_impromptu_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Impromptu
    
    Args:
        data: 
        
    Returns:
        Dict: result
    """
    stats = {
        'total_samples': len(data),
        'valid_samples': 0,
        'missing_images': 0,
        'invalid_questions': 0,
        'question_types': {},
        'camera_usage': {}
    }
    
    for sample in data:
        is_valid = True
        
        # 
        required_fields = ['scene_token', 'frame_token', 'question', 'answer', 'image_path']
        for field in required_fields:
            if field not in sample:
                print(f"Warning: Missing field '{field}' in sample {sample.get('scene_token', 'unknown')}")
                is_valid = False
        
        # image
        if 'image_path' in sample:
            for camera, path in sample['image_path'].items():
                if not os.path.exists(path):
                    print(f"Warning: Image file not found: {path}")
                    stats['missing_images'] += 1
                    is_valid = False
        
        # question
        if 'question_type' in sample:
            q_type = sample['question_type']
            stats['question_types'][q_type] = stats['question_types'].get(q_type, 0) + 1
        
        # 
        if 'image_path' in sample:
            for camera in sample['image_path'].keys():
                stats['camera_usage'][camera] = stats['camera_usage'].get(camera, 0) + 1
        
        if is_valid:
            stats['valid_samples'] += 1
    
    return stats


def load_impromptu_data(data_file: str) -> List[Dict[str, Any]]:
    """
    Impromptu
    
    Args:
        data_file: 
        
    Returns:
        List[Dict]: 
    """
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} samples from {data_file}")
    
    # 
    stats = validate_impromptu_data(data)
    print(f"Data validation stats: {stats}")
    
    return data


def save_impromptu_results(results: List[Dict[str, Any]], output_file: str):
    """
    Imprompturesult
    
    Args:
        results: result
        output_file: 
    """
    # output directory
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_file}")
    print(f"Total results: {len(results)}")


def create_impromptu_batch_data(samples: List[Dict[str, Any]], batch_size: int = 1) -> List[Dict[str, Any]]:
    """
    ImpromptuProcessing
    
    Args:
        samples: sample
        batch_size: Processing
        
    Returns:
        List[Dict]: Processing
    """
    batches = []
    
    for i in range(0, len(samples), batch_size):
        batch_samples = samples[i:i + batch_size]
        
        batch_data = {
            'question': [sample['question'] for sample in batch_samples],
            'image_path': [sample['image_path'] for sample in batch_samples],
            'scene_token': [sample.get('scene_token', '') for sample in batch_samples],
            'frame_token': [sample.get('frame_token', '') for sample in batch_samples],
            'question_type': [sample.get('question_type', '') for sample in batch_samples],
            'answer': [sample.get('answer', '') for sample in batch_samples],
            'tag': [sample.get('tag', []) for sample in batch_samples]
        }
        
        batches.append(batch_data)
    
    return batches


def analyze_impromptu_results(results_file: str) -> Dict[str, Any]:
    """
    Imprompturesult
    
    Args:
        results_file: result
        
    Returns:
        Dict: result
    """
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    analysis = {
        'total_results': len(results),
        'question_types': {},
        'avg_response_length': 0,
        'response_lengths': [],
        'camera_usage': {}
    }
    
    total_length = 0
    
    for result in results:
        # question
        q_type = result.get('question_type', 'unknown')
        analysis['question_types'][q_type] = analysis['question_types'].get(q_type, 0) + 1
        
        # 
        pred = result.get('pred', '')
        if pred:
            length = len(pred.split())
            analysis['response_lengths'].append(length)
            total_length += length
        
        # 
        if 'image_path' in result:
            for camera in result['image_path'].keys():
                analysis['camera_usage'][camera] = analysis['camera_usage'].get(camera, 0) + 1
    
    if analysis['response_lengths']:
        analysis['avg_response_length'] = total_length / len(analysis['response_lengths'])
        analysis['min_response_length'] = min(analysis['response_lengths'])
        analysis['max_response_length'] = max(analysis['response_lengths'])
    
    return analysis
