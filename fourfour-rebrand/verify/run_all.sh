#!/usr/bin/env bash
# Запускает все доступные проверки ребрендинга fourfour.
#
# Использование (внутри каталога fourfour-rebrand):
#   ./verify/run_all.sh /путь/к/чистому/апстриму/Telegram-iOS-master
#
# Первая проверка (синтаксис Swift) требует:
#   pip install tree_sitter tree_sitter_swift
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRISTINE="${1:-$ROOT/upstream/Telegram-iOS-master}"
PYTHON="${PYTHON:-python3}"
STATUS=0

if [ ! -d "$PRISTINE" ]; then
    echo "Не найден каталог с оригинальными исходниками: $PRISTINE"
    echo "Сначала выполните: ./verify/apply_patch.sh  (он скачает апстрим)"
    exit 2
fi

echo "############ 1/3 Синтаксис Swift (tree-sitter) ############"
if "$PYTHON" -c "import tree_sitter_swift" 2>/dev/null; then
    "$PYTHON" "$ROOT/verify/check_swift_syntax.py" "$ROOT/baseline/original" "$ROOT/changed-files" || STATUS=1
else
    echo "Пропущено: не установлен tree_sitter_swift (pip install tree_sitter tree_sitter_swift)"
fi

echo
echo "############ 2/3 Брендинг и используемые API ############"
"$PYTHON" "$ROOT/verify/check_branding.py" "$PRISTINE" || STATUS=1

echo
echo "############ 3/3 Патч применяется к чистому дереву ############"
# 3a. Патч должен применяться к оригинальным файлам (git apply --check, без изменений).
if ( cd "$PRISTINE" && git apply --check "$ROOT/patches/0001-fourfour-rebrand.patch" 2>/dev/null ); then
    echo "OK: git apply --check в чистом дереве апстрима"
else
    echo "ПРЕДУПРЕЖДЕНИЕ: git apply --check не выполнился (нет git-репозитория?) — проверяю через patch"
fi

# 3b. Применяем патч к копии ТОЛЬКО оригинальных файлов и сверяем результат с changed-files/.
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
mkdir -p "$TMP_DIR/Telegram" "$TMP_DIR/Swiftgram/SGSettingsUI/Sources"
cp "$ROOT/baseline/original/Telegram/BUILD" "$TMP_DIR/Telegram/BUILD"
cp "$ROOT/baseline/original/Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift" \
   "$TMP_DIR/Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift"
if ( cd "$TMP_DIR" && patch -s -p1 < "$ROOT/patches/0001-fourfour-rebrand.patch" ); then
    if diff -q "$TMP_DIR/Telegram/BUILD" "$ROOT/changed-files/Telegram/BUILD" >/dev/null \
       && diff -q "$TMP_DIR/Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift" \
                  "$ROOT/changed-files/Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift" >/dev/null; then
        echo "OK: оригинал + патч == changed-files/ (побайтово)"
    else
        echo "ОШИБКА: результат применения патча не совпал с changed-files/"
        STATUS=1
    fi
else
    echo "ОШИБКА: патч не применился к оригинальным файлам"
    STATUS=1
fi

echo
if [ "$STATUS" -eq 0 ]; then
    echo "РЕЗУЛЬТАТ: все доступные проверки пройдены"
else
    echo "РЕЗУЛЬТАТ: есть замечания (см. выше)"
fi
exit "$STATUS"
