#!/bin/bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "This script is intended to be sourced by a run_temporal wrapper."
    exit 1
fi

set -euo pipefail

: "${MODEL_IDS:?MODEL_IDS must be defined by the wrapper script}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUN_DIR="${PROJECT_ROOT}/run_temporal"
PYTHON_BIN="${PYTHON_BIN:-python}"
DEFAULT_MAIN_PROJECT_ROOT="$(cd "${PROJECT_ROOT}/.." && pwd)"
MAIN_PROJECT_ROOT="${MAIN_PROJECT_ROOT:-${DEFAULT_MAIN_PROJECT_ROOT}}"
MODEL_BASE_PATH="${MODEL_BASE_PATH:-${MAIN_PROJECT_ROOT}/models}"

PREPARE_SCRIPT="${RUN_DIR}/run_prepare_fixed_subset_front_history_1to10.sh"
FILTER_SCRIPT="${PROJECT_ROOT}/preprocessing_scripts/filter_temporal_run_input.py"
PACK_SCRIPT="${PROJECT_ROOT}/preprocessing_scripts/pack_temporal_mcqa_results.py"
SYSTEM_PROMPT="${MAIN_PROJECT_ROOT}/inference/prompt.txt"

INPUT_DIR="${RUN_DIR}/inputs"
RESULT_ROOT="${RUN_DIR}/results"
PROBE_ROOT="${RUN_DIR}/probe"
CACHE_JSON="${RUN_DIR}/model_image_limits.json"

Q2_INPUT_JSON="${INPUT_DIR}/q2_fixed_subset_front_history_1f_to_10f_ordered.json"
Q2_INPUT_SUMMARY_JSON="${INPUT_DIR}/q2_fixed_subset_front_history_1f_to_10f_summary.json"
Q6_INPUT_JSON="${INPUT_DIR}/q6_fixed_subset_front_history_1f_to_10f_ordered.json"
Q6_INPUT_SUMMARY_JSON="${INPUT_DIR}/q6_fixed_subset_front_history_1f_to_10f_summary.json"

NUM_PROCESSES="${NUM_PROCESSES:-1}"
BATCH_SIZE="${BATCH_SIZE:-1}"
TEMPERATURE="${TEMPERATURE:-0.7}"
TOP_P="${TOP_P:-0.8}"
MAX_TOKENS="${MAX_TOKENS:-64}"
PROBE_MAX_TOKENS="${PROBE_MAX_TOKENS:-16}"
FORCE_REPROBE="${FORCE_REPROBE:-false}"

mkdir -p "${RESULT_ROOT}" "${PROBE_ROOT}"

if [ ! -f "${PREPARE_SCRIPT}" ]; then
    echo "ERROR: prepare script not found: ${PREPARE_SCRIPT}"
    exit 1
fi
if [ ! -f "${FILTER_SCRIPT}" ]; then
    echo "ERROR: filter script not found: ${FILTER_SCRIPT}"
    exit 1
fi
if [ ! -f "${PACK_SCRIPT}" ]; then
    echo "ERROR: pack script not found: ${PACK_SCRIPT}"
    exit 1
fi
if [ ! -f "${SYSTEM_PROMPT}" ]; then
    echo "ERROR: system prompt not found: ${SYSTEM_PROMPT}"
    exit 1
fi

ensure_prepared_inputs() {
    if [ -f "${Q2_INPUT_JSON}" ] && [ -f "${Q6_INPUT_JSON}" ]; then
        return 0
    fi

    echo "Prepared inputs not found. Running preprocessing first."
    bash "${PREPARE_SCRIPT}"
}


