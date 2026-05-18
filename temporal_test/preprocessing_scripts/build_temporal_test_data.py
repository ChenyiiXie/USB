#!/usr/bin/env python3
"""
Build front-only temporal test data from raw nuScenes clean shards.

Experiment definition:
- use the earliest `anchor_index` valid frames from each scene
- use the last frame in that fixed window as the supervision anchor
- only expose historical front-view images ending at t-1
- generate 1f..anchor_index settings from the shared fixed window
"""

from __future__ import annotations

import argparse
import json
import os
import re
from typing import Any, Dict, List, Tuple


CAMERA_ORDER = ["CAM_FRONT"]


def parse_q2_answer(answer: str) -> Tuple[str | None, str | None]:
    patterns = [
        r"Object 1:\s*(\w+),\s*(\w+)",
        r"<DYNAMIC OBJECTS>Object 1:\s*(\w+),\s*(\w+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, answer or "", re.MULTILINE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
    return None, None


def parse_q6_answer(answer: str) -> Tuple[str | None, str | None]:
    match = re.search(r"<SPEED PATH PLAN>(\w+),\s*(\w+)", answer or "")
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return None, None


def extract_object1_from_question(question: str) -> Dict[str, Any] | None:
    pattern = (
        r"Object 1:\s*([^,]+),\s*(\d+)\s*meters\s*ahead,\s*(\d+)\s*meters\s*to\s*the\s*"
        r"(left|right),\s*speed\s*of\s*(\d+)\s*m/s\."
    )
    match = re.search(pattern, question or "", re.IGNORECASE)
    if not match:
        return None
    obj_type, distance, offset, direction, speed = match.groups()
    return {
        "type": obj_type.strip(),
        "distance": int(distance),
        "offset": int(offset),
        "direction": direction.strip(),
        "speed": int(speed),
    }


def collect_scene_frames(shard_dir: str) -> Dict[str, List[int]]:
    scene_frames: Dict[str, List[int]] = {}
    for filename in os.listdir(shard_dir):
        match = re.match(r"nuScences_(\d+)_([0-9]+)\.CAM_FRONT\.png$", filename)
        if not match:
            continue
        scene_id = match.group(1)
        moment = int(match.group(2))
        scene_frames.setdefault(scene_id, []).append(moment)

    for scene_id, moments in list(scene_frames.items()):
        scene_frames[scene_id] = sorted(set(moments))
    return scene_frames


def build_sample_prefix(shard_dir: str, scene_id: str, moment: int) -> str:
    return os.path.join(shard_dir, f"nuScences_{scene_id}_{moment}")


def build_image_path(shard_dir: str, scene_id: str, moment: int) -> str:
    return os.path.join(shard_dir, f"nuScences_{scene_id}_{moment}.CAM_FRONT.png")


def load_text_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read().strip()


def is_scene_eligible(shard_dir: str, scene_id: str, frames: List[int], anchor_index: int) -> bool:
    if len(frames) < anchor_index:
        return False

    fixed_window = frames[:anchor_index]
    anchor_moment = fixed_window[-1]
    prefix = build_sample_prefix(shard_dir, scene_id, anchor_moment)

    required_text_files = [
        f"{prefix}.q2_question.txt",
        f"{prefix}.q2_answer.txt",
        f"{prefix}.q6_question.txt",
        f"{prefix}.q6_answer.txt",
    ]
    if not all(os.path.exists(path) for path in required_text_files):
        return False

    if not all(os.path.exists(build_image_path(shard_dir, scene_id, moment)) for moment in fixed_window):
        return False

    q2_question = load_text_file(f"{prefix}.q2_question.txt")
    q2_answer = load_text_file(f"{prefix}.q2_answer.txt")
    q6_answer = load_text_file(f"{prefix}.q6_answer.txt")

    q2_speed, q2_path = parse_q2_answer(q2_answer)
    q6_speed, q6_path = parse_q6_answer(q6_answer)
    object1 = extract_object1_from_question(q2_question)
    return bool(q2_speed and q2_path and q6_speed and q6_path and object1)


def select_test_scenes(shard_dir: str, anchor_index: int, max_scenes: int) -> List[Dict[str, Any]]:
    scene_frames = collect_scene_frames(shard_dir)
    selected_scenes: List[Dict[str, Any]] = []

    for scene_id in sorted(scene_frames, key=lambda value: int(value)):
        frames = scene_frames[scene_id]
        if not is_scene_eligible(shard_dir, scene_id, frames, anchor_index):
            continue

        fixed_window = frames[:anchor_index]
        selected_scenes.append(
            {
                "scene_id": scene_id,
                "fixed_window_frames": fixed_window,
                "anchor_moment": fixed_window[-1],
            }
        )
        if max_scenes > 0 and len(selected_scenes) >= max_scenes:
            break

    return selected_scenes


def format_temporal_key(relative_index: int) -> str:
    return f"T_MINUS_{relative_index}_CAM_FRONT"


def build_temporal_image_paths(
    shard_dir: str,
    scene_id: str,
    fixed_window_frames: List[int],
    frame_count: int,
) -> Dict[str, str]:
    image_paths: Dict[str, str] = {}
    start_index = len(fixed_window_frames) - frame_count

    for absolute_index in range(start_index, len(fixed_window_frames)):
        moment = fixed_window_frames[absolute_index]
        relative_index = len(fixed_window_frames) - absolute_index
        image_path = build_image_path(shard_dir, scene_id, moment)
        if os.path.exists(image_path):
            image_paths[format_temporal_key(relative_index)] = image_path

    return image_paths


def build_temporal_frames(fixed_window_frames: List[int], scene_id: str, frame_count: int) -> List[Dict[str, Any]]:
    temporal_frames: List[Dict[str, Any]] = []
    start_index = len(fixed_window_frames) - frame_count

    for absolute_index in range(start_index, len(fixed_window_frames)):
        moment = fixed_window_frames[absolute_index]
        relative_index = len(fixed_window_frames) - absolute_index
        temporal_frames.append(
            {
                "label": f"t-{relative_index}",
                "moment": moment,
                "sample_token": f"nuScences_{scene_id}_{moment}",
            }
        )
    return temporal_frames


def build_temporal_entry(
    shard_dir: str,
    scene_id: str,
    fixed_window_frames: List[int],
    frame_count: int,
    question_type: str,
) -> Dict[str, Any]:
    anchor_moment = fixed_window_frames[-1]
    prefix = build_sample_prefix(shard_dir, scene_id, anchor_moment)
    q_num = 2 if question_type == "q2" else 6

    question = load_text_file(f"{prefix}.q{q_num}_question.txt")
    answer = load_text_file(f"{prefix}.q{q_num}_answer.txt")
    image_paths = build_temporal_image_paths(shard_dir, scene_id, fixed_window_frames, frame_count)
    temporal_frames = build_temporal_frames(fixed_window_frames, scene_id, frame_count)

    return {
        "scene_token": f"nuScences_{scene_id}",
        "frame_token": f"nuScences_{scene_id}_{anchor_moment}",
        "anchor_frame_token": f"nuScences_{scene_id}_{anchor_moment}",
        "question_type": question_type,
        "question": question,
        "answer": answer,
        "tag": [q_num - 1],
        "image_path": image_paths,
        "frame_count": frame_count,
        "temporal_setting": f"{frame_count}f",
        "temporal_frames": temporal_frames,
        "source_shard": os.path.basename(shard_dir),
        "camera_policy": "front_only",
        "visible_latest_frame_label": "t-1",
        "supervision_frame_label": "t-1",
    }


def build_temporal_dataset(
    shard_dir: str,
    anchor_index: int,
    max_scenes: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    selected_scenes = select_test_scenes(shard_dir, anchor_index, max_scenes)
    dataset: List[Dict[str, Any]] = []

    for scene_info in selected_scenes:
        scene_id = scene_info["scene_id"]
        fixed_window_frames = scene_info["fixed_window_frames"]

        for frame_count in range(1, anchor_index + 1):
            dataset.append(build_temporal_entry(shard_dir, scene_id, fixed_window_frames, frame_count, "q2"))
            dataset.append(build_temporal_entry(shard_dir, scene_id, fixed_window_frames, frame_count, "q6"))

    summary = {
        "source_shard": os.path.basename(shard_dir),
        "anchor_index": anchor_index,
        "max_scenes_requested": max_scenes,
        "selected_scene_count": len(selected_scenes),
        "selected_scenes": selected_scenes,
        "total_samples": len(dataset),
        "question_types": {
            "q2": sum(1 for item in dataset if item["question_type"] == "q2"),
            "q6": sum(1 for item in dataset if item["question_type"] == "q6"),
        },
        "temporal_settings": {
            f"{i}f": sum(1 for item in dataset if item["temporal_setting"] == f"{i}f")
            for i in range(1, anchor_index + 1)
        },
        "camera_policy": "front_only",
        "visible_latest_frame_label": "t-1",
        "shared_fixed_window_size": anchor_index,
    }
    return dataset, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build front-only temporal 1..N test data")
    parser.add_argument(
        "--base_shard_dir",
        type=str,
        default="data/nuscenes_dataset/clean/nuScenes_train_shard_0000",
        help="source clean shard directory",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./nuscenes_temporal_test_raw",
        help="output root directory",
    )
    parser.add_argument(
        "--variant",
        type=str,
        default="clean",
        help="output variant name",
    )
    parser.add_argument(
        "--anchor_index",
        type=int,
        default=10,
        help="fixed window size; the last frame in this window is the supervision anchor",
    )
    parser.add_argument(
        "--max_scenes",
        type=int,
        default=0,
        help="max number of scenes to keep; <=0 keeps all eligible scenes",
    )
    args = parser.parse_args()

    print("Starting front-only temporal 1..N preprocessing")
    print(f"source_shard={args.base_shard_dir}")
    print(f"output_dir={args.output_dir}")
    print(f"variant={args.variant}")
    print(f"anchor_index={args.anchor_index}")
    print(f"max_scenes={args.max_scenes}")

    if not os.path.isdir(args.base_shard_dir):
        raise FileNotFoundError(f"source shard not found: {args.base_shard_dir}")

    dataset, summary = build_temporal_dataset(args.base_shard_dir, args.anchor_index, args.max_scenes)

    variant_dir = os.path.join(args.output_dir, args.variant)
    os.makedirs(variant_dir, exist_ok=True)

    shard_name = os.path.basename(args.base_shard_dir)
    shard_suffix = shard_name.replace("nuScenes_", "")
    output_json = os.path.join(variant_dir, f"nuscenes_temporal_test_data_{args.variant}_{shard_suffix}.json")
    summary_json = os.path.join(variant_dir, f"nuscenes_temporal_test_summary_{args.variant}_{shard_suffix}.json")

    with open(output_json, "w", encoding="utf-8") as file:
        json.dump(dataset, file, ensure_ascii=False, indent=2)
    with open(summary_json, "w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)

    print(f"saved_dataset={output_json}")
    print(f"saved_summary={summary_json}")
    print(f"selected_scene_count={summary['selected_scene_count']}")
    print(f"total_samples={summary['total_samples']}")


if __name__ == "__main__":
    main()
