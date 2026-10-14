#!/usr/bin/env bash
# Применяет патч fourfour к чистому апстриму Swiftgram/Telegram-iOS.
#
# Использование:
#   ./verify/apply_patch.sh [каталог-назначения]
#
# По умолчанию исходники распаковываются в ./upstream/Telegram-iOS-master
# и туда применяется patches/0001-fourfour-rebrand.patch.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_ROOT="${1:-$ROOT/upstream}"
TARBALL_URL="https://codeload.github.com/Swiftgram/Telegram-iOS/tar.gz/refs/heads/master"
TARBALL_SHA256="cb17299b5c37329645c32720f58a6516e32e757b0aebefa934863a73f43cbed1"

mkdir -p "$TARGET_ROOT"
cd "$TARGET_ROOT"

if [ ! -d "Telegram-iOS-master" ]; then
    echo "==> Скачиваю апстрим Swiftgram/Telegram-iOS (master)"
    curl -L -o swiftgram.tar.gz "$TARBALL_URL"
    echo "==> Проверяю SHA-256 архива"
    echo "$TARBALL_SHA256  swiftgram.tar.gz" | shasum -a 256 -c -
    echo "==> Распаковываю"
    tar -xzf swiftgram.tar.gz
else
    echo "==> Каталог Telegram-iOS-master уже существует, распаковка пропущена"
fi

cd Telegram-iOS-master

echo "==> Проверяю, что патч применяется"
git apply --check "$ROOT/patches/0001-fourfour-rebrand.patch" 2>/dev/null \
  || patch --dry-run -p1 < "$ROOT/patches/0001-fourfour-rebrand.patch"

echo "==> Применяю патч"
git apply "$ROOT/patches/0001-fourfour-rebrand.patch" 2>/dev/null \
  || patch -p1 < "$ROOT/patches/0001-fourfour-rebrand.patch"

echo
echo "==> Готово. Изменённые файлы:"
echo "    Telegram/BUILD"
echo "    Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift"
echo
echo "==> Проверка значений:"
grep -n -A 1 "CFBundleDisplayName" Telegram/BUILD | grep -E "fourfour|CFBundleDisplayName" | head -10
grep -n "title: .text(\"fourfour\")" Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift
grep -n "UIColor(rgb: 0x000000)" Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift
