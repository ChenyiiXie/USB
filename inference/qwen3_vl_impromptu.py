"""
Qwen3-VL-8B-InstructImpromptu
Qwen3-VL-8B-Instruct
/
"""

import os
import re
import json
import argparse
from typing import Any, Dict, List

import torch
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor
try:
    from transformers import AutoModelForVision2Seq  # Generate
except Exception:
    AutoModelForVision2Seq = None

# （）
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inference.impromptu_utils import (
    replace_system_prompt_impromptu,
    process_impromptu_question,
)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Qwen3-VL-8B-Instruct Inference for Impromptu Dataset')
    parser.add_argument('--model', type=str, required=True, help='Qwen3-VL-8B-Instructmodel path')
    parser.add_argument('--data', type=str, required=True, help='merged Impromptu data JSON file')
    parser.add_argument('--output', type=str, required=True, help='JSON（）')
    parser.add_argument('--system_prompt', type=str, required=True, help='system prompt file')
    parser.add_argument('--num_processes', type=int, default=1, help='，CLI')
    parser.add_argument('--max_model_len', type=int, default=8192, help='，CLI')
    parser.add_argument('--num_images_per_prompt', type=int, default=6, help='maximum number of images per sample')
    parser.add_argument('--batch_size', type=int, default=1, help='（sampleProcessing）')
    parser.add_argument('--temperature', type=float, default=0.2, help='')
    parser.add_argument('--top_p', type=float, default=0.2, help='Top-p ')
    parser.add_argument('--max_tokens', type=int, default=512, help='Generatetoken')
    parser.add_argument('--max_samples', type=int, default=None, help='Processingsample（）')
    parser.add_argument('--save_processed_images', action='store_true', help='Processing image')
    parser.add_argument('--debug_image_dir', type=str, default='debug_processed_images', help='image')
    return parser.parse_args()


def select_images_from_dict(image_path_dict: Dict[str, str], camera_order: List[str], limit: int) -> List[str]:
    """imageimage，"""
    selected_paths: List[str] = []
    for cam in camera_order:
        if cam in image_path_dict and image_path_dict[cam] is not None:
            selected_paths.append(image_path_dict[cam])
        if len(selected_paths) >= limit:
            break
    # ：，
    if len(selected_paths) < limit:
        for cam, path in image_path_dict.items():
            if path is not None and path not in selected_paths:
                selected_paths.append(path)
            if len(selected_paths) >= limit:
                break
    return selected_paths


def load_images_as_pil(image_paths: List[str]) -> List[Image.Image]:
    """imagePIL"""
    pil_images: List[Image.Image] = []
    for path in image_paths:
        try:
            img = Image.open(path).convert('RGB')
            pil_images.append(img)
        except Exception as e:
            print(f"Warning: failed to load image {path}: {e}")
    return pil_images


def build_messages(system_prompt: str, question_text: str, num_images: int) -> List[Dict[str, Any]]:
    """Qwen3-VL"""
    # Qwen3-VL：userimage + 
    user_content: List[Dict[str, Any]] = []
    for _ in range(num_images):
        user_content.append({"type": "image"})
    user_content.append({"type": "text", "text": question_text})

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    return messages


def main():
    args = parse_arguments()

    # 
    with open(args.system_prompt, 'r', encoding='utf-8') as f:
        raw_system_prompt = f.read()

    # Processing
    print(f"Loading Qwen3-VL-8B-Instruct model from: {args.model}")
    processor = AutoProcessor.from_pretrained(args.model, trust_remote_code=True)
    
    # transformers
    model = None
    load_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    
    # Generate
    if AutoModelForVision2Seq is not None:
        try:
            model = AutoModelForVision2Seq.from_pretrained(
                args.model,
                trust_remote_code=True,
                dtype=load_dtype,
            )
        except Exception as e:
            print(f"[Info] AutoModelForVision2Seq load failed, try CausalLM. Reason: {e}")
    
    if model is None:
        try:
            model = AutoModelForCausalLM.from_pretrained(
                args.model,
                trust_remote_code=True,
                dtype=load_dtype,
            )
        except Exception as e:
            print(f"[Info] AutoModelForCausalLM load failed, fallback to base AutoModel. Reason: {e}")
            from transformers import AutoModel
            model = AutoModel.from_pretrained(
                args.model,
                trust_remote_code=True,
                dtype=load_dtype,
            )
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()

    # 
    print(f"Loading Impromptu data from: {args.data}")
    with open(args.data, 'r', encoding='utf-8') as f:
        all_data = json.load(f)

    if args.max_samples is not None:
        all_data = all_data[:args.max_samples]
        print(f"Limited to {len(all_data)} samples for testing")
    else:
        print(f"Loaded {len(all_data)} samples")

    # 
    output_file = args.output if args.output.endswith('.json') else f"{args.output}.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    if not os.path.exists(output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2, ensure_ascii=False)

    results_dir = os.path.dirname(output_file)
    individual_results_dir = os.path.join(results_dir, 'individual_results')
    os.makedirs(individual_results_dir, exist_ok=True)

    camera_order = ['CAM_FRONT', 'CAM_FRONT_LEFT', 'CAM_FRONT_RIGHT', 'CAM_BACK', 'CAM_BACK_LEFT', 'CAM_BACK_RIGHT']

    for idx, sample in enumerate(all_data):
        sample_num = idx + 1

        question_raw = sample.get('question', '')
        processed_question = process_impromptu_question(question_raw)
        if processed_question is None:
            print(f"⏭️  Skipempty questionsample {sample_num}/{len(all_data)}")
            continue

        image_path_dict = sample.get('image_path', {}) or {}
        selected_paths = select_images_from_dict(image_path_dict, camera_order, args.num_images_per_prompt)
        pil_images = load_images_as_pil(selected_paths)

        # 
        system_prompt = replace_system_prompt_impromptu(raw_system_prompt, image_path_dict)

        # 
        messages = build_messages(system_prompt=system_prompt, question_text=processed_question, num_images=len(pil_images))
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        # Processing：image， [[]]
        if len(pil_images) > 0:
            inputs = processor(text=[text], images=[pil_images], return_tensors="pt")
        else:
            inputs = processor(text=[text], return_tensors="pt")
        inputs = {k: v.to(model.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                do_sample=True,
                temperature=float(args.temperature),
                top_p=float(args.top_p),
                max_new_tokens=int(args.max_tokens),
            )

        # Generate
        generated_text = processor.batch_decode(
            generated_ids[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True
        )[0].strip()

        # sampleresult
        result = {
            'question': sample.get('question', ''),
            'image_path': image_path_dict,
            'question_type': sample.get('question_type', ''),
            'scene_token': sample.get('scene_token', ''),
            'frame_token': sample.get('frame_token', ''),
            'answer': sample.get('answer', ''),
            'pred': generated_text,
        }

        scene_token = result.get('scene_token', f'sample_{sample_num:06d}')
        individual_file = os.path.join(individual_results_dir, f'sample_{sample_num:06d}_{scene_token}.json')
        with open(individual_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # toresult
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
        else:
            existing_results = []

        existing_results.append(result)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(existing_results, f, indent=2, ensure_ascii=False)

        print(f"✅ Sample {sample_num}/{len(all_data)} completed and saved to {individual_file}")

    print("\nProcessing completed. Individual files saved.")
    print(f"Individual results directory: {individual_results_dir}")
    print(f"Main results file: {output_file}")


if __name__ == '__main__':
    main()
