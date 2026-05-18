#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 nuscenes_switch  JSON  q7 
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any


def remove_q7_content_from_file(file_path: str) -> bool:
    """
     JSON  q7 
    
    Args:
        file_path: JSON 
        
    Returns:
        bool: successProcessing file
    """
    try:
        #  JSON 
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 
        if not isinstance(data, list):
            print(f": {file_path} ，SkipProcessing")
            return False
        
        #  q7 
        original_count = len(data)
        q7_count = sum(1 for item in data if item.get('question_type') == 'q7')
        
        #  q7 
        filtered_data = [item for item in data if item.get('question_type') != 'q7']
        
        # 
        filtered_count = len(filtered_data)
        
        #  q7 ，
        if q7_count > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=2)
            
            print(f"✓ {file_path}:  {q7_count}  q7  (: {original_count}, : {filtered_count})")
            return True
        else:
            print(f"- {file_path}:  q7 ")
            return True
            
    except Exception as e:
        print(f"✗ Processing file {file_path} : {e}")
        return False


def remove_q7_content_from_directory(directory_path: str) -> Dict[str, int]:
    """
     JSON Remove q7 entries
    
    Args:
        directory_path: 
        
    Returns:
        Dict[str, int]: Results
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f": directory not found: {directory_path}")
        return {"error": 1, "success": 0, "total": 0}
    
    #  JSON 
    json_files = list(directory.rglob('*.json'))
    
    if not json_files:
        print(f":  {directory_path} Found JSON ")
        return {"error": 0, "success": 0, "total": 0}
    
    print(f"Found {len(json_files)}  JSON ")
    print("=" * 60)
    
    success_count = 0
    error_count = 0
    
    # Process each  JSON 
    for json_file in json_files:
        if remove_q7_content_from_file(str(json_file)):
            success_count += 1
        else:
            error_count += 1
    
    print("=" * 60)
    print(f"ProcessingDone: success {success_count} , failed {error_count} ")
    
    return {
        "success": success_count,
        "error": error_count,
        "total": len(json_files)
    }


def main():
    """
    
    """
    #  preprocessing_scripts/question_switch/，Project root
    project_root = Path(__file__).resolve().parents[2]
    nuscenes_switch_dir = project_root / "nuscenes_switch"
    
    print("=" * 60)
    print("Remove q7 entries from JSON files under nuscenes_switch")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f": {nuscenes_switch_dir}")
    print()
    
    # 
    if not nuscenes_switch_dir.exists():
        print(f": nuscenes_switch directory not found: {nuscenes_switch_dir}")
        print("Run data preprocessing scriptGenerate")
        sys.exit(1)
    
    # Run
    results = remove_q7_content_from_directory(str(nuscenes_switch_dir))
    
    # result
    print()
    print("=" * 60)
    print("result:")
    print(f"  - : {results['total']}")
    print(f"  - successProcessing: {results['success']}")
    print(f"  - Processingfailed: {results['error']}")
    
    if results['error'] > 0:
        print(f"  -  {results['error']} Processingfailed，error message")
        # failed（failed）
        # failed
        directory = Path(nuscenes_switch_dir)
        json_files = list(directory.rglob('*.json'))
        failed_files = []
        for json_file in json_files:
            if not remove_q7_content_from_file(str(json_file)):
                failed_files.append(str(json_file))
        
        # failed，success
        summary_files = [f for f in failed_files if 'summary' in f.lower()]
        if len(summary_files) == results['error']:
            print("  - failed，")
            print("  - q7 ")
        else:
            print("  - Processingfailed，error message")
            sys.exit(1)
    else:
        print("  - Processingsuccess！")
        print("  - q7 ")


if __name__ == '__main__':
    main()
