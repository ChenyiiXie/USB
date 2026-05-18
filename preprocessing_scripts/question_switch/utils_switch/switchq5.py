import json
import re
from typing import Dict, List, Any
import random
from camera_utils import generate_camera_view_template

def extract_weather_from_answer(answer):
    """，"""
    answer_lower = answer.lower()
    
    # weather，
    #  "under ... weather conditions"  "... weather conditions" mode
    weather_match = re.search(r'under\s+(clear|rainy|foggy|snowy|cloudy|overcast)?\s*weather\s+conditions?[^.]*', answer_lower)
    
    if weather_match:
        weather_text = weather_match.group(0)
        # 
        weather_text = re.sub(r'\b(daytime|nighttime|daylight|night)\s+(driving\s+scene\s+)?', '', weather_text)
        weather_text = re.sub(r'the\s+image\s+shows\s+a\s+', '', weather_text)
        weather_text = re.sub(r'^\s*under\s+', '', weather_text)
        # 
        weather_text = weather_text.strip().capitalize()
        if not weather_text.endswith('.'):
            weather_text += '.'
        return weather_text
    
    # Foundstandard，mode
    # ："clear weather conditions, with ample sunlight and no visible precipitation"
    if re.search(r'clear.*weather.*sunlight.*no.*precipitation', answer_lower):
        return "Clear weather conditions, with ample sunlight and no visible precipitation."
    # ："clear weather conditions, indicating good visibility"
    elif re.search(r'clear.*weather.*good visibility', answer_lower):
        return "Clear weather conditions, indicating good visibility."
    # ："clear weather conditions"
    elif re.search(r'clear.*weather', answer_lower):
        return "Clear weather conditions."
    # 
    elif 'rain' in answer_lower and 'precipitation' in answer_lower:
        return "Rainy weather conditions with visible precipitation."
    elif 'rain' in answer_lower:
        return "Rainy weather conditions."
    # 
    elif 'fog' in answer_lower:
        return "Foggy weather conditions."
    # 
    elif 'snow' in answer_lower:
        return "Snowy weather conditions."
    # 
    elif 'cloud' in answer_lower or 'overcast' in answer_lower:
        return "Cloudy weather conditions."
    
    return "Clear weather conditions."

def extract_time_from_answer(answer):
    """（/）"""
    answer_lower = answer.lower()
    
    # types
    if re.search(r'daytime|daylight hours?|during.*day|well-lit.*natural light', answer_lower):
        return "Daytime."
    # 
    elif re.search(r'night|nighttime|evening|dark', answer_lower):
        return "Nighttime."
    
    # 
    return "Daytime."

def extract_road_conditions_from_answer(answer):
    """"""
    # roadsurface
    sentences = [s.strip() for s in answer.split('.') if s.strip()]
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        # 
        if re.search(r'road surface|road.*condition', sentence_lower):
            # 、、
            if not re.search(r'truck|car|jeep|van|vehicle|pedestrian|traffic light|moving|positioned|stationary|parked', sentence_lower):
                return sentence + '.'
    
    # Found，
    answer_lower = answer.lower()
    
    # ："smooth and free of obstacles"
    if re.search(r'smooth.*free of obstacles?', answer_lower):
        return "The road surface appears smooth and free of obstacles."
    # ："smooth with no visible obstacles"
    elif re.search(r'smooth.*no visible obstacles?', answer_lower):
        return "The road surface appears smooth with no visible obstacles."
    # ："smooth"
    elif 'smooth' in answer_lower:
        return "The road surface appears smooth."
    # 
    elif re.search(r'obstacle|debris|hazard', answer_lower):
        return "There are obstacles present on the road."
    
    return "The road surface appears to be in normal condition."

