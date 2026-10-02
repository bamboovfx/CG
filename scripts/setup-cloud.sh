#!/usr/bin/env bash
# 安装与本机一致的官方 Blender 后台版本，校验下载完整性并验收。
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .local/tools
archive=blender-5.1.2-linux-x64.tar.xz
binary=.local/tools/blender-5.1.2-linux-x64/blender
if [[ ! -x "$binary" ]]; then
  curl --fail --location --retry 3 "https://download.blender.org/release/Blender5.1/$archive" -o ".local/tools/$archive"
  printf '%s  %s\n' aaccb355f50183979b698bcce7467103a76261b5fa59f4972295842662a285fb ".local/tools/$archive" | sha256sum --check
  tar -xJf ".local/tools/$archive" -C .local/tools
fi
python3 scripts/check_workspace.py --blender "$binary"
