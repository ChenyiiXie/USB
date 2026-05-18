#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"
MODEL_BASE_PATH="${MODEL_BASE_PATH:-${PROJECT_ROOT}/models}"
QWEN3_MODEL_PATH="${QWEN3_MODEL_PATH:-${MODEL_BASE_PATH}/Qwen/Qwen3-VL-8B-Instruct}"


# Impromptu - Processingnuscenes_switch（）
# Qwen3-VL-8B-Instruct，Processing8 data variants

# ==========================================
# 🔧  - 
# ==========================================

# 
# true: ，Skipcompleted variants
# false: ，rerunvariant
ENABLE_RESUME=true

# 
# true: Validate data completeness，Processing
# false: result
ENABLE_DATA_VALIDATION=true

# Clean temporary files
# true: ProcessingDoneClean temporary files
# false: Kept temporary file
AUTO_CLEANUP=true

# 
# true: Processing
# false: 
VERBOSE_LOGGING=true

# # Qwen3-VL-8B-Instruct model path
# #  QWEN3_VL_MODEL_PATH ，
# MODEL_BASE_PATH="${MODEL_BASE_PATH:-${PROJECT_ROOT}/models}"
# QWEN3_VL_MODEL_PATH="${QWEN3_VL_MODEL_PATH:-$MODEL_BASE_PATH/Qwen/Qwen3-VL-8B-Instruct}"

# if [ ! -d "$QWEN3_VL_MODEL_PATH" ]; then
#     echo "❌ Found Qwen3-VL-8B-Instruct : $QWEN3_VL_MODEL_PATH"
#     echo " QWEN3_VL_MODEL_PATH model path"
#     exit 1
# fi

# ==========================================
# 🚀 
# ==========================================

echo "=========================================="
echo "🚀 Impromptuvariant（Qwen3-VL-8B-Instruct）"
echo "=========================================="

# 
validate_config() {
    local errors=0
    
    # 
    for config in "ENABLE_RESUME" "ENABLE_DATA_VALIDATION" "AUTO_CLEANUP" "VERBOSE_LOGGING"; do
        local value=$(eval echo \$$config)
        if [ "$value" != "true" ] && [ "$value" != "false" ]; then
            echo "❌ : $config  'true'  'false'，: $value"
            errors=$((errors + 1))
        fi
    done
    
    if [ $errors -gt 0 ]; then
        echo ""
        exit 1
    fi
}

# 
validate_config

# 
echo "📋 :"
echo "  - : $([ "$ENABLE_RESUME" = "true" ] && echo "✅ " || echo "❌ ")"
echo "  - : $([ "$ENABLE_DATA_VALIDATION" = "true" ] && echo "✅ " || echo "❌ ")"
echo "  - : $([ "$AUTO_CLEANUP" = "true" ] && echo "✅ " || echo "❌ ")"
echo "  - : $([ "$VERBOSE_LOGGING" = "true" ] && echo "✅ " || echo "❌ ")"
echo ""
# GPU（，0GPU）
GPU_INDEX=0
export CUDA_VISIBLE_DEVICES="$GPU_INDEX"

RESULTS_DIR="result/Impromptu_variants_results_qwen3vl"
mkdir -p result
mkdir -p "$RESULTS_DIR"
mkdir -p Impromptu_variants_individual_files
mkdir -p inference_log

# Progress
PROGRESS_FILE="inference_log/impromptu_progress_qwen3vl.txt"
COMPLETED_VARIANTS_FILE="inference_log/completed_variants_qwen3vl.txt"

# 
print_usage() {
    cat <<EOF
Usage:
  $0                    # run from scratch
  $0 --resume           # resume from the last interruption
  $0 --resume <variant> # resume from a specific variant

Options:
  --help, -h            # show this help message
  --resume [variant]    # enable resume, optionally from a variant

Progress files:
  - $PROGRESS_FILE
  - $COMPLETED_VARIANTS_FILE
EOF
}

RESUME_FROM=""
RESUME_MODE=false

