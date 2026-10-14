# Сборка fourfour (нужен macOS)

## Почему сборка не выполнена в этой среде

Проект Swiftgram/Telegram-iOS собирается только на macOS:

* сборка идёт через Bazel (`build-system/Make/Make.py`), который для iOS-таргетов требует Xcode и Apple-тулчейн;
* компилятор Swift, `xcodebuild`, `codesign`, `xcrun`, `simctl` доступны только в macOS.

В среде, где готовился этот патч (Linux, без Xcode/Swift-тулчейна), физически невозможно
собрать `.app`/`.ipa`. Вместо сборки выполнены статические проверки — см.
[VERIFICATION-LOG.txt](VERIFICATION-LOG.txt) и §7 в [../README.md](../README.md).

## Шаги сборки на macOS

1. Получить исходники **вместе с git-сабмодулями** и применить патч:

```bash
git clone --depth 1 --recurse-submodules --shallow-submodules \
    https://github.com/Swiftgram/Telegram-iOS.git Telegram-iOS
cd Telegram-iOS
git apply /path/to/tbot/fourfour-rebrand/patches/0001-fourfour-rebrand.patch
```

   Сабмодули обязательны для сборки (`third-party/td`, `third-party/webrtc/webrtc`,
   `submodules/TgVoipWebrtc/tgcalls`, `build-system/bazel-rules/*` и др.) — в tar.gz-архиве GitHub
   их нет, поэтому скачивание архива для **сборки** не подходит (для проверки патча — подходит,
   см. `../verify/apply_patch.sh`).

2. Подготовить конфигурацию сборки. Патч ничего из этого не меняет (bundle id, scheme, entitlements,
   provisioning, team id — как в апстриме; хеши файлов: `../baseline/UNTOUCHED-CONFIG-SHA256.txt`).

   Готовый вариант для сборки без своего Apple-аккаунта — файл из этого репозитория
   `../ci/appstore-configuration.json` (значения апстрима + обязательный для форка ключ `sg_config`,
   без него `Make.py` падает с «Configuration at ... does not contain sg_config»):

```bash
cp /path/to/tbot/fourfour-rebrand/ci/appstore-configuration.json build-system/my-configuration.json
python3 build-system/Make/ImportCertificates.py --path build-system/fake-codesigning/certs   # fake-подпись
```

   Свой аккаунт: `openssl rand -hex 8`, Xcode-проект с Product Name = `Swiftgram`, Organization
   Identifier = `org.<hex>`, Team ID из сертификата Apple Development → заполнить
   `build-system/template_minimal_development_configuration.json` (и не забыть `sg_config`).

3. Собрать (пример — сборка под устройство с fake-подписью; `.ipa` подписывается уже на вашей стороне):

```bash
python3 -u build-system/Make/Make.py \
    --overrideXcodeVersion \
    --cacheDir="$HOME/telegram-bazel-cache" \
    build \
    --configurationPath=build-system/my-configuration.json \
    --codesigningInformationPath=build-system/fake-codesigning \
    --buildNumber=1 \
    --configuration=debug_arm64 \
    --outputBuildArtifactsPath="$PWD/build-out"
```

   `--configuration` — одно из `debug_arm64`, `release_arm64`, `debug_sim_arm64`, `release_sim_arm64`
   (`--outputBuildArtifactsPath` доступен только для сборок под устройство). Сборка под симулятор
   вообще не требует подписи:

```bash
python3 -u build-system/Make/Make.py --overrideXcodeVersion build \
    --configurationPath=build-system/my-configuration.json \
    --codesigningInformationPath=build-system/fake-codesigning \
    --buildNumber=1 --configuration=debug_sim_arm64
```

   Артефакты: `build-out/Swiftgram.ipa` (имя IPA выводится из имени bazel-таргета — он остался
   `Swiftgram`, поэтому файл может называться `Swiftgram.ipa`; имя **приложения на iPhone** берётся
   из `CFBundleDisplayName` и будет `fourfour`).

   Симулятор:

```bash
# без подписи (fake-подпись), чтобы не требовался Apple-аккаунт:
python3 build-system/Make/Make.py --overrideXcodeVersion \
    generateProject \
    --configurationPath=build-system/my-configuration.json \
    --codesigningInformationPath=build-system/fake-codesigning
# далее в Xcode: схема Swiftgram (внутреннее имя не менялось), симулятор iPhone, Run
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
