#!/usr/bin/env python3
"""
Проверка ребрендинга fourfour: что изменено ровно то, что нужно, и что
используемые API существуют в исходниках апстрима.

Запуск (внутри каталога fourfour-rebrand):
    python3 verify/check_branding.py <PRISTINE_ROOT>

<PRISTINE_ROOT> — каталог с оригинальным деревом Swiftgram/Telegram-iOS
(например, распакованный апстрим), из которого берутся подписи API из
submodules/TelegramPresentationData/Sources/PresentationTheme.swift
и submodules/ItemListUI/Sources/ItemListItem.swift.
"""
import difflib
import os
import re
import sys
import plistlib

CHANGED_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "changed-files")
BASELINE_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "baseline", "original")

results = []


def check(name, condition, details=""):
    results.append((name, bool(condition), details))
    status = "OK  " if condition else "FAIL"
    print(f"[{status}] {name}" + (f" — {details}" if details else ""))


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def changed_lines(baseline_path, changed_path):
    """Строки, отличающиеся от оригинала (в формате unified diff, только -/+)."""
    base = read(baseline_path).splitlines()
    new = read(changed_path).splitlines()
    diff = list(difflib.unified_diff(base, new, lineterm="", n=0))
    return [line for line in diff if (line.startswith("+") or line.startswith("-")) and
            not line.startswith("+++") and not line.startswith("---")]


