#!/usr/bin/env bash
# 一键复现：生成 → 静态检查 → 离线模拟（连跑两轮）→ 预览 → BDX 回读
set -euo pipefail
cd "$(dirname "$0")"

LINT="../../scripts/chain_lint.py"
if [ ! -f "$LINT" ]; then
  LINT="../../.dsh/skills/mcbe-command-blocks/scripts/chain_lint.py"
fi

python3 gen.py
python3 "$LINT" spec.json --format markdown --write plan.md
python3 sim.py 400
MPLCONFIGDIR=/tmp/mpl-dsh python3 preview.py
python3 readbdx.py
echo "OK: terrain.bdx / plan.md / preview.png"