if [ "$#" -gt 0 ]; then
    case "$1" in
        --help|-h)
            print_usage
            exit 0
            ;;
        --resume)
            RESUME_MODE=true
            if [ "$#" -gt 1 ] && [ -n "$2" ]; then
                RESUME_FROM="$2"
            fi
            ;;
        "")
            ;;
        *)
            echo "❌ Unknown argument: $1"
            print_usage
            exit 1
            ;;
    esac
fi

echo "🎯 Using GPU index: $CUDA_VISIBLE_DEVICES"

if [ "$RESUME_MODE" = "true" ]; then
    if [ -n "$RESUME_FROM" ]; then
        echo "🔄 mode：variant '$RESUME_FROM' "
    else
        echo "🔄 mode：resume from the last interruption"
    fi
fi

# Record start time
start_time=$(date)
echo "⏰ Start time: $start_time"

# Define data variants as a space-separated list
variants="backlight bit_error bright clean compress crash dark fog frame_lost glare lens lightning motion_blur quant rain sandstorm saturate smoke snow splash zoom_blur"

# Define train and validation shards
train_shards="0000 0001 0002 0003 0004 0005 0006 0007 0008 0009 0010 0011 0012 0013 0014 0015 0016 0017 0018 0019 0020 0021 0022"
val_shards="0000 0001 0002 0003 0004 0005"

# Count variants
variant_count=$(echo $variants | wc -w)
train_count=$(echo $train_shards | wc -w)
val_count=$(echo $val_shards | wc -w)

echo "📊 Found $variant_count  data variants"
echo "📊 Each variant contains $train_count train shards and $val_count validation shards"

# Check completed variant
check_variant_completed() {
    local variant=$1
    local result_file="$RESULTS_DIR/${variant}/${variant}_results.json"
    local merged_file="temp_${variant}_merged.json"
    
    # Return incomplete when resume is disabled
    if [ "$ENABLE_RESUME" != "true" ]; then
        if [ "$VERBOSE_LOGGING" = "true" ]; then
            echo "🔄 Resume disabled; rerun $variant"
        fi
        return 1
    fi
    
    # Check result file exists and is non-empty
    if [ -f "$result_file" ] && [ -s "$result_file" ]; then
        # Validate JSON file
        if python -c "import json; json.load(open('$result_file'))" 2>/dev/null; then
            # If data validation is disabled, only check result existence
            if [ "$ENABLE_DATA_VALIDATION" != "true" ]; then
                if [ "$VERBOSE_LOGGING" = "true" ]; then
                    echo "✅ $variant completed, skipping data validation"
                fi
                return 0  # Done
            fi
            
            # Validate completeness by comparing result and merged counts
            if [ -f "$merged_file" ]; then
                local result_count=$(python -c "import json; data=json.load(open('$result_file')); print(len(data))" 2>/dev/null)
                local merged_count=$(python -c "import json; data=json.load(open('$merged_file')); print(len(data))" 2>/dev/null)
                
                if [ "$result_count" = "$merged_count" ] && [ "$result_count" -gt 0 ]; then
                    if [ "$VERBOSE_LOGGING" = "true" ]; then
                        echo "✅ $variant completed: processed $result_count/$merged_count question"
                    fi
                    return 0  # Done
                else
                    if [ "$VERBOSE_LOGGING" = "true" ]; then
                        echo "⚠️  $variant incomplete: processed only $result_count/$merged_count question"
                    fi
                    return 1  # Done
                fi
            else
                if [ "$VERBOSE_LOGGING" = "true" ]; then
                    echo "⚠️  Unable to validate $variant completion status：merged file not found"
                fi
                return 1  # Done
            fi
        else
            if [ "$VERBOSE_LOGGING" = "true" ]; then
                echo "⚠️  Foundresult: $result_file"
            fi
            return 1  # Done
        fi
    else
        return 1  # Done
    fi
}

# Log progress
log_progress() {
    local variant=$1
    local status=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $variant: $status" >> "$PROGRESS_FILE"
}

# Record completed variant
mark_variant_completed() {
    local variant=$1
    if ! grep -q "^$variant$" "$COMPLETED_VARIANTS_FILE" 2>/dev/null; then
        echo "$variant" >> "$COMPLETED_VARIANTS_FILE"
    fi
}

