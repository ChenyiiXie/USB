#!/usr/bin/env python3
"""
ProcessingnuScenesvariant，shardGenerateImpromptu
keep only the first timestamp of each scene，matching the nuscenes_impromptu_data_first_moment_v2.json format
"""

import os
import json
import argparse
import shutil
from tqdm import tqdm
from typing import List, Dict, Any

# ，question
CAMERA_ORDER = [
    'CAM_FRONT',
    'CAM_FRONT_RIGHT',
    'CAM_FRONT_LEFT',
    'CAM_BACK',
    'CAM_BACK_RIGHT',
    'CAM_BACK_LEFT',
]

# variant
VARIANTS = [
    'backlight', 'bit_error', 'bright', 'clean', 'compress', 'crash', 'dark', 
    'fog', 'frame_lost', 'glare', 'lens', 'lightning', 'motion_blur', 'quant', 
    'rain', 'sandstorm', 'saturate', 'smoke', 'snow', 'splash', 'zoom_blur'
]

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp')

def classify_question_by_number(q_num: int) -> str:
    """questionquestion"""
    return f"q{q_num}"

def process_qa_pair_from_files(nuscenes_dir: str, sample_id: str, q_num: int, image_paths: Dict[str, str]) -> Dict[str, Any]:
    """，extract_first_moment.py"""
    q_file = f"{sample_id}.q{q_num}_question.txt"
    a_file = f"{sample_id}.q{q_num}_answer.txt"
    img_file = f"{sample_id}.q{q_num}_images.json"
    
    q_path = os.path.join(nuscenes_dir, q_file)
    a_path = os.path.join(nuscenes_dir, a_file)
    img_path = os.path.join(nuscenes_dir, img_file)
    
    if not all(os.path.exists(p) for p in [q_path, a_path, img_path]):
        return None
    
    # question
    with open(q_path, 'r', encoding='utf-8') as f:
        question = f.read().strip()
    
    # 
    with open(a_path, 'r', encoding='utf-8') as f:
        answer = f.read().strip()
    
    # Read image
    with open(img_path, 'r', encoding='utf-8') as f:
        required_cameras = json.load(f)
    
    # required_camerasimage_paths，CAMERA_ORDER
    filtered_image_paths = {}
    required_set = set(required_cameras)
    for camera in CAMERA_ORDER:
        if camera in required_set and camera in image_paths:
            filtered_image_paths[camera] = image_paths[camera]
    
    # Generatetoken - ：
    scene_token = sample_id  # sample_idscene_token
    frame_token = f"{sample_id}_0"  # （_0）
    
    # questionquestion
    question_type = classify_question_by_number(q_num)
    
    # result
    result = {
        "scene_token": scene_token,
        "frame_token": frame_token,
        "question_type": question_type,
        "question": question,
        "answer": answer,
        "tag": [q_num - 1],  # 0
        "image_path": filtered_image_paths
    }
    
    return result

def get_shard_list(base_data_dir: str, variant: str) -> List[str]:
    """variantshard"""
    variant_dir = os.path.join(base_data_dir, variant)
    if not os.path.exists(variant_dir):
        return []
    
    shards = []
    for item in os.listdir(variant_dir):
        if os.path.isdir(os.path.join(variant_dir, item)) and 'shard' in item:
            shards.append(item)
    
    return sorted(shards)

def is_first_moment_sample_id(sample_id: str) -> bool:
    """Return True for the first timestamp sample id used by this dataset."""
    return not any(sample_id.endswith(f'_{i}') for i in range(1, 10))

def collect_first_moment_sample_ids(shard_dir: str) -> List[str]:
    """Collect sample ids from image filenames in one shard."""
    sample_ids = set()
    for filename in os.listdir(shard_dir):
        if filename.lower().endswith(IMAGE_EXTENSIONS):
            sample_id = filename.split('.')[0]
            if is_first_moment_sample_id(sample_id):
                sample_ids.add(sample_id)
    return sorted(sample_ids)

def materialize_clean_first_moment_dataset(base_data_dir: str, output_dir: str, max_samples: int = None) -> bool:
    """Copy clean first-moment files into output_dir/clean/<shard>."""
    clean_dir = os.path.join(base_data_dir, "clean")
    if not os.path.isdir(clean_dir):
        print(f"❌ cleandirectory not found: {clean_dir}")
        return False

    shards = get_shard_list(base_data_dir, "clean")
    if not shards:
        print(f"❌ Foundclean shard: {clean_dir}")
        return False

    output_clean_dir = os.path.join(output_dir, "clean")
    os.makedirs(output_clean_dir, exist_ok=True)

    total_files = 0
    total_samples = 0
    print(f"📁 clean: {clean_dir} -> {output_clean_dir}")

    for shard_name in shards:
        src_shard_dir = os.path.join(clean_dir, shard_name)
        dst_shard_dir = os.path.join(output_clean_dir, shard_name)
        os.makedirs(dst_shard_dir, exist_ok=True)

        sample_ids = collect_first_moment_sample_ids(src_shard_dir)
        if max_samples and len(sample_ids) > max_samples:
            sample_ids = sample_ids[:max_samples]

        copied_files = 0
        for sample_id in tqdm(sample_ids, desc=f" {shard_name}", leave=False):
            prefix = f"{sample_id}."
            for filename in os.listdir(src_shard_dir):
                if filename.startswith(prefix):
                    src = os.path.join(src_shard_dir, filename)
                    dst = os.path.join(dst_shard_dir, filename)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                        copied_files += 1

        total_samples += len(sample_ids)
        total_files += copied_files
        print(f"   ✅ {shard_name}: {len(sample_ids)} samples, {copied_files} files")

    print(f"✅ cleanDone: {total_samples} samples, {total_files} files")
    return True

