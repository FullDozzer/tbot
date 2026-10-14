# Сборка fourfour (нужен macOS)

## Почему сборка не выполнена в этой среде

Проект Swiftgram/Telegram-iOS собирается только на macOS:

* сборка идёт через Bazel (`build-system/Make/Make.py`), который для iOS-таргетов требует Xcode и Apple-тулчейн;
* компилятор Swift, `xcodebuild`, `codesign`, `xcrun`, `simctl` доступны только в macOS.

В среде, где готовился этот патч (Linux, без Xcode/Swift-тулчейна), физически невозможно
собрать `.app`/`.ipa`. Вместо сборки выполнены статические проверки — см.
[VERIFICATION-LOG.txt](VERIFICATION-LOG.txt) и §7 в [../README.md](../README.md).

## Шаги сборки на macOS

1. Получить исходники и применить патч (см. `../verify/apply_patch.sh`, либо `git clone --recursive -j8 https://github.com/Swiftgram/Telegram-iOS.git` + `git apply ../patches/0001-fourfour-rebrand.patch`).

2. Подготовить конфигурацию сборки (bundle id, api_id/api_hash, team_id) — как в README апстрима:

```bash
openssl rand -hex 8
# создать Xcode-проект с Product Name = Swiftgram, Organization Identifier = org.<hex>
# взять Team ID из сертификата Apple Development
# заполнить build-system/template_minimal_development_configuration.json
```

   Ничего из этих настроек патч не меняет: bundle id, scheme, entitlements, provisioning, team id — как в апстриме
   (хеши файлов: `../baseline/UNTOUCHED-CONFIG-SHA256.txt`).

3. Собрать:

```bash
python3 build-system/Make/Make.py \
    --cacheDir="$HOME/telegram-bazel-cache" \
    build \
    --configurationPath=build-system/template_minimal_development_configuration.json \
    --xcodeManagedCodesigning \
    --buildNumber=1 \
    --configuration=debug
```

   Артефакты: `bazel-bin/Telegram/fourfour.ipa` (имя IPA выводится из имени bazel-таргета — он остался
   `Swiftgram`, поэтому файл может называться `Swiftgram.ipa`; имя **приложения на iPhone** берётся
   из `CFBundleDisplayName` и будет `fourfour`).

   Симулятор:

```bash
python3 build-system/Make/Make.py \
    --cacheDir="$HOME/telegram-bazel-cache" \
    generateProject \
    --configurationPath=build-system/template_minimal_development_configuration.json \
    --xcodeManagedCodesigning
# далее в Xcode: схема fourfour/Swiftgram, симулятор iPhone, Run
```

4. Установка на устройство/в симулятор:

```bash
xcrun simctl install booted "путь/к/fourfour.app"
xcrun simctl launch booted <bundle-id>
```

## Что проверить после сборки (5 минут)

1. **Домашний экран iPhone** — подпись под иконкой: `fourfour`.
2. **Настройки iOS → Основные → Хранилище iPhone** — имя приложения: `fourfour`.
3. **Настройки (вкладка) → пункт `Swiftgram` → экран настроек четыре-четыре**:
   * по центру верхней панели — `fourfour`;
   * фон верхней панели — чёрный `#000000`, надпись и кнопка «Назад» — белые;
   * часы/индикаторы статус-бара на этом экране — белые (на чёрном фоне).
4. **Остальной интерфейс** — чаты, сообщения, настройки Telegram, кнопки — без изменений.
5. Системное меню «Поделиться», галерея виджетов, Siri — имя `fourfour`.

## Откат

```bash
cp fourfour-rebrand/baseline/original/Telegram/BUILD  <checkout>/Telegram/BUILD
cp fourfour-rebrand/baseline/original/Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift \
   <checkout>/Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift
```