resolve_model_config() {
    local model_id="$1"
    MODEL_EXTRA_ARGS=()

    case "${model_id}" in
        qwen3)
            MODEL_TAG="qwen3"
            MODEL_LABEL="Qwen3-VL-8B-Instruct"
            INFER_SCRIPT="${MAIN_PROJECT_ROOT}/inference/qwen3_vl_impromptu.py"
            MODEL_MAX_MODEL_LEN="${MAX_MODEL_LEN_QWEN3:-4096}"
            MODEL_PATH=""
            for candidate in \
                "${MODEL_BASE_PATH}/Qwen/Qwen3-VL-8B-Instruct" \
                "${MODEL_BASE_PATH}/._____temp/Qwen/Qwen3-VL-8B-Instruct"
            do
                if [ -e "${candidate}" ]; then
                    MODEL_PATH="${candidate}"
                    break
                fi
            done
            ;;
        llava16)
            MODEL_TAG="llava16"
            MODEL_LABEL="llava-v1.6-mistral-7b-hf"
            INFER_SCRIPT="${MAIN_PROJECT_ROOT}/inference/llava16_mistral_impromptu.py"
            MODEL_MAX_MODEL_LEN="${MAX_MODEL_LEN_LLAVA16:-4096}"
            MODEL_PATH=""
            for candidate in \
                "${MODEL_BASE_PATH}/llava-hf/llava-v1.6-mistral-7b-hf" \
                "${MODEL_BASE_PATH}/._____temp/llava-hf/llava-v1.6-mistral-7b-hf"
            do
                if [ -e "${candidate}" ]; then
                    MODEL_PATH="${candidate}"
                    break
                fi
            done
            ;;
        internvl35)
            MODEL_TAG="internvl35"
            MODEL_LABEL="InternVL3_5-8B-Instruct"
            INFER_SCRIPT="${MAIN_PROJECT_ROOT}/inference/internvl3_5_impromptu.py"
            MODEL_MAX_MODEL_LEN="${MAX_MODEL_LEN_INTERNVL35:-4096}"
            MODEL_PATH=""
            for candidate in \
                "${MODEL_BASE_PATH}/OpenGVLab/InternVL3_5-8B-Instruct" \
                "${MODEL_BASE_PATH}/._____temp/OpenGVLab/InternVL3_5-8B-Instruct" \
                "${MODEL_BASE_PATH}/._____temp/OOpenGVLab/InternVL3_5-8B-Instruct"
            do
                if [ -e "${candidate}" ]; then
                    MODEL_PATH="${candidate}"
                    break
                fi
            done
            ;;
        qwen25)
            MODEL_TAG="qwen25"
            MODEL_LABEL="Qwen2.5-VL-7B-Instruct"
            INFER_SCRIPT="${MAIN_PROJECT_ROOT}/inference/qwen2.5_transformer_impromptu.py"
            MODEL_MAX_MODEL_LEN="${MAX_MODEL_LEN_QWEN25:-4096}"
            MODEL_PATH=""
            for candidate in \
                "${MODEL_BASE_PATH}/Qwen/Qwen2.5-VL-7B-Instruct" \
                "${MODEL_BASE_PATH}/._____temp/Qwen/Qwen2.5-VL-7B-Instruct"
            do
                if [ -e "${candidate}" ]; then
                    MODEL_PATH="${candidate}"
                    break
                fi
            done
            ;;
        keye15)
            MODEL_TAG="keye15"
            MODEL_LABEL="Keye-VL-1_5-8B"
            INFER_SCRIPT="${MAIN_PROJECT_ROOT}/inference/Keye-VL-1_5-8B_impromptu.py"
            MODEL_MAX_MODEL_LEN="${MAX_MODEL_LEN_KEYE15:-8192}"
            MODEL_EXTRA_ARGS=("--vision_max_side" "${VISION_MAX_SIDE_KEYE15:-640}")
            MODEL_PATH=""
            for candidate in \
                "${MODEL_BASE_PATH}/Kwai-Keye/Keye-VL-1_5-8B" \
                "${MODEL_BASE_PATH}/._____temp/Kwai-Keye/Keye-VL-1_5-8B"
            do
                if [ -e "${candidate}" ]; then
                    MODEL_PATH="${candidate}"
                    break
                fi
            done
            ;;
        phi35)
            MODEL_TAG="phi35"
            MODEL_LABEL="Phi-3.5-vision-instruct"
            INFER_SCRIPT="${MAIN_PROJECT_ROOT}/inference/phi3_5_impromptu.py"
            MODEL_MAX_MODEL_LEN="${MAX_MODEL_LEN_PHI35:-131072}"
            MODEL_PATH=""
            for candidate in \
                "${MODEL_BASE_PATH}/LLM-Research/Phi-3.5-vision-instruct" \
                "${MODEL_BASE_PATH}/._____temp/LLM-Research/Phi-3.5-vision-instruct"
            do
                if [ -e "${candidate}" ]; then
                    MODEL_PATH="${candidate}"
                    break
                fi
            done
            ;;
        llava15)
            MODEL_TAG="llava15"
            MODEL_LABEL="llava-1.5-7b-hf"
            INFER_SCRIPT="${MAIN_PROJECT_ROOT}/inference/llava1.5_impromptu.py"
            MODEL_MAX_MODEL_LEN="${MAX_MODEL_LEN_LLAVA15:-4096}"
            MODEL_EXTRA_ARGS=("--gpu_memory_utilization" "${GPU_MEMORY_UTILIZATION_LLAVA15:-0.85}")
            MODEL_PATH=""
            for candidate in \
                "${MODEL_BASE_PATH}/llava-1.5-7b-hf" \
                "${MODEL_BASE_PATH}/._____temp/llava-1.5-7b-hf"
            do
                if [ -e "${candidate}" ]; then
                    MODEL_PATH="${candidate}"
                    break
                fi
            done
            ;;
        *)
            echo "ERROR: unsupported model id: ${model_id}"
            exit 1
            ;;
    esac

    if [ -z "${MODEL_PATH}" ]; then
        echo "ERROR: unable to resolve model path for ${model_id}"
        exit 1
    fi
    if [ ! -f "${INFER_SCRIPT}" ]; then
        echo "ERROR: inference script not found: ${INFER_SCRIPT}"
        exit 1
    fi
}


