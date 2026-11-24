set -euo pipefail
test "$(git rev-parse HEAD)" = bf48804c5ea558de62ad1eabd508a8ae18ae4203
test -z "$(git status --porcelain)"

export PYTHONPATH="$PWD/src"
export OLLAMA_CONTEXT_LENGTH=16384
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
export OLLAMA_NUM_PARALLEL=8

out=outputs/diag50-bf48804
mkdir "$out"

# Use a dedicated server with the specified environment.
if curl -fsS http://localhost:11434/api/version >/dev/null 2>&1; then
  echo "Port 11434 is already serving Ollama; stop that instance first." >&2
  exit 1
fi
ollama serve >"$out/ollama.log" 2>&1 &
echo "$!" >"$out/ollama.pid"

curl -fsS --retry 30 --retry-connrefused --retry-delay 1 \
  http://localhost:11434/api/version >"$out/version.json"
curl -fsS http://localhost:11434/api/show \
  -d '{"model":"qwen3-4b-t8:latest"}' >"$out/model.json"
nvidia-smi --query-gpu=name,memory.total,driver_version \
  --format=csv,noheader >"$out/gpu.txt"

python3 - "$out" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
assert json.loads((root / "version.json").read_text())["version"] == "0.40.17"
card = json.loads((root / "model.json").read_text())
weights = next(
    line.split()[1] for line in card["modelfile"].splitlines()
    if line.startswith("FROM ")
)
assert Path(weights).name == (
    "sha256-85e4a5b7b8ef0e48af0e8658f5aaab9c2324c76c1641493f4d1e25fce54b18b9"
)
assert card["details"]["quantization_level"] == "Q4_K_M"
assert card["template"]
parameters = dict(
    line.split(maxsplit=1)
    for line in card["parameters"].splitlines() if line.strip()
)
for key, value in {
    "num_thread": 8, "top_k": 20, "top_p": 0.8, "repeat_penalty": 1,
}.items():
    assert float(parameters[key]) == value, (key, parameters.get(key))
assert "RTX 3090" in (root / "gpu.txt").read_text()
print("Server configuration checks passed.")
PY

common=(
  E1
  --profiles dev_s0_01,dev_s1_01,dev_s2_01,dev_s3_01,dev_s4_01
  --repeats 2
  --model qwen3-4b-t8:latest
  --base-url http://localhost:11434/v1
  --temperature 0.3 --llm-seed 0 --context-length 16384
)

pids=()
i=0
for variants in A/N,A/F A/R1 A/R3 A/R3P; do
  python3 -m project_d.experiments.matrix "${common[@]}" \
    --variants "$variants" --output-dir "$out/g$i" \
    >"$out/g$i.console.log" 2>&1 &
  pids+=("$!")
  i=$((i + 1))
done

status=0
for pid in "${pids[@]}"; do
  wait "$pid" || status=1
done
curl -fsS http://localhost:11434/api/ps >"$out/loaded-models.json"
exit "$status"