def labels_of(signature):
    """Имена параметров с обеих сторон от ':' в списке аргументов."""
    return set(re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*:", signature))


def extract_signature(source, declaration):
    """Возвращает текст сигнатуры для 'func withUpdated(...)' и т.п."""
    index = source.find(declaration)
    if index == -1:
        return None
    end = source.find(")", source.find("(", index))
    depth = 0
    i = source.find("(", index)
    while i < len(source):
        if source[i] == "(":
            depth += 1
        elif source[i] == ")":
            depth -= 1
            if depth == 0:
                return source[index:i + 1]
        i += 1
    return None


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    pristine = os.path.abspath(sys.argv[1])

    build_base = os.path.join(BASELINE_ROOT, "Telegram", "BUILD")
    build_new = os.path.join(CHANGED_ROOT, "Telegram", "BUILD")
    swift_base = os.path.join(BASELINE_ROOT, "Swiftgram", "SGSettingsUI", "Sources", "SGSettingsController.swift")
    swift_new = os.path.join(CHANGED_ROOT, "Swiftgram", "SGSettingsUI", "Sources", "SGSettingsController.swift")

    build_text = read(build_new)
    swift_text = read(swift_new)

    print("=== 1. Отображаемое имя приложения (Telegram/BUILD) ===")
    app_name_fragment = build_text[build_text.find('name = "AppNameInfoPlist"'):]
    app_name_fragment = app_name_fragment[:app_name_fragment.find(")")]
    check("AppNameInfoPlist: CFBundleDisplayName = fourfour",
          "<key>CFBundleDisplayName</key>\n    <string>fourfour</string>" in app_name_fragment)

    tg_fragment = build_text[build_text.find('name = "TelegramInfoPlist"'):]
    tg_fragment = tg_fragment[:tg_fragment.find("\nbroadcast_upload_extension(") if "\nbroadcast" in tg_fragment else len(tg_fragment)]
    check("TelegramInfoPlist: CFBundleDisplayName = fourfour",
          re.search(r"<key>CFBundleDisplayName</key>\s*<string>fourfour</string>", tg_fragment) is not None)
    check("TelegramInfoPlist: CFBundleName = fourfour",
          re.search(r"<key>CFBundleName</key>\s*<string>fourfour</string>", tg_fragment) is not None)

    print()
    print("=== 2. Изменения в Telegram/BUILD строго ограничены ===")
    build_changes = changed_lines(build_base, build_new)
    value_lines = [line for line in build_changes
                   if line.strip("+-").strip() in ("<string>Swiftgram</string>", "<string>fourfour</string>")]
    check("в BUILD изменены только значения CFBundleDisplayName/CFBundleName (3 строки)",
          len(build_changes) == 6 and len(value_lines) == 6,
          f"изменённых строк: {len(build_changes)} (ожидалось 6 = 3 удалённых + 3 добавленных)")
    check("не тронуты внутренние идентификаторы (имя bazel-таргета, проект Xcode)",
          'ios_application(\n    name = "Swiftgram"' in build_text and 'project_name = "Swiftgram"' in build_text)

    print()
    print("=== 3. Экран настроек fourfour (SGSettingsController.swift) ===")
    check("заголовок верхней плашки = fourfour",
          'title: .text("fourfour")' in swift_text)
    check("фон верхней плашки = #000000",
          re.search(r"UIColor\(rgb: 0x000000\)", swift_text) is not None)
    check("чёрная тема применяется только к экрану настроек fourfour",
          "sgFourFourSettingsPresentationData(presentationData)" in swift_text)

    swift_changes = changed_lines(swift_base, swift_new)
    removed = [line for line in swift_changes if line.startswith("-")]
    check("из исходного файла удалена только одна строка (заголовок Swiftgram)",
          len(removed) == 1 and 'title: .text("Swiftgram")' in removed[0],
          f"удалено строк: {len(removed)}")
    check("остальные строки только добавлены (интерфейс не переписывался)",
          all(line.startswith("+") for line in swift_changes if line not in removed))

    print()
    print("=== 4. Используемые API существуют в апстриме ===")
    theme_source = read(os.path.join(pristine, "submodules", "TelegramPresentationData",
                                     "Sources", "PresentationTheme.swift"))
    item_list_source = read(os.path.join(pristine, "submodules", "ItemListUI",
                                         "Sources", "ItemListItem.swift"))
    presentation_data_source = read(os.path.join(pristine, "submodules", "TelegramPresentationData",
                                                 "Sources", "PresentationData.swift"))

    nav_bar_sig = extract_signature(theme_source,
                                    "public func withUpdated(buttonColor: UIColor? = nil, micLevelColor")
    nav_bar_sig = extract_signature(theme_source,
                                    "public func withUpdated(buttonColor: UIColor? = nil, disabledButtonColor")
    nav_bar_labels = labels_of(nav_bar_sig) if nav_bar_sig else set()
    for label in ["buttonColor", "primaryTextColor", "secondaryTextColor",
                  "blurredBackgroundColor", "opaqueBackgroundColor", "separatorColor"]:
        check(f"PresentationThemeRootNavigationBar.withUpdated({label}:)", label in nav_bar_labels)

    panel_sig = extract_signature(theme_source, "public func withUpdated(panelBackgroundColor: UIColor? = nil")
    panel_labels = labels_of(panel_sig) if panel_sig else set()
    for label in ["panelControlColor", "panelControlDisabledColor", "panelControlAccentColor"]:
        check(f"PresentationThemeChatInputPanel.withUpdated({label}:)", label in panel_labels)

    root_sig = extract_signature(theme_source, "public func withUpdated(statusBarStyle: PresentationThemeStatusBarStyle? = nil, tabBar")
    root_labels = labels_of(root_sig) if root_sig else set()
    for label in ["statusBarStyle", "navigationBar"]:
        check(f"PresentationThemeRootController.withUpdated({label}:)", label in root_labels)

    chat_sig = extract_signature(theme_source, "public func withUpdated(defaultWallpaper: TelegramWallpaper? = nil, animateMessageColors")
    check("PresentationThemeChat.withUpdated(inputPanel:)", "inputPanel" in (labels_of(chat_sig) if chat_sig else set()))

    theme_init_sig = extract_signature(theme_source, "public init(name: PresentationThemeName, index: Int64")
    theme_init_labels = labels_of(theme_init_sig) if theme_init_sig else set()
    for label in ["name", "index", "referenceTheme", "overallDarkAppearance", "intro", "passcode",
                  "rootController", "list", "chatList", "chat", "actionSheet", "contextMenu",
                  "inAppNotification", "chart", "preview"]:
        check(f"PresentationTheme.init({label}:)", label in theme_init_labels)

    print()
    print("=== 4b. Порядок именованных аргументов (Swift требует порядок объявления) ===")

    branding_start = swift_text.find("// MARK: fourfour branding")
    branding_end = swift_text.find("private func SGControllerEntries")
    branding_block = swift_text[branding_start:branding_end]

    def top_level_labels(source, call_marker):
        """Метки верхнеуровневых аргументов вызова, начинающегося с call_marker."""
        index = source.find(call_marker)
        if index == -1:
            return None
        open_index = source.find("(", index + len(call_marker) - 1)
        depth = 0
        parts = []
        current = ""
        for i in range(open_index, len(source)):
            char = source[i]
            if char in "([{":
                depth += 1
                if depth == 1:
                    continue  # сам открывающий символ вызова не добавляем в аргумент
            elif char in ")]}":
                depth -= 1
                if depth == 0:
                    parts.append(current)
                    break
            if depth == 1 and char == ",":
                parts.append(current)
                current = ""
            else:
                current += char
        labels = []
        for part in parts:
            match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", part)
            if match:
                labels.append(match.group(1))
        return labels

    def is_subsequence(call_labels, declaration_labels):
        it = iter(declaration_labels)
        return all(label in it for label in call_labels)

    call_sites = [
        ("navigationBar.withUpdated", "theme.rootController.navigationBar.withUpdated(",
         "public func withUpdated(buttonColor: UIColor? = nil, disabledButtonColor"),
        ("inputPanel.withUpdated", "theme.chat.inputPanel.withUpdated(",
         "public func withUpdated(panelBackgroundColor: UIColor? = nil"),
        ("rootController.withUpdated", "theme.rootController.withUpdated(",
         "public func withUpdated(statusBarStyle: PresentationThemeStatusBarStyle? = nil, tabBar"),
        ("chat.withUpdated", "theme.chat.withUpdated(",
         "public func withUpdated(defaultWallpaper: TelegramWallpaper? = nil, animateMessageColors"),
        ("PresentationTheme.init", "let brandedTheme = PresentationTheme(",
         "public init(name: PresentationThemeName, index: Int64"),
    ]
    for label, call_marker, declaration_marker in call_sites:
        call_labels = top_level_labels(branding_block, call_marker)
        declaration_labels = labels_of(extract_signature(theme_source, declaration_marker) or "")
        declaration_order = [item for item in re.findall(
            r"([A-Za-z_][A-Za-z0-9_]*)\s*:", extract_signature(theme_source, declaration_marker) or "")]
        check(f"{label}: аргументы переданы в порядке объявления",
              call_labels is not None and is_subsequence(call_labels, declaration_order),
              f"вызов: {call_labels}")

    check("PresentationData.withUpdated(theme:)",
          "public func withUpdated(theme: PresentationTheme) -> PresentationData" in presentation_data_source)
    check("ItemListPresentationData(_ presentationData: PresentationData)",
          "convenience init(_ presentationData: PresentationData)" in item_list_source)
    check("PresentationThemeStatusBarStyle.white (белый текст в статус-баре)",
          "case white = 1" in theme_source and "return .White" in theme_source)

    print()
    print("=== 5. Валидность plist-фрагментов (XML) ===")
    for fragment_name, marker in [("AppNameInfoPlist", 'name = "AppNameInfoPlist"'),
                                  ("TelegramInfoPlist", 'name = "TelegramInfoPlist"')]:
        start = build_text.find(marker)
        fragment = build_text[start:]
        fragment = fragment[fragment.find('"""') + 3:]
        fragment = fragment[:fragment.find('"""')]
        # подстановки bazel/апстрима заменяем на безопасные значения
        fragment = fragment.replace("{telegram_bundle_id}", "com.example.app")
        fragment = re.sub(r"<string>[^<]*\$\{[^}]*\}[^<]*</string>", "<string>placeholder</string>", fragment)
        fragment = fragment.replace("&", "&amp;")
        xml = f'<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict>{fragment}</dict></plist>'
        try:
            parsed = plistlib.loads(xml.encode("utf-8"))
            ok = isinstance(parsed, dict)
        except Exception as error:  # noqa: BLE001
            parsed, ok = {}, False
            print("        ошибка разбора:", error)
        if ok:
            name = "fourfour"
            check(f"{fragment_name}: XML валиден", True)
            if fragment_name == "AppNameInfoPlist":
                check("  → CFBundleDisplayName", parsed.get("CFBundleDisplayName") == name,
                      f"значение: {parsed.get('CFBundleDisplayName')!r}")
            if fragment_name == "TelegramInfoPlist":
                check("  → CFBundleDisplayName", parsed.get("CFBundleDisplayName") == name,
                      f"значение: {parsed.get('CFBundleDisplayName')!r}")
                check("  → CFBundleName", parsed.get("CFBundleName") == name,
                      f"значение: {parsed.get('CFBundleName')!r}")
        else:
            check(f"{fragment_name}: XML валиден", False)

    print()
    print("=== 6. Что осталось содержать «Swiftgram» (осознанно не менялось) ===")
    remaining = []
    for i, line in enumerate(build_text.splitlines(), start=1):
        if "Swiftgram" in line:
            remaining.append((i, line.strip()))
    print(f"  Всего упоминаний «Swiftgram» в Telegram/BUILD: {len(remaining)}")
    for line_number, line in remaining:
        print(f"    строка {line_number}: {line}")

    print()
    failed = [name for name, ok, _ in results if not ok]
    if failed:
        print(f"РЕЗУЛЬТАТ: ПРОВАЛЕНО {len(failed)} проверок:")
        for name in failed:
            print("  -", name)
        return 1
    print(f"РЕЗУЛЬТАТ: все {len(results)} проверок пройдены")
    return 0


if __name__ == "__main__":
    sys.exit(main())