get_cached_limit() {
    local model_id="$1"
    if [ ! -f "${CACHE_JSON}" ]; then
        return 0
    fi
    "${PYTHON_BIN}" - "${CACHE_JSON}" "${model_id}" <<'PY'
import json
import sys

cache_path, model_id = sys.argv[1:]
try:
    with open(cache_path, "r", encoding="utf-8") as file:
        payload = json.load(file)
except Exception:
    sys.exit(0)

item = payload.get(model_id)
if isinstance(item, dict):
    value = item.get("max_supported_images")
    if isinstance(value, int) and value > 0:
        print(value)
PY
}


set_cached_limit() {
    local model_id="$1"
    local max_supported_images="$2"
    local model_label="$3"
    local model_path="$4"

    "${PYTHON_BIN}" - "${CACHE_JSON}" "${model_id}" "${max_supported_images}" "${model_label}" "${model_path}" <<'PY'
import json
import os
import sys
from datetime import datetime

cache_path, model_id, max_supported_images, model_label, model_path = sys.argv[1:]
payload = {}
if os.path.exists(cache_path):
    try:
        with open(cache_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, dict):
            payload = data
    except Exception:
        payload = {}

payload[model_id] = {
    "model_label": model_label,
    "model_path": model_path,
    "max_supported_images": int(max_supported_images),
    "updated_at": datetime.now().isoformat(timespec="seconds"),
}

os.makedirs(os.path.dirname(cache_path), exist_ok=True)
with open(cache_path, "w", encoding="utf-8") as file:
    json.dump(payload, file, ensure_ascii=False, indent=2)
PY
}


raw_output_has_expected_count() {
    local raw_output_json="$1"
    local expected_count="$2"
    "${PYTHON_BIN}" - "${raw_output_json}" "${expected_count}" <<'PY'
import json
import sys

path, expected = sys.argv[1], int(sys.argv[2])
try:
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)
except Exception:
    sys.exit(1)

