#!/usr/bin/env python3
"""Prepare fixed-subset temporal inference data without label balancing."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def parse_scene_id(scene_token: str) -> int:
    match = re.search(r"nuScences_(\d+)$", scene_token or "")
    return int(match.group(1)) if match else -1


def parse_frame_moment(frame_token: str) -> int:
    match = re.search(r"nuScences_\d+_(\d+)$", frame_token or "")
    return int(match.group(1)) if match else -1


def parse_temporal_setting(temporal_setting: str) -> int:
    match = re.match(r"(\d+)f$", temporal_setting or "")
    return int(match.group(1)) if match else -1


def sample_sort_key(item: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        item.get("source_shard", ""),
        parse_scene_id(item.get("scene_token", "")),
        parse_frame_moment(item.get("frame_token", "")),
        int(item.get("frame_count", -1)),
        parse_temporal_setting(item.get("temporal_setting", "")),
        item.get("source_json", ""),
    )


def load_json_list(json_file: Path) -> List[Dict[str, Any]]:
    with open(json_file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, list) else []


def collect_samples(
    input_dir: Path,
    question_type: str,
    allowed_temporal_settings: Iterable[str],
) -> Tuple[List[Dict[str, Any]], Counter]:
    allowed_set = set(allowed_temporal_settings)
    samples: List[Dict[str, Any]] = []
    source_counter: Counter = Counter()

    for json_file in sorted(input_dir.rglob("*.json")):
        if "summary" in json_file.name.lower():
            continue

        data = load_json_list(json_file)
        if not data:
            continue

        relative_path = str(json_file.relative_to(input_dir))
        for item in data:
            if not isinstance(item, dict):
                continue
            if item.get("question_type") != question_type:
                continue
            if item.get("temporal_setting") not in allowed_set:
                continue

            sample = dict(item)
            sample["source_json"] = relative_path
            sample["source_shard"] = sample.get("source_shard", "")
            sample["scene_uid"] = f"{sample.get('source_shard', '')}:{sample.get('scene_token', '')}"
            sample["frame_uid"] = f"{sample.get('source_shard', '')}:{sample.get('frame_token', '')}"
            source_counter[relative_path] += 1
            samples.append(sample)

    return sorted(samples, key=sample_sort_key), source_counter


def build_complete_anchor_groups(
    samples: List[Dict[str, Any]],
    allowed_temporal_settings: List[str],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    grouped: Dict[str, Dict[str, Any]] = {}

    for sample in samples:
        frame_uid = sample["frame_uid"]
        group = grouped.setdefault(frame_uid, {"frame_uid": frame_uid, "samples_by_setting": {}})
        setting = sample.get("temporal_setting", "")
        existing = group["samples_by_setting"].get(setting)
        if existing is None or sample_sort_key(sample) < sample_sort_key(existing):
            group["samples_by_setting"][setting] = sample

    complete_groups: List[Dict[str, Any]] = []
    dropped_frame_uids: List[str] = []

    for frame_uid, group in grouped.items():
        samples_by_setting = group["samples_by_setting"]
        if not all(setting in samples_by_setting for setting in allowed_temporal_settings):
            dropped_frame_uids.append(frame_uid)
            continue
        ordered_samples = [samples_by_setting[setting] for setting in allowed_temporal_settings]
        complete_groups.append({"frame_uid": frame_uid, "ordered_samples": ordered_samples, "representative": ordered_samples[0]})

    complete_groups.sort(key=lambda item: sample_sort_key(item["representative"]))
    dropped_frame_uids.sort()
    return complete_groups, dropped_frame_uids


def expand_groups(groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    expanded: List[Dict[str, Any]] = []
    for group in groups:
        expanded.extend(group["ordered_samples"])
    return sorted(expanded, key=sample_sort_key)


def build_summary(
    question_type: str,
    input_dir: Path,
    allowed_temporal_settings: List[str],
    source_counter: Counter,
    all_samples: List[Dict[str, Any]],
    complete_groups: List[Dict[str, Any]],
    dropped_frame_uids: List[str],
    selected_samples: List[Dict[str, Any]],
) -> Dict[str, Any]:
    temporal_counter = Counter(sample.get("temporal_setting", "unknown") for sample in selected_samples)
    shard_counter = Counter(sample.get("source_shard", "unknown") for sample in selected_samples)
    scene_counter = Counter(sample.get("scene_uid", "unknown") for sample in selected_samples)

    return {
        "question_type": question_type,
        "selection_basis": "fixed_subset_complete_anchors",
        "input_dir": str(input_dir),
        "allowed_temporal_settings": allowed_temporal_settings,
        "total_collected_samples": len(all_samples),
        "complete_anchor_count": len(complete_groups),
        "dropped_incomplete_anchor_count": len(dropped_frame_uids),
        "dropped_incomplete_frame_uids": dropped_frame_uids,
        "total_output_samples": len(selected_samples),
        "output_samples_per_anchor": len(allowed_temporal_settings),
        "temporal_settings_after": dict(sorted(temporal_counter.items(), key=lambda kv: parse_temporal_setting(kv[0]))),
        "shards_after": dict(sorted(shard_counter.items())),
        "scene_count_after": len(scene_counter),
        "source_files": dict(sorted(source_counter.items())),
        "selected_frame_uids": [group["frame_uid"] for group in complete_groups],
        "camera_policy": "front_only",
        "visible_latest_frame_label": "t-1",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare fixed-subset temporal inference data")
    parser.add_argument("--input_dir", type=str, required=True, help="switched temporal JSON directory")
    parser.add_argument("--output_json", type=str, required=True, help="output ordered inference JSON")
    parser.add_argument("--summary_json", type=str, required=True, help="output summary JSON")
    parser.add_argument("--question_type", type=str, required=True, choices=["q2.1", "q6"], help="question type to keep")
    parser.add_argument(
        "--allowed_temporal_settings",
        nargs="+",
        required=True,
        help="temporal settings to keep, in output order",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_json = Path(args.output_json)
    summary_json = Path(args.summary_json)

    if not input_dir.is_dir():
        raise FileNotFoundError(f"input_dir not found: {input_dir}")

    allowed_temporal_settings = list(args.allowed_temporal_settings)
    all_samples, source_counter = collect_samples(input_dir, args.question_type, allowed_temporal_settings)
    complete_groups, dropped_frame_uids = build_complete_anchor_groups(all_samples, allowed_temporal_settings)
    selected_samples = expand_groups(complete_groups)
    summary = build_summary(
        question_type=args.question_type,
        input_dir=input_dir,
        allowed_temporal_settings=allowed_temporal_settings,
        source_counter=source_counter,
        all_samples=all_samples,
        complete_groups=complete_groups,
        dropped_frame_uids=dropped_frame_uids,
        selected_samples=selected_samples,
    )

    output_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.parent.mkdir(parents=True, exist_ok=True)

    with open(output_json, "w", encoding="utf-8") as file:
        json.dump(selected_samples, file, ensure_ascii=False, indent=2)
    with open(summary_json, "w", encoding="utf-8") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)

    print(f"saved_ordered_input={output_json}")
    print(f"saved_summary={summary_json}")
    print(f"complete_anchor_count={summary['complete_anchor_count']}")
    print(f"total_output_samples={summary['total_output_samples']}")


if __name__ == "__main__":
    main()