# Check resume state
if [ -f "$COMPLETED_VARIANTS_FILE" ]; then
    completed_count=$(wc -l < "$COMPLETED_VARIANTS_FILE")
    echo "📋 Found $completed_count completed variants"
    
    if [ "$completed_count" -gt 0 ]; then
        echo "✅ completed variants:"
        while read -r variant; do
            if [ -n "$variant" ]; then
                echo "  - $variant"
            fi
        done < "$COMPLETED_VARIANTS_FILE"
    fi
else
    echo "📋 FoundDonevariant，"
    completed_count=0
fi

# Process each  data variants
for variant in $variants; do
    echo ""
    echo "=========================================="
    echo "🔄 Processing variant: $variant"
    echo "=========================================="
    
    # Check whether this variant should be skipped
    skip_variant=false
    
    # variants，to
    if [ -n "$RESUME_FROM" ]; then
        if [ "$variant" != "$RESUME_FROM" ]; then
            echo "⏭️  Skip variant $variant（to $RESUME_FROM）"
            continue
        else
            echo "🎯 tovariant $RESUME_FROM，start processing"
            RESUME_FROM=""  # clear flag so subsequent variants run normally
        fi
    fi
    
    # Check whether variant is completed
    if check_variant_completed "$variant"; then
        echo "✅ variant $variant completed, skip"
        log_progress "$variant" "skipped, already completed"
        continue
    fi
    
    # start processing
    log_progress "$variant" "start processing"
    
    # variantoutput directory
    mkdir -p "$RESULTS_DIR/$variant"
    mkdir -p "Impromptu_variants_individual_files/$variant"
    
    # variantJSONto
    echo "📁 Copying $variant JSONto..."
    cp "nuscenes_switch/$variant"/*.json "Impromptu_variants_individual_files/$variant/"
    echo "✅ $variant 29JSON filesto Impromptu_variants_individual_files/$variant/"
    
    # variantJSON
    echo "📊 Merging $variant JSON..."
    
    # Create temporary merged file
    temp_merged_file="temp_${variant}_merged.json"
    
    python -c "
import json
import os
import glob

variant = '$variant'
temp_file = '$temp_merged_file'

# Get all JSON file paths
data_dir = f'nuscenes_switch/{variant}'
json_files = glob.glob(f'{data_dir}/*.json')

print(f'Found {len(json_files)} JSON files')

# Merge all JSON files
all_data = []
for json_file in sorted(json_files):
    print(f'Processing: {json_file}')
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        all_data.extend(data)

print(f'Total merged sample count: {len(all_data)}')

# Save merged data
with open(temp_file, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print(f'to: {temp_file}')
"
    
    # Check merge success
    if [ $? -eq 0 ]; then
        echo "✅ $variant data merge completed！"
        
        # Run inference script
        echo "📊 start processing $variant sample..."
        python inference/qwen3_vl_impromptu.py \
            --model "${QWEN3_MODEL_PATH}" \
            --data "temp_${variant}_merged.json" \
            --output "$RESULTS_DIR/${variant}/${variant}_results" \
            --system_prompt "${PROJECT_ROOT}/inference/prompt.txt" \
            --num_images_per_prompt 6 \
            --max_model_len 4096 \
            --num_processes 1 \
            --batch_size 1 \
            --temperature 0.7 \
            --top_p 0.8 \
            --max_tokens 512 \
            2>&1 | tee "inference_log/${variant}_inference_qwen3vl.log"
        
        # Runresult
        if [ $? -eq 0 ]; then
            echo "✅ $variant Runsuccess！"
            
            # Validate data completeness
            if [ -f "$RESULTS_DIR/${variant}/${variant}_results.json" ]; then
                result_count=$(python -c "import json; data=json.load(open('$RESULTS_DIR/${variant}/${variant}_results.json')); print(len(data))" 2>/dev/null)
                merged_count=$(python -c "import json; data=json.load(open('temp_${variant}_merged.json')); print(len(data))" 2>/dev/null)
                
                echo "📊 $variant Processing progress: $result_count/$merged_count question"
                
                # Mark complete only when counts fully match
                if [ "$result_count" = "$merged_count" ] && [ "$result_count" -gt 0 ]; then
                    echo "✅ $variant inference completed successfully！all data processed"
                    log_progress "$variant" "inference completed successfully"
                    mark_variant_completed "$variant"
                else
                    echo "⚠️  $variant inference incomplete; rerun required"
                    log_progress "$variant" "Done"
                fi
            else
                echo "❌ $variant result file not generated"
                log_progress "$variant" "result file not generated"
            fi
            
            # Show result file information
            echo "📁 $variant result file path:"
            ls -la "$RESULTS_DIR/${variant}/${variant}_results"* 2>/dev/null || echo "  no result files"
            
            # Clean temporary files
            if [ "$AUTO_CLEANUP" = "true" ]; then
                rm -f "temp_${variant}_merged.json"
                if [ "$VERBOSE_LOGGING" = "true" ]; then
                    echo "🧹 Clean temporary files: temp_${variant}_merged.json"
                fi
            else
                if [ "$VERBOSE_LOGGING" = "true" ]; then
                    echo "📁 Kept temporary file: temp_${variant}_merged.json"
                fi
            fi
            
        else
            echo "❌ $variant inference failed！"
            log_progress "$variant" "inference failed"
            echo "Check the error message and retry"
            # Clean temporary files
            if [ "$AUTO_CLEANUP" = "true" ]; then
                rm -f "temp_${variant}_merged.json"
                if [ "$VERBOSE_LOGGING" = "true" ]; then
                    echo "🧹 Clean temporary files: temp_${variant}_merged.json"
                fi
            else
                if [ "$VERBOSE_LOGGING" = "true" ]; then
                    echo "📁 Kept temporary file: temp_${variant}_merged.json"
                fi
            fi
            continue
        fi
    else
        echo "❌ $variant data merge failed！"
        log_progress "$variant" "data merge failed"
        echo "Check whether data files exist"
        continue
    fi
    
    # Error handling during processing
    if [ $? -ne 0 ]; then
        echo "❌ $variant error during processing！"
        log_progress "$variant" "error during processing"
        continue
    fi
done

# Record end time
end_time=$(date)
echo ""
echo "=========================================="
echo "⏰ End time: $end_time"
echo "=========================================="

# Show resume statistics
echo ""
echo "📊 Resume statistics:"
if [ -f "$COMPLETED_VARIANTS_FILE" ]; then
    total_completed=$(wc -l < "$COMPLETED_VARIANTS_FILE")
    echo "✅ Completed in this run: $total_completed variants"
    
    # Completed in this runvariants
    if [ "$total_completed" -gt 0 ]; then
        echo "📋 Variants completed in this run:"
        while read -r variant; do
            if [ -n "$variant" ]; then
                echo "  - $variant"
            fi
        done < "$COMPLETED_VARIANTS_FILE"
    fi
else
    echo "❌ FoundDone"
fi

# Show progress log
if [ -f "$PROGRESS_FILE" ]; then
    echo ""
    echo "📝 Progress log, last 10 lines:"
    tail -10 "$PROGRESS_FILE"
fi

# Show all result file locations
echo "📁 result file path:"
find "$RESULTS_DIR" -name "*.json" -type f | sort

echo ""
echo "📁 All individual JSON file locations:"
find Impromptu_variants_individual_files -name "*.json" -type f | sort

# Summarize overall results
echo ""
echo "📊 Overall result summary:"
for variant in $variants; do
    result_file="$RESULTS_DIR/${variant}/${variant}_results.json"
    individual_dir="Impromptu_variants_individual_files/${variant}"
    
    if [ -f "$result_file" ]; then
        result_count=$(python -c "import json; data=json.load(open('$result_file')); print(f'{variant}: {len(data)} question')")
        echo "  $result_count"
    else
        echo "  $variant: inference processing failed"
    fi
    
    # Count individual files
    if [ -d "$individual_dir" ]; then
        file_count=$(find "$individual_dir" -name "*.json" -type f | wc -l)
        echo "    └─ individual JSON files: $file_count "
    else
        echo "    └─ individual JSON files: copy failed"
    fi
done

echo ""
echo "=========================================="
echo "🎉 variantDone！"
echo "=========================================="
