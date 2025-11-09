#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[deploy] begin at $(date -Is)"
echo "[deploy] ROOT=$ROOT"

# 檢查 venv
if [ ! -x ./.venv/bin/python ]; then
  echo "[deploy][WARN] .venv not found, will try to create ..."
  python3 -m venv .venv
  ./.venv/bin/pip install -r requirements.txt || true
fi

# systemd (user)
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/ai-invest-lab.service <<'UNIT'
[Unit]
Description=AI-Invest-Lab Daily Pipeline (oneshot)
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=%h/ai-invest-lab
Environment=PYTHONPATH=.
EnvironmentFile=%h/ai-invest-lab/.env
ExecStart=%h/ai-invest-lab/scripts/run_daily_pipeline.sh
TimeoutStartSec=1800
Nice=10
IOSchedulingClass=best-effort

[Install]
WantedBy=default.target
UNIT

systemctl --user daemon-reload
systemctl --user enable ai-invest-lab.service || true

# cron
cat > /tmp/aiinvest.cron <<'CRON'
CRON_TZ=America/New_York
5 17 * * 1-5 systemctl --user start ai-invest-lab.service
CRON
( crontab -l 2>/dev/null; cat /tmp/aiinvest.cron ) | crontab -
rm /tmp/aiinvest.cron

echo "[deploy] done."