if not isinstance(payload, list):
    sys.exit(1)
if len(payload) != expected:
    sys.exit(1)
sys.exit(0)
PY
}


probe_model_limit() {
    local model_id="$1"
    resolve_model_config "${model_id}"

    if [ "${FORCE_REPROBE}" != "true" ]; then
        local cached_limit
        cached_limit="$(get_cached_limit "${model_id}")"
        if [ -n "${cached_limit}" ]; then
            echo "[probe][${MODEL_TAG}] max_supported_images=${cached_limit} (cached)" >&2
            echo "${cached_limit}"
            return 0
        fi
    fi

    local model_probe_root="${PROBE_ROOT}/${MODEL_TAG}"
    mkdir -p "${model_probe_root}"

    local max_success=0
    local count
    for count in $(seq 1 10); do
        echo "[probe][${MODEL_TAG}] count=${count}" >&2
        local probe_input_json="${model_probe_root}/q2_probe_${count}f_input.json"
        local probe_summary_json="${model_probe_root}/q2_probe_${count}f_summary.json"
        local probe_output_prefix="${model_probe_root}/q2_probe_${count}f"
        local probe_raw_output_json="${probe_output_prefix}.json"
        local probe_log_file="${probe_output_prefix}.log"

        "${PYTHON_BIN}" "${FILTER_SCRIPT}" \
            --input_json "${Q2_INPUT_JSON}" \
            --output_json "${probe_input_json}" \
            --input_summary_json "${Q2_INPUT_SUMMARY_JSON}" \
            --output_summary_json "${probe_summary_json}" \
            --exact_frame_count "${count}" \
            --max_samples 1 \
            >/dev/null

        rm -f "${probe_raw_output_json}" "${probe_log_file}"
        rm -rf "${model_probe_root}/individual_results"

        set +e
        (
            cd "${MAIN_PROJECT_ROOT}"
            "${PYTHON_BIN}" "${INFER_SCRIPT}" \
                --model "${MODEL_PATH}" \
                --data "${probe_input_json}" \
                --output "${probe_output_prefix}" \
                --system_prompt "${SYSTEM_PROMPT}" \
                --num_images_per_prompt "${count}" \
                --max_model_len "${MODEL_MAX_MODEL_LEN}" \
                --num_processes 1 \
                --batch_size 1 \
                --temperature 0.7 \
                --top_p 0.8 \
                --max_tokens "${PROBE_MAX_TOKENS}" \
                "${MODEL_EXTRA_ARGS[@]}" \
                --max_samples 1
        ) >"${probe_log_file}" 2>&1
        local exit_code=$?
        set -e

        if [ "${exit_code}" -ne 0 ]; then
            echo "[probe][${MODEL_TAG}] stop_at=${count} reason=inference_error log=${probe_log_file}" >&2
            break
        fi
        if ! raw_output_has_expected_count "${probe_raw_output_json}" 1; then
            echo "[probe][${MODEL_TAG}] stop_at=${count} reason=unexpected_output log=${probe_log_file}" >&2
            break
        fi
        max_success="${count}"
    done

    if [ "${max_success}" -le 0 ]; then
        echo "ERROR: failed to probe any supported image count for ${MODEL_LABEL}"
        exit 1
    fi

    set_cached_limit "${model_id}" "${max_success}" "${MODEL_LABEL}" "${MODEL_PATH}"
    echo "[probe][${MODEL_TAG}] max_supported_images=${max_success}" >&2
    printf '%s\n' "${max_success}"
}


