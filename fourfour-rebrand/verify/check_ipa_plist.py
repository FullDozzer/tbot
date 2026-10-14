#!/usr/bin/env python3
"""Читает Info.plist из распакованного .ipa (или .app) и показывает имя приложения.

Использование:
    python3 check_ipa_plist.py <каталог с распакованным .ipa или .app>
    python3 check_ipa_plist.py --expected fourfour <каталог>

Печатает ключи Info.plist в виде аннотаций GitHub Actions (::notice::), если задана
переменная окружения GITHUB_ACTIONS, и завершается с кодом 1, если CFBundleDisplayName
не совпадает с ожидаемым (по умолчанию fourfour).
"""

import argparse
import glob
import os
import plistlib
import sys

KEYS = [
    "CFBundleDisplayName",
    "CFBundleName",
    "CFBundleIdentifier",
    "CFBundleShortVersionString",
    "CFBundleVersion",
]


def find_info_plist(root):
    """Ищет Info.plist: сначала Payload/*.app (внутри .ipa), потом *.app."""
    candidates = []
    candidates += glob.glob(os.path.join(root, "Payload", "*.app", "Info.plist"))
    candidates += glob.glob(os.path.join(root, "Payload", "*", "*.app", "Info.plist"))
    candidates += sorted(glob.glob(os.path.join(root, "**", "*.app", "Info.plist"), recursive=True))
    if os.path.isfile(root) and root.endswith(".plist"):
        candidates.append(root)
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def emit_annotation(title, value):
    """Публикует значение как аннотацию GitHub Actions (если мы внутри Actions)."""
    escaped = str(value).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print("::notice title={}::{}".format(title, escaped))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="каталог с распакованным .ipa / .app (или сам Info.plist)")
    parser.add_argument("--expected", default="fourfour",
                        help="ожидаемое значение CFBundleDisplayName (по умолчанию fourfour)")
    parser.add_argument("--no-strict", action="store_true",
                        help="не падать при несовпадении (только показать значения)")
    arguments = parser.parse_args()

    info_plist = find_info_plist(arguments.path)
    if info_plist is None:
        print("Не найден Info.plist в {}".format(arguments.path), file=sys.stderr)
        return 1

    with open(info_plist, "rb") as file:
        data = plistlib.load(file)

    print("Info.plist: {}".format(info_plist))
    values = {}
    for key in KEYS:
        values[key] = str(data.get(key, ""))
        print("  {} = {}".format(key, values[key]))
        if os.environ.get("GITHUB_ACTIONS") == "true":
            emit_annotation(key, values[key])

    display_name = values["CFBundleDisplayName"] or values["CFBundleName"]
    if display_name != arguments.expected and not arguments.no_strict:
        message = "CFBundleDisplayName = {!r}, ожидалось {!r}".format(display_name, arguments.expected)
        if os.environ.get("GITHUB_ACTIONS") == "true":
            print("::error title=Имя приложения::{}".format(message))
        print("ОШИБКА: " + message, file=sys.stderr)
        return 1

    print("OK: имя приложения в сборке — {}".format(display_name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
