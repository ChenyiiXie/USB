#!/bin/bash

set -euo pipefail

MODEL_IDS=(qwen3)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "${SCRIPT_DIR}/../scripts/common_temporal_runner.sh"

echo "=========================================="
echo "Qwen3"
echo "Order: q2 then q6"
echo "=========================================="

run_group

echo "=========================================="
echo "Qwen3"
echo "=========================================="