def process_single_shard_first_moment(base_data_dir: str, variant: str, shard_name: str, max_samples: int = None) -> List[Dict[str, Any]]:
    """Processingshard，keep only the first timestamp of each scene"""
    shard_dir = os.path.join(base_data_dir, variant, shard_name)
    if not os.path.exists(shard_dir):
        print(f"   ⚠️  Sharddirectory not found: {shard_dir}")
        return []
    
    # sampleID - sample
    sample_ids = collect_first_moment_sample_ids(shard_dir)
    
    # sample
    if max_samples and len(sample_ids) > max_samples:
        sample_ids = sample_ids[:max_samples]
    
    print(f"   📊 Found {len(sample_ids)} sample（first timestamp only）")
    
    all_qa_pairs = []
    
    # Process each sample
    for sample_id in tqdm(sample_ids, desc=f"Processing {shard_name}", leave=False):
        # 
        image_paths = {}
        for cam_name in CAMERA_ORDER:
            # cleanvariant
            if variant == 'clean':
                image_filename = f"{sample_id}.{cam_name}.png"
            else:
                image_filename = f"{sample_id}.{cam_name}_{variant}.png"
            
            image_path = os.path.join(shard_dir, image_filename)
            
            if os.path.exists(image_path):
                image_paths[cam_name] = image_path
        
        # Found，Processing
        if len(image_paths) >= 4:  # 4
            # Processing7（q1toq7）
            for q_num in range(1, 8):
                qa_pair = process_qa_pair_from_files(shard_dir, sample_id, q_num, image_paths)
                if qa_pair:
                    all_qa_pairs.append(qa_pair)
    
    return all_qa_pairs

def process_variant_by_shard_first_moment(base_data_dir: str, variant: str, output_dir: str, max_samples: int = None) -> bool:
    """shardProcessingvariants，"""
    print(f"\n🔄 Start variant: {variant} (first timestamp only)")
    
    # shard
    shards = get_shard_list(base_data_dir, variant)
    if not shards:
        print(f"   ❌ Foundshard")
        return False
    
    print(f"   📁 Found {len(shards)} shard: {', '.join(shards)}")
    
    # shardJSON
    success_count = 0
    for shard_name in shards:
        print(f"   🔍 Processing {shard_name}...")
        
        # Processingshard
        qa_pairs = process_single_shard_first_moment(base_data_dir, variant, shard_name, max_samples)
        
        if qa_pairs:
            # variant
            variant_dir = os.path.join(output_dir, variant)
            os.makedirs(variant_dir, exist_ok=True)
            
            # Generateshard
            shard_suffix = shard_name.replace('nuScenes_', '').replace('_shard_', '_')
            output_json = os.path.join(variant_dir, f"nuscenes_impromptu_data_{variant}_{shard_suffix}.json")
            
            # JSON
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
            
            print(f"   ✅ {shard_name}: {len(qa_pairs)}  -> {output_json}")
            success_count += 1
        else:
            print(f"   ⚠️  {shard_name}: Generate")
    
    print(f"✅ {variant} Preprocessing completed！successProcessing {success_count}/{len(shards)} shard")
    return success_count > 0

def main():
    parser = argparse.ArgumentParser(description='shardProcessingnuScenesvariant，，GenerateImpromptu')
    parser.add_argument('--base_data_dir', type=str, required=True,
                       help='base data directory')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='output directory')
    parser.add_argument('--max_samples', type=int, default=None,
                       help='maximum samples per shard for testing')
    parser.add_argument('--variants', nargs='+', default=VARIANTS,
                       help='variants to process')
    parser.add_argument('--materialize_first_moment', action='store_true',
                       help='base_data_dir/cleantooutput_dir/clean，GenerateQA JSON')
    
    args = parser.parse_args()
    
    if args.materialize_first_moment:
        print("🚀 clean")
        print(f"📁 base data directory: {args.base_data_dir}")
        print(f"📁 output directory: {args.output_dir}")
        if args.max_samples:
            print(f"🔢 shardmaximum samples: {args.max_samples}")
        ok = materialize_clean_first_moment_dataset(args.base_data_dir, args.output_dir, args.max_samples)
        raise SystemExit(0 if ok else 1)

    print("🚀 shardProcessingnuScenesvariant（first timestamp only，Impromptu）")
    print(f"📁 base data directory: {args.base_data_dir}")
    print(f"📁 output directory: {args.output_dir}")
    if args.max_samples:
        print(f"🔢 shardmaximum samples: {args.max_samples}")
    print(f"📋 variants: {args.variants}")
    
    # output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process each variants
    success_count = 0
    total_count = len(args.variants)
    
    for variant in args.variants:
        try:
            if process_variant_by_shard_first_moment(args.base_data_dir, variant, args.output_dir, args.max_samples):
                success_count += 1
        except Exception as e:
            print(f"❌ variants {variant} : {e}")
    
    # Generate summary report
    summary = {
        "total_variants": total_count,
        "successful_variants": success_count,
        "failed_variants": total_count - success_count,
        "variants_processed": args.variants,
        "output_directory": args.output_dir,
        "max_samples_per_shard": args.max_samples,
        "note": "keep only the first timestamp of each scene，matching the nuscenes_impromptu_data_first_moment_v2.json format"
    }
    
    summary_file = os.path.join(args.output_dir, "preprocessing_summary_first_moment.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 Preprocessing completed！")
    print(f"✅ success: {success_count}/{total_count}")
    print(f"❌ failed: {total_count - success_count}/{total_count}")
    print(f"📄 summary report: {summary_file}")

if __name__ == "__main__":
    main()
