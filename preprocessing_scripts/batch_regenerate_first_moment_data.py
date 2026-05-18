#!/usr/bin/env python3
"""
Batch regenerate nuscenes_variants_by_shard_impromptu_full data
keep only the first timestamp of each scene，matching the nuscenes_impromptu_data_first_moment_v2.json format
"""

import os
import json
import argparse
import subprocess
import time
from datetime import datetime
from pathlib import Path

# 21 data variants
ALL_VARIANTS = [
    'backlight', 'bit_error', 'bright', 'clean', 'compress', 'crash', 'dark',
    'fog', 'frame_lost', 'glare', 'lens', 'lightning', 'motion_blur', 'quant',
    'rain', 'sandstorm', 'saturate', 'smoke', 'snow', 'splash', 'zoom_blur'
]

def check_variant_availability(base_data_dir: str) -> dict:
    """Checking variant availability"""
    print("🔍 Checking variant availability...")
    
    available_variants = {}
    
    for variant in ALL_VARIANTS:
        variant_dir = os.path.join(base_data_dir, variant)
        
        if os.path.exists(variant_dir):
            # Check shard directory count
            shard_dirs = [d for d in os.listdir(variant_dir) 
                         if d.startswith("nuScenes_train_shard_")]
            shard_dirs.sort()
            
            available_variants[variant] = {
                'path': variant_dir,
                'shard_count': len(shard_dirs),
                'shards': shard_dirs
            }
            
            print(f"✅ {variant}: {len(shard_dirs)} shard directories")
        else:
            print(f"❌ {variant}: directory not found")
    
    return available_variants

def preprocess_single_variant_first_moment(variant: str, base_data_dir: str, output_dir: str, 
                                         max_samples: int = None, skip_existing: bool = False) -> bool:
    """Preprocess one variant and keep only the first timestamp"""
    print(f"\n🔄 Start variant: {variant} (first timestamp only)")
    
    # Build command
    cmd = [
        "python", "preprocessing_scripts/preprocess_variants_by_shard_first_moment.py",
        "--base_data_dir", base_data_dir,
        "--output_dir", output_dir,
        "--variants", variant
    ]
    
    if max_samples:
        cmd.extend(["--max_samples", str(max_samples)])
    
    print(f"🚀 Running command: {' '.join(cmd)}")
    
    # Record start time
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 minute timeout
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {variant} Processingsuccess！duration: {duration:.1f}s")
            
            # Check output files
            variant_dir = os.path.join(output_dir, variant)
            if os.path.exists(variant_dir):
                json_files = [f for f in os.listdir(variant_dir) if f.endswith('.json')]
                print(f"📊 {variant} result: {len(json_files)} JSON files")
            
            return True
        else:
            print(f"❌ {variant} Processingfailed！duration: {duration:.1f}s")
            print(f"📄 error message: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {variant} preprocessing timed out！")
        return False
    except Exception as e:
        print(f"❌ {variant} preprocessing error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Batch regenerate nuscenes_variants_by_shard_impromptu_full data（first timestamp only）')
    parser.add_argument('--base_data_dir', type=str,
                       default='data/nuscenes_dataset_first',
                       help='base data directory')
    parser.add_argument('--output_dir', type=str,
                       default='./nuscenes_variants_by_shard_impromptu_full',
                       help='output directory')
    parser.add_argument('--max_samples', type=int, default=None,
                       help='maximum samples per shard for testing')
    parser.add_argument('--variants', type=str, nargs='+', default=ALL_VARIANTS,
                       help='variants to process，process all variants by default')
    parser.add_argument('--skip_existing', action='store_true', default=False,
                       help='skip existingoutput files')
    parser.add_argument('--parallel', type=int, default=1,
                       help='number of variants to process in parallel')
    
    args = parser.parse_args()
    
    print("🚀 Start batch regeneration of first-timestamp nuScenes variants")
    print(f"📁 base data directory: {args.base_data_dir}")
    print(f"📁 output directory: {args.output_dir}")
    print(f"🔢 maximum samples: {args.max_samples if args.max_samples else 'unlimited'}")
    print(f"📋 variants: {args.variants}")
    print(f"⏭️  skip existing: {args.skip_existing}")
    print(f"🔄 parallel jobs: {args.parallel}")
    
    # base data directory
    if not os.path.exists(args.base_data_dir):
        print(f"❌ base data directorynot found: {args.base_data_dir}")
        return
    
    # output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Check variant availability
    available_variants = check_variant_availability(args.base_data_dir)
    
    # Filter available variants
    variants_to_process = [v for v in args.variants if v in available_variants]
    
    if not variants_to_process:
        print("❌ No available variants to process")
        return
    
    print(f"\n📊 Will process {len(variants_to_process)} variants")
    
    # Record start time
    start_time = datetime.now()
    
    # variants
    successful_variants = []
    failed_variants = []
    
    for i, variant in enumerate(variants_to_process, 1):
        print(f"\n📋 Progress: {i}/{len(variants_to_process)}")
        
        success = preprocess_single_variant_first_moment(
            variant, 
            args.base_data_dir, 
            args.output_dir, 
            args.max_samples,
            args.skip_existing
        )
        
        if success:
            successful_variants.append(variant)
        else:
            failed_variants.append(variant)
    
    # Record end time
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    # Generate summary report
    summary = {
        'preprocessing_info': {
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_duration_seconds': total_duration,
            'total_variants': len(variants_to_process),
            'successful_variants': len(successful_variants),
            'failed_variants': len(failed_variants)
        },
        'successful_variants': successful_variants,
        'failed_variants': failed_variants,
        'available_variants': available_variants,
        'paths': {
            'base_data_dir': args.base_data_dir,
            'output_dir': args.output_dir
        },
        'parameters': {
            'max_samples': args.max_samples,
            'skip_existing': args.skip_existing,
            'parallel': args.parallel
        },
        'note': 'keep only the first timestamp of each scene，matching the nuscenes_impromptu_data_first_moment_v2.json format'
    }
    
    # Save summary report
    summary_file = os.path.join(args.output_dir, 'batch_regeneration_summary_first_moment.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    # result
    print(f"\n🎉 Batch regeneration completed！")
    print(f"⏰ Total duration: {total_duration:.1f}s ({total_duration/60:.1f}min)")
    print(f"📊 Results:")
    print(f"   ✅ success: {len(successful_variants)}/{len(variants_to_process)}")
    print(f"   ❌ failed: {len(failed_variants)}/{len(variants_to_process)}")
    
    if successful_variants:
        print(f"✅ successvariants:")
        for variant in successful_variants:
            print(f"   - {variant}")
    
    if failed_variants:
        print(f"❌ failedvariants:")
        for variant in failed_variants:
            print(f"   - {variant}")
    
    print(f"📄 summary report: {summary_file}")
    
    print(f"\n💡 Next steps:")
    print(f"   1. summary reportresult")
    print(f"   2. failedvariantsrerun")
    print(f"   3. Validate generated data format")
    print(f"   4. Run inference scripts for model evaluation")

if __name__ == "__main__":
    main()