def split_q5_entry(entry):
    """q53question"""
    # （，questionanswer）
    base_info = {k: v for k, v in entry.items() if k not in ['question', 'answer']}
    
    # 
    original_answer = entry["answer"]
    
    # 3，question_type"q5"
    q5_entries = []
    
    # Q5-Weather
    q5_weather = base_info.copy()
    q5_weather["question_type"] = "q5"
    # imageGeneratequestion
    image_paths = base_info.get('image_path', {})
    camera_template = generate_camera_view_template(image_paths)
    q5_weather["question"] = f"{camera_template}\n\nBased on the multi-view camera images, what are the prevailing weather conditions?"
    q5_weather["answer"] = extract_weather_from_answer(original_answer)
    q5_entries.append(q5_weather)
    
    # Q5-/（）
    q5_time = base_info.copy()
    q5_time["question_type"] = "q5"
    q5_time["question"] = f"{camera_template}\n\nBased on the multi-view camera images, is it daytime or nighttime?\n\nA. Daytime\nB. Nighttime\n\nAnswer: [Letter, e.g., \"A\" or \"B\"]"
    #  - 
    time_answer = extract_time_from_answer(original_answer)
    q5_time["answer"] = time_answer  # ，convert_q5_to_multiple_choiceProcessing
    q5_entries.append(q5_time)
    
    # Q5-
    q5_road = base_info.copy()
    q5_road["question_type"] = "q5"
    q5_road["question"] = f"{camera_template}\n\nBased on the multi-view camera images, describe the road conditions. Is the surface smooth, or are there obstacles present?"
    q5_road["answer"] = extract_road_conditions_from_answer(original_answer)
    q5_entries.append(q5_road)
    
    return q5_entries

def convert_q5_to_multiple_choice(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Q5question3（q5.1, q5.2, q5.3）
    main_converter.py
    """
    # Q53question，
    split_entries = split_q5_entry(data)
    converted_entries = []
    
    for i, entry in enumerate(split_entries):
        converted_entry = entry.copy()
        
        # questionquestion
        question = entry.get('question', '')
        answer = entry.get('answer', '')
        
        if 'weather conditions' in question:
            # Q5.1 - Weather
            converted_entry['question_type'] = 'q5.1'
            # imageGeneratequestion
            image_paths = entry.get('image_path', {})
            camera_template = generate_camera_view_template(image_paths)
            converted_entry['question'] = (
                f"{camera_template}\n\n"
                "Question: Based on the multi-view camera images, what are the prevailing weather conditions?\n\n"
                "Instructions:\n"
                "- Look carefully at all camera views to assess weather conditions\n"
                "- Consider factors like visibility, precipitation, lighting, and atmospheric conditions\n"
                "- Provide a clear description of the weather conditions\n\n"
                "Your answer:"
            )
            converted_entry['answer'] = answer
            
        elif 'daytime or nighttime' in question:
            # Q5.2 - 
            converted_entry['question_type'] = 'q5.2'
            # imageGeneratequestion
            image_paths = entry.get('image_path', {})
            camera_template = generate_camera_view_template(image_paths)
            
            # 
            if 'daytime' in answer.lower():
                correct_text = 'Daytime'
            elif 'nighttime' in answer.lower() or 'night' in answer.lower():
                correct_text = 'Nighttime'
            else:
                correct_text = 'Daytime' if 'day' in answer.lower() else 'Nighttime'
            
            # ，
            options = ['Daytime', 'Nighttime']
            random.shuffle(options)
            
            # （）
            correct_index = options.index(correct_text)
            correct_letter = chr(65 + correct_index)

            # question
            q_text = (
                f"{camera_template}\n\n"
                "Question: Based on the multi-view camera images, is it daytime or nighttime?\n\n"
                "Please select the most appropriate option:\n\n"
            )
            for i, opt in enumerate(options):
                q_text += f"{chr(65 + i)}. {opt}\n"
            q_text += (
                "\nInstructions:\n"
                "- Look carefully at all camera views to assess lighting conditions\n"
                "- Consider factors like natural light, shadows, and overall brightness\n"
                "- Provide only the letter of your choice\n"
                "Your answer (provide only the letter):"
            )
            converted_entry['question'] = q_text
            converted_entry['answer'] = correct_letter
            
        elif 'road conditions' in question:
            # Q5.3 - 
            converted_entry['question_type'] = 'q5.3'
            # imageGeneratequestion
            image_paths = entry.get('image_path', {})
            camera_template = generate_camera_view_template(image_paths)
            converted_entry['question'] = (
                f"{camera_template}\n\n"
                "Question: Based on the multi-view camera images, describe the road conditions. "
                "Is the surface smooth, or are there obstacles present?\n\n"
                "Instructions:\n"
                "- Look carefully at all camera views to assess road conditions\n"
                "- Consider factors like surface quality, obstacles, markings, and traffic\n"
                "- Provide a clear description of the road conditions\n\n"
                "Your answer:"
            )
            converted_entry['answer'] = answer
        
        converted_entries.append(converted_entry)
    
    return converted_entries

def main():
    # ，main_converter.py
    print("：main_converter.py，")
    print(": python3 preprocessing_scripts/question_switch/utils_switch/main_converter.py")

if __name__ == "__main__":
    main()