#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
temporal test 
Processing Q2  Q6
"""

import json
import os
from pathlib import Path

from switchq2 import convert_q2_temporal_to_multiple_choice
from switchq6 import convert_q6_temporal_to_multiple_choice


def convert_question_by_type(data):
    """questionquestion"""
    question_type = data.get("question_type", "")
    if question_type == "q2":
        return [convert_q2_temporal_to_multiple_choice(data)]
    if question_type == "q6":
        return [convert_q6_temporal_to_multiple_choice(data)]
    return [data]


def process_data_file(input_file: str, output_file: str):
    """Processing JSON """
    print(f"Processing file: {input_file}")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"Skipsample: {input_file}")
        return

    converted_data = []
    for item in data:
        try:
            converted_data.extend(convert_question_by_type(item))
        except Exception as exc:
            print(f"Error while converting question: {exc}")
            converted_data.append(item)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=2)

    print(f"Done，to: {output_file}")
    print(f"question: {len(data)}, question: {len(converted_data)}")


def process_directory(input_dir: str, output_dir: str, overwrite: bool = False):
    """Processing"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for json_file in input_path.rglob("*.json"):
        if "summary" in json_file.name.lower():
            print(f"Skip: {json_file}")
            continue
        relative_path = json_file.relative_to(input_path)
        output_file = output_path / relative_path

        if output_file.exists() and not overwrite:
            print(f"skip existing: {output_file}")
            continue

        process_data_file(str(json_file), str(output_file))


def main():
    import argparse

    script_dir = Path(__file__).parent.parent.parent
    default_input = script_dir / "nuscenes_temporal_test_raw"
    default_output = script_dir / "nuscenes_temporal_test_switch"

    parser = argparse.ArgumentParser(description="temporal Q2/Q6 ")
    parser.add_argument("--input_path", default=str(default_input), help=f"，: {default_input}")
    parser.add_argument("--output_path", default=str(default_output), help=f"，: {default_output}")
    parser.add_argument("--overwrite", action="store_true", help="")
    args = parser.parse_args()

    input_path = Path(args.input_path)
    output_path = Path(args.output_path)

    print(f": {input_path}")
    print(f": {output_path}")
    print(f"mode: {'' if args.overwrite else ''}")
    print("-" * 50)

    if input_path.is_file():
        process_data_file(str(input_path), str(output_path))
    elif input_path.is_dir():
        process_directory(str(input_path), str(output_path), args.overwrite)
    else:
        print(f"not found: {input_path}")


if __name__ == "__main__":
    main()
