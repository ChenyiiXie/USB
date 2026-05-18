#!/usr/bin/env python3
"""
Pack temporal multiple-choice inference results into a single structured JSON.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


OPTION_PATTERN = re.compile(r"^([A-D])\.\s*(.+)$")


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_option_map(question: str) -> Dict[str, str]:
    option_map: Dict[str, str] = {}
    for raw_line in (question or "").splitlines():
        line = raw_line.strip()
        match = OPTION_PATTERN.match(line)
        if match:
            option_map[match.group(1)] = match.group(2).strip()
    return option_map


def normalize_pred_letter(pred: Any) -> Optional[str]:
    if pred is None:
        return None

    text = str(pred).strip().upper()
    if not text:
        return None
    if text in {"A", "B", "C", "D"}:
        return text

    match = re.search(r"\b([A-D])\b", text)
    if match:
        return match.group(1)

    match = re.match(r"^([A-D])(?:[^A-Z]|$)", text)
    if match:
        return match.group(1)

    return None


def split_joint_answer(answer: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not answer or "," not in answer:
        return None, None
    speed, path = answer.split(",", 1)
    return speed.strip(), path.strip()


def safe_accuracy(correct: int, total: int) -> Optional[float]:
    if total <= 0:
        return None
    return correct / total


def compute_metrics(results: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    result_list = list(results)
    total = len(result_list)

    exact_correct = 0
    speed_correct = 0
    path_correct = 0

    per_temporal_total: Counter = Counter()
    per_temporal_correct: Counter = Counter()
    per_label_total: Counter = Counter()
    per_label_correct: Counter = Counter()

    for item in result_list:
        temporal_setting = item.get("temporal_setting", "unknown")
        correct_answer = item.get("correct_answer") or "unknown"

        per_temporal_total[temporal_setting] += 1
        per_label_total[correct_answer] += 1

        if item.get("is_correct"):
            exact_correct += 1
            per_temporal_correct[temporal_setting] += 1
            per_label_correct[correct_answer] += 1

        if item.get("pred_speed") and item.get("pred_speed") == item.get("correct_speed"):
            speed_correct += 1
        if item.get("pred_path") and item.get("pred_path") == item.get("correct_path"):
            path_correct += 1

    return {
        "total_samples": total,
        "exact_mcqa_accuracy": safe_accuracy(exact_correct, total),
        "joint_state_accuracy": safe_accuracy(exact_correct, total),
        "speed_accuracy": safe_accuracy(speed_correct, total),
        "path_accuracy": safe_accuracy(path_correct, total),
        "accuracy_by_temporal_setting": {
            key: {
                "correct": per_temporal_correct[key],
                "total": per_temporal_total[key],
                "accuracy": safe_accuracy(per_temporal_correct[key], per_temporal_total[key]),
            }
            for key in sorted(per_temporal_total.keys(), key=lambda value: int(value[:-1]) if value.endswith("f") else 9999)
        },
        "accuracy_by_correct_answer": {
            key: {
                "correct": per_label_correct[key],
                "total": per_label_total[key],
                "accuracy": safe_accuracy(per_label_correct[key], per_label_total[key]),
            }
            for key in sorted(per_label_total.keys())
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Pack temporal MCQA inference results")
    parser.add_argument("--ordered_input_json", type=str, required=True)
    parser.add_argument("--raw_output_json", type=str, required=True)
    parser.add_argument("--combined_output_json", type=str, required=True)
    parser.add_argument("--question_type", type=str, required=True)
    parser.add_argument("--model_family", type=str, required=True)
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--input_summary_json", type=str, required=False, default="")
    args = parser.parse_args()

    ordered_input_json = Path(args.ordered_input_json)
    raw_output_json = Path(args.raw_output_json)
    combined_output_json = Path(args.combined_output_json)
    input_summary_json = Path(args.input_summary_json) if args.input_summary_json else None

    ordered_input = load_json(ordered_input_json)
    raw_output = load_json(raw_output_json)
    input_summary = load_json(input_summary_json) if input_summary_json and input_summary_json.exists() else None

    if not isinstance(ordered_input, list):
        raise SystemExit(f"ordered_input_json is not a list: {ordered_input_json}")
    if not isinstance(raw_output, list):
        raise SystemExit(f"raw_output_json is not a list: {raw_output_json}")
    if len(ordered_input) != len(raw_output):
        raise SystemExit(f"Input/output length mismatch: {len(ordered_input)} vs {len(raw_output)}")

    payload: Dict[str, Any] = {
        "question_type": args.question_type,
        "model_family": args.model_family,
        "model_path": args.model_path,
        "raw_output_file": str(raw_output_json),
        "input_summary_file": str(input_summary_json) if input_summary is not None and input_summary_json else None,
        "input_summary": input_summary,
        "total_samples": len(ordered_input),
        "results": [],
    }

    for idx, (sample, prediction) in enumerate(zip(ordered_input, raw_output), start=1):
        pred_raw = prediction.get("pred") if isinstance(prediction, dict) else prediction
        pred_letter = normalize_pred_letter(pred_raw)
        option_map = extract_option_map(sample.get("question", ""))
        pred_answer = option_map.get(pred_letter)
        correct_answer = sample.get("correct_answer")
        correct_letter = sample.get("answer")

        correct_speed, correct_path = split_joint_answer(correct_answer)
        pred_speed, pred_path = split_joint_answer(pred_answer)

        payload["results"].append(
            {
                "run_index": idx,
                "source_shard": sample.get("source_shard"),
                "scene_uid": sample.get("scene_uid"),
                "frame_uid": sample.get("frame_uid"),
                "temporal_setting": sample.get("temporal_setting"),
                "frame_count": sample.get("frame_count"),
                "scene_token": sample.get("scene_token"),
                "frame_token": sample.get("frame_token"),
                "question_type": sample.get("question_type"),
                "correct_letter": correct_letter,
                "correct_answer": correct_answer,
                "correct_speed": correct_speed,
                "correct_path": correct_path,
                "pred_raw": pred_raw,
                "pred_letter": pred_letter,
                "pred_answer": pred_answer,
                "pred_speed": pred_speed,
                "pred_path": pred_path,
                "is_correct": pred_letter == correct_letter,
                "question": sample.get("question"),
                "image_path": sample.get("image_path"),
                "temporal_frames": sample.get("temporal_frames"),
                "source_json": sample.get("source_json"),
            }
        )

    payload["metrics"] = compute_metrics(payload["results"])

    combined_output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(combined_output_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"saved combined ordered results: {combined_output_json}")
    print(f"total_samples={payload['total_samples']}")
    print(f"exact_mcqa_accuracy={payload['metrics']['exact_mcqa_accuracy']}")
    print(f"speed_accuracy={payload['metrics']['speed_accuracy']}")
    print(f"path_accuracy={payload['metrics']['path_accuracy']}")


if __name__ == "__main__":
    main()
