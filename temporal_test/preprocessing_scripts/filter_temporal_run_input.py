#!/usr/bin/env python3
"""Filter ordered temporal inputs for probing or model-specific max-frame runs."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List


def parse_temporal_setting(temporal_setting: str) -> int:
    match = re.match(r"(\d+)f$", temporal_setting or "")
    return int(match.group(1)) if match else -1


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter temporal ordered inputs")
    parser.add_argument("--input_json", type=str, required=True)
    parser.add_argument("--output_json", type=str, required=True)
    parser.add_argument("--input_summary_json", type=str, default="")
    parser.add_argument("--output_summary_json", type=str, default="")
    parser.add_argument("--max_frame_count", type=int, default=0, help="keep settings <= this count")
    parser.add_argument("--exact_frame_count", type=int, default=0, help="keep settings == this count")
    parser.add_argument("--max_samples", type=int, default=0, help="keep at most N samples after filtering")
    args = parser.parse_args()

    if args.max_frame_count > 0 and args.exact_frame_count > 0:
        raise SystemExit("use only one of --max_frame_count and --exact_frame_count")

    input_json = Path(args.input_json)
    output_json = Path(args.output_json)
    samples = load_json(input_json)
    if not isinstance(samples, list):
        raise SystemExit(f"input_json is not a list: {input_json}")

    filtered: List[Dict[str, Any]] = []
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        frame_count = parse_temporal_setting(sample.get("temporal_setting", ""))
        if args.exact_frame_count > 0 and frame_count != args.exact_frame_count:
            continue
        if args.max_frame_count > 0 and frame_count > args.max_frame_count:
            continue
        filtered.append(sample)

    if args.max_samples > 0:
        filtered = filtered[: args.max_samples]

    dump_json(output_json, filtered)

    if args.input_summary_json and args.output_summary_json:
        input_summary = load_json(Path(args.input_summary_json))
        if not isinstance(input_summary, dict):
            input_summary = {}

        temporal_counter: Dict[str, int] = {}
        selected_frame_uids: List[str] = []
        seen_frame_uids = set()
        for sample in filtered:
            temporal_setting = sample.get("temporal_setting", "unknown")
            temporal_counter[temporal_setting] = temporal_counter.get(temporal_setting, 0) + 1
            frame_uid = sample.get("frame_uid")
            if frame_uid and frame_uid not in seen_frame_uids:
                seen_frame_uids.add(frame_uid)
                selected_frame_uids.append(frame_uid)

        output_summary = dict(input_summary)
        output_summary["total_output_samples"] = len(filtered)
        output_summary["complete_anchor_count"] = len(selected_frame_uids)
        output_summary["selected_frame_uids"] = selected_frame_uids
        output_summary["temporal_settings_after"] = dict(sorted(temporal_counter.items(), key=lambda kv: parse_temporal_setting(kv[0])))
        if args.max_frame_count > 0:
            output_summary["max_evaluated_frame_count"] = args.max_frame_count
        if args.exact_frame_count > 0:
            output_summary["exact_probe_frame_count"] = args.exact_frame_count
        dump_json(Path(args.output_summary_json), output_summary)

    print(f"saved_filtered_input={output_json}")
    print(f"filtered_sample_count={len(filtered)}")


if __name__ == "__main__":
    main()