run_task_for_model() {
    local task="$1"
    local model_id="$2"
    local max_supported_images="$3"

    resolve_model_config "${model_id}"

    local full_input_json=""
    local full_summary_json=""
    local question_type=""
    case "${task}" in
        q2)
            full_input_json="${Q2_INPUT_JSON}"
            full_summary_json="${Q2_INPUT_SUMMARY_JSON}"
            question_type="q2.1"
            ;;
        q6)
            full_input_json="${Q6_INPUT_JSON}"
            full_summary_json="${Q6_INPUT_SUMMARY_JSON}"
            question_type="q6"
            ;;
        *)
            echo "ERROR: unsupported task ${task}"
            exit 1
            ;;
    esac

    local filtered_root="${RESULT_ROOT}/filtered_inputs/${MODEL_TAG}"
    local filtered_input_json="${filtered_root}/${task}_up_to_${max_supported_images}f.json"
    local filtered_summary_json="${filtered_root}/${task}_up_to_${max_supported_images}f_summary.json"
    "${PYTHON_BIN}" "${FILTER_SCRIPT}" \
        --input_json "${full_input_json}" \
        --output_json "${filtered_input_json}" \
        --input_summary_json "${full_summary_json}" \
        --output_summary_json "${filtered_summary_json}" \
        --max_frame_count "${max_supported_images}"

    local model_result_root="${RESULT_ROOT}/${task}_${MODEL_TAG}"
    local raw_output_prefix="${model_result_root}/${task}_fixed_subset_front_history_1f_to_${max_supported_images}f"
    local raw_output_json="${raw_output_prefix}.json"
    local combined_output_json="${RESULT_ROOT}/${task}_${MODEL_TAG}_ordered_results_upto_${max_supported_images}f.json"
    local log_file="${model_result_root}/inference.log"

    mkdir -p "${model_result_root}"
    rm -f "${raw_output_json}" "${log_file}"
    rm -rf "${model_result_root}/individual_results"

    echo ""
    echo "------------------------------------------"
    echo "Running ${task} for ${MODEL_LABEL}"
    echo "model_id=${model_id}"
    echo "max_supported_images=${max_supported_images}"
    echo "input_json=${filtered_input_json}"
    echo "------------------------------------------"

    (
        cd "${MAIN_PROJECT_ROOT}"
        "${PYTHON_BIN}" "${INFER_SCRIPT}" \
            --model "${MODEL_PATH}" \
            --data "${filtered_input_json}" \
            --output "${raw_output_prefix}" \
            --system_prompt "${SYSTEM_PROMPT}" \
            --num_images_per_prompt "${max_supported_images}" \
            --max_model_len "${MODEL_MAX_MODEL_LEN}" \
            --num_processes "${NUM_PROCESSES}" \
            --batch_size "${BATCH_SIZE}" \
            --temperature "${TEMPERATURE}" \
            --top_p "${TOP_P}" \
            --max_tokens "${MAX_TOKENS}" \
            "${MODEL_EXTRA_ARGS[@]}" \
        2>&1 | tee "${log_file}"
    )

    "${PYTHON_BIN}" "${PACK_SCRIPT}" \
        --ordered_input_json "${filtered_input_json}" \
        --raw_output_json "${raw_output_json}" \
        --combined_output_json "${combined_output_json}" \
        --question_type "${question_type}" \
        --model_family "${model_id}" \
        --model_path "${MODEL_PATH}" \
        --input_summary_json "${filtered_summary_json}"
}


run_group() {
    ensure_prepared_inputs

    declare -A MODEL_LIMITS=()
    local model_id
    for model_id in "${MODEL_IDS[@]}"; do
        MODEL_LIMITS["${model_id}"]="$(probe_model_limit "${model_id}")"
        echo "Detected max_supported_images for ${model_id}: ${MODEL_LIMITS[${model_id}]}"
    done

    for model_id in "${MODEL_IDS[@]}"; do
        run_task_for_model q2 "${model_id}" "${MODEL_LIMITS[${model_id}]}"
    done

    for model_id in "${MODEL_IDS[@]}"; do
        run_task_for_model q6 "${model_id}" "${MODEL_LIMITS[${model_id}]}"
    done
}
