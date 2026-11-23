#!/usr/bin/env bash
# 저장소 전체를 bundle 파일 하나로 백업한다(macOS·리눅스).
# 사용: 저장소 폴더에서 ./scripts/backup_bundle.sh [백업폴더]
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "$root"

dest="${1:-$HOME/Backups/muwon406}"
mkdir -p "$dest"
file="$dest/muwon406-$(date +%Y%m%d-%H%M).bundle"

git bundle create "$file" --all
git bundle verify "$file"
echo "백업 완료: $file"
