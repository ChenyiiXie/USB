# Unstructured Scene Benchmark (USB): Which VLM Performs Better in Autonomous Driving?

USB evaluates vision-language models on unstructured autonomous-driving scenes with six-view inputs, corrupted visual variants, Q1-Q6 driving QA prompts, and temporal front-view history tests.

## Environment

```bash
git clone <your-repo-url> USB
cd USB

conda create -n drivebench python=3.11 -y
conda activate drivebench
pip install -r requirements.txt
```

Recommended runtime: Linux, CUDA 12.4+, 32 GB RAM or more. Model weights are searched under `models` by default; update the paths in the run scripts if needed.

## Data Preprocessing

Run preprocessing in order:

```bash
# 1. Extract first-moment clean files by shard.
python preprocessing_scripts/preprocess_variants_by_shard_first_moment.py \
  --base_data_dir /path/to/raw_nuscenes_dataset \
  --output_dir nuscenes_first_moment_clean \
  --materialize_first_moment

# 2. Generate clean + corrupted first-moment variants.
python preprocessing_scripts/add_noise.py \
  --input_dir nuscenes_first_moment_clean \
  --output_dir nuscenes_dataset_first \
  --seed 42

# 3. Run the full preprocessing pipeline.
ORIGINAL_DATA_PATH="$(pwd)/nuscenes_dataset_first" \
bash preprocessing_scripts/run_data_preprocessing.sh
```

Generated files:

```text
nuscenes_variants_by_shard_impromptu_full/
nuscenes_switch/
comparison_results_final.xlsx
```

For temporal Q2/Q6 inputs:

```bash
cd temporal_test

BASE_CLEAN_DIR=/path/to/nuscenes_dataset/clean \
REBUILD_FROM_CLEAN=true \
CLEAN_OUTPUT=true \
bash run_temporal/run_prepare_fixed_subset_front_history_1to10.sh
```

Generated files:

```text
temporal_test/run_temporal/inputs/q2_fixed_subset_front_history_1f_to_10f_ordered.json
temporal_test/run_temporal/inputs/q6_fixed_subset_front_history_1f_to_10f_ordered.json
```

## Inference

Run corrupted-variant inference:

```bash
bash inference/run_impromptu/run_impromptu_variants_full_switch_qwen3vl.sh

```



Run temporal Q2/Q6 inference:

```bash
bash run_temporal/run_qwen3_q2_then_q6.sh
```

Outputs:

```text
result/
inference_log/
temporal_test/run_temporal/results/
temporal_test/run_temporal/probe/
```
