#!/bin/bash

set -euo pipefail

RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${RUN_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

REQUESTED_REBUILD_FROM_CLEAN="${REBUILD_FROM_CLEAN:-false}"
CLEAN_OUTPUT="${CLEAN_OUTPUT:-false}"

BASE_CLEAN_DIR="${BASE_CLEAN_DIR:-data/nuscenes_dataset/clean}"
SHARD_GLOB="${SHARD_GLOB:-nuScenes_*_shard_*}"
VARIANT="${VARIANT:-clean}"
ANCHOR_INDEX="${ANCHOR_INDEX:-10}"
MAX_SCENES_PER_SHARD="${MAX_SCENES_PER_SHARD:-0}"

RAW_DIR="${PROJECT_ROOT}/nuscenes_temporal_test_raw"
SWITCH_DIR="${PROJECT_ROOT}/nuscenes_temporal_test_switch"
INPUT_DIR="${RUN_DIR}/inputs"

Q2_OUTPUT_JSON="${INPUT_DIR}/q2_fixed_subset_front_history_1f_to_10f_ordered.json"
Q2_SUMMARY_JSON="${INPUT_DIR}/q2_fixed_subset_front_history_1f_to_10f_summary.json"
Q6_OUTPUT_JSON="${INPUT_DIR}/q6_fixed_subset_front_history_1f_to_10f_ordered.json"
Q6_SUMMARY_JSON="${INPUT_DIR}/q6_fixed_subset_front_history_1f_to_10f_summary.json"

BUILD_SCRIPT="${PROJECT_ROOT}/preprocessing_scripts/build_temporal_test_data.py"
CONVERTER_SCRIPT="${PROJECT_ROOT}/question_switch/utils_switch/main_converter.py"
PREPARE_SCRIPT="${PROJECT_ROOT}/preprocessing_scripts/prepare_fixed_subset_temporal_inference_data.py"

ALLOWED_SETTINGS=(1f 2f 3f 4f 5f 6f 7f 8f 9f 10f)

SHOULD_REBUILD_FROM_CLEAN="${REQUESTED_REBUILD_FROM_CLEAN}"
if [ ! -d "${SWITCH_DIR}" ] && [ "${SHOULD_REBUILD_FROM_CLEAN}" != "true" ]; then
    SHOULD_REBUILD_FROM_CLEAN="true"
fi

echo "=========================================="
echo "Prepare fixed-subset front-history 1..10 data"
echo "project_root=${PROJECT_ROOT}"
echo "rebuild_from_clean=${SHOULD_REBUILD_FROM_CLEAN}"
echo "clean_output=${CLEAN_OUTPUT}"
echo "anchor_index=${ANCHOR_INDEX}"
echo "=========================================="

mkdir -p "${INPUT_DIR}"

if [ "${CLEAN_OUTPUT}" = "true" ]; then
    rm -f "${Q2_OUTPUT_JSON}" "${Q2_SUMMARY_JSON}" "${Q6_OUTPUT_JSON}" "${Q6_SUMMARY_JSON}"
fi

if [ "${SHOULD_REBUILD_FROM_CLEAN}" = "true" ]; then
    if [ ! -d "${BASE_CLEAN_DIR}" ]; then
        echo "ERROR: base clean dir not found: ${BASE_CLEAN_DIR}"
        exit 1
    fi

    mapfile -t SHARD_DIRS < <(find "${BASE_CLEAN_DIR}" -maxdepth 1 -mindepth 1 -type d -name "${SHARD_GLOB}" | sort)
    if [ "${#SHARD_DIRS[@]}" -eq 0 ]; then
        echo "ERROR: no shard directories found under ${BASE_CLEAN_DIR}"
        exit 1
    fi

    if [ "${CLEAN_OUTPUT}" = "true" ]; then
        rm -rf "${RAW_DIR}" "${SWITCH_DIR}"
    fi
    mkdir -p "${RAW_DIR}" "${SWITCH_DIR}"

    echo "Building raw temporal data from clean shards"
    for shard_dir in "${SHARD_DIRS[@]}"; do
        echo "building shard=${shard_dir}"
        "${PYTHON_BIN}" "${BUILD_SCRIPT}" \
            --base_shard_dir "${shard_dir}" \
            --output_dir "${RAW_DIR}" \
            --variant "${VARIANT}" \
            --anchor_index "${ANCHOR_INDEX}" \
            --max_scenes "${MAX_SCENES_PER_SHARD}"
    done

    echo "Converting raw temporal data to switch format"
    "${PYTHON_BIN}" "${CONVERTER_SCRIPT}" \
        --input_path "${RAW_DIR}" \
        --output_path "${SWITCH_DIR}" \
        --overwrite
fi

if [ ! -d "${SWITCH_DIR}" ]; then
    echo "ERROR: switched temporal dir not found: ${SWITCH_DIR}"
    exit 1
fi

echo "Preparing fixed-subset Q2 input"
"${PYTHON_BIN}" "${PREPARE_SCRIPT}" \
    --input_dir "${SWITCH_DIR}" \
    --output_json "${Q2_OUTPUT_JSON}" \
    --summary_json "${Q2_SUMMARY_JSON}" \
    --question_type "q2.1" \
    --allowed_temporal_settings "${ALLOWED_SETTINGS[@]}"

echo "Preparing fixed-subset Q6 input"
"${PYTHON_BIN}" "${PREPARE_SCRIPT}" \
    --input_dir "${SWITCH_DIR}" \
    --output_json "${Q6_OUTPUT_JSON}" \
    --summary_json "${Q6_SUMMARY_JSON}" \
    --question_type "q6" \
    --allowed_temporal_settings "${ALLOWED_SETTINGS[@]}"

echo "=========================================="
echo "Prepared Q2 input: ${Q2_OUTPUT_JSON}"
echo "Prepared Q6 input: ${Q6_OUTPUT_JSON}"
echo "=========================================="
