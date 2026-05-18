#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Q7question
Q7questionquestion
"""

import re
from typing import Dict, Any
from camera_utils import generate_camera_view_template_for_waypoints

def extract_coordinates_from_answer(answer: str) -> str:
    """
    Q7，PLANNING
    """
    if not answer:
        return answer
    
    # mode：[-, ]  [, ]
    coordinate_pattern = r'\[-?\d+\.?\d*,\s*-?\d+\.?\d*\]'
    coordinates = re.findall(coordinate_pattern, answer)
    
    if coordinates:
        # 
        return ', '.join(coordinates)
    else:
        # Found，
        return answer

def convert_q7_to_structured_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Q7questionquestion
    """
    if data.get('question_type') != 'q7':
        return data
    
    # question
    original_question = data.get('question', '')
    
    # 
    if "Output exactly 10 coordinate pairs" in original_question:
        # question，Processing
        original_answer = data.get('answer', '')
        cleaned_answer = extract_coordinates_from_answer(original_answer)
        
        # 
        converted_data = data.copy()
        converted_data['answer'] = cleaned_answer
        
        return converted_data
    
    # questionimage（ <CAM_*>: \n<image> ）
    has_cam_tags = original_question.strip().startswith('<CAM_')
    if not has_cam_tags:
        # image
        image_paths = data.get('image_path', {})
        
        # Generate（<image>）
        image_format = generate_camera_view_template_for_waypoints(image_paths)
        
        # image
        original_question = re.sub(r'\(1\) front view \(which you should focus on with the most attention\) <image>, \(2\) front right view <image>, and \(3\) front left view <image>', '', original_question)
        # 
        original_question = image_format + "\n" + original_question
    
    # question
    format_instruction = (
        "\n\nPlease provide your answer in the following exact format: "
        "Output exactly 10 coordinate pairs as [x, y] separated by commas, "
        "starting with the first timestep and ending with the 10th timestep. "
        "Example: [x1, y1], [x2, y2], [x3, y3], [x4, y4], [x5, y5], [x6, y6], [x7, y7], [x8, y8], [x9, y9], [x10, y10]. "
        "All coordinates should be rounded to 2 decimal places."
    )
    
    # question
    new_question = original_question + format_instruction
    
    # Processing，
    original_answer = data.get('answer', '')
    cleaned_answer = extract_coordinates_from_answer(original_answer)
    
    # 
    converted_data = data.copy()
    converted_data['question'] = new_question
    converted_data['answer'] = cleaned_answer
    
    return converted_data

def convert_q7_to_structured_format_for_main(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Q7questionquestion
    main_converter.py
    """
    return convert_q7_to_structured_format(data)

def main():
    """
    ，
    """
    # 
    test_data = {
        "question_type": "q7",
        "question": "You are an autonomous driving agent. You have access to multi-view camera images of a vehicle: (1) front view (which you should focus on with the most attention) <image>, (2) front right view <image>, and (3) front left view <image>. Your task is to do your best to predict future waypoints for the vehicle over the next 10 timesteps, given the vehicle's intent inferred from the images. Provided are the previous ego vehicle status recorded over the last 3.0 seconds (at 0.5-second intervals). This includes the x and y coordinates of the ego vehicle. Positive x means forward direction while positive y means leftwards. The data is presented in the format [x, y]:(t-3.0s) [-23.29, 0.05], Acceleration: X 0.44, Y -0.07 m/s^2, Velocity: X 7.54, Y 0.0 m/s, (t-2.5s) [-19.46, 0.04], Acceleration: X 0.22, Y 0.05 m/s^2, Velocity: X 7.69, Y 0.0 m/s, (t-2.0s) [-15.5, 0.05], Acceleration: X 0.13, Y -0.07 m/s^2, Velocity: X 7.75, Y 0.0 m/s, (t-1.5s) [-11.6, 0.06], Acceleration: X -0.01, Y -0.15 m/s^2, Velocity: X 7.78, Y 0.0 m/s, (t-1.0s) [-7.68, 0.04], Acceleration: X -0.11, Y -0.11 m/s^2, Velocity: X 7.71, Y 0.0 m/s, (t-0.5s) [-3.8, 0.04], Acceleration: X -0.23, Y -0.2 m/s^2, Velocity: X 7.6, Y 0.0 m/s, (t-0.0s) [0.0, 0.0], Acceleration: X -0.32, Y -0.09 m/s^2, Velocity: X 7.43, Y 0.0 m/s",
        "answer": "<PLANNING>Predicted future movement details for the next 5 seconds (sampled at 0.5-second intervals), including BEV location in x and y directions (in meters). Positive x means forward direction while positive y means leftwards. The output is formatted as [x, y]: [-0.00, 0.00], [3.32, -0.10], [6.58, -0.27], [9.82, -0.55], [13.05, -0.92], [16.31, -1.33], [19.64, -1.76], [23.09, -2.19], [26.70, -2.69], [30.33, -3.24]</PLANNING>",
        "tag": [6]
    }
    
    # 
    converted = convert_q7_to_structured_format(test_data)
    print("question:")
    print(test_data['question'])
    print("\n:")
    print(test_data['answer'])
    print("\nquestion:")
    print(converted['question'])
    print("\n:")
    print(converted['answer'])

if __name__ == '__main__':
    main()
