#!/usr/bin/env python3
"""
Синтаксическая проверка изменённых Swift-файлов (без Xcode/Swift-компилятора).

Файлы разбираются грамматикой Swift (tree-sitter), ищутся узлы ERROR/MISSING.
Метод сравнения: оригинальный и изменённый файл должны давать одинаковое число
ошибок разбора — значит правка не внесла синтаксических ошибок.

Установка зависимостей:
    pip install tree_sitter tree_sitter_swift

Запуск (внутри каталога fourfour-rebrand):
    python3 verify/check_swift_syntax.py baseline/original changed-files
"""
import sys
import os


def parse_stats(path, parser):
    with open(path, "rb") as f:
        data = f.read()
    tree = parser.parse(data)
    errors = []
    missing = []

    def walk(node):
        if node.type == "ERROR":
            errors.append(node)
        if node.is_missing:
            missing.append(node)
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return errors, missing


def find_files(root, extension):
    result = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(extension):
                result.append(os.path.join(dirpath, name))
    return sorted(result)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2

    import tree_sitter
    import tree_sitter_swift

    language = tree_sitter.Language(tree_sitter_swift.language())
    parser = tree_sitter.Parser(language)

    pristine_root = sys.argv[1]
    changed_root = sys.argv[2]

    changed_files = find_files(changed_root, ".swift")
    if not changed_files:
        print(f"Нет .swift файлов в {changed_root}")
        return 2

    failed = False
    for changed in changed_files:
        relative = os.path.relpath(changed, changed_root)
        pristine = os.path.join(pristine_root, relative)
        print(f"== {relative}")

        if not os.path.exists(pristine):
            print("   ! нет оригинала для сравнения — пропущено")
            continue

        base_errors, base_missing = parse_stats(pristine, parser)
        new_errors, new_missing = parse_stats(changed, parser)
        print(f"   оригинал:   ERROR={len(base_errors)}  MISSING={len(base_missing)}")
        print(f"   изменённый: ERROR={len(new_errors)}  MISSING={len(new_missing)}")

        if len(new_errors) != len(base_errors) or len(new_missing) != len(base_missing):
            failed = True
            for node in new_errors[:5]:
                print(f"   ! ERROR: {node.start_point} -> {node.end_point}")
            for node in new_missing[:5]:
                print(f"   ! MISSING: {node.type} @ {node.start_point}")
        else:
            print("   OK: новых синтаксических ошибок нет")

    print()
    if failed:
        print("РЕЗУЛЬТАТ: ЕСТЬ ПРОБЛЕМЫ (см. выше)")
        return 1
    print("РЕЗУЛЬТАТ: синтаксис изменённых файлов в порядке")
    return 0


if __name__ == "__main__":
    sys.exit(main())
