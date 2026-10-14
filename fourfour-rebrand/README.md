# fourfour — минимальный ребрендинг Swiftgram (Telegram-iOS)

Репозиторий-источник: `https://github.com/Swiftgram/Telegram-iOS`
База: `master` @ `cf8b23beaaac4126a396337ac2d5be13f9f76b66` (2026-07-29) — подробности в [UPSTREAM.md](UPSTREAM.md).

Глобальная замена слова «Swiftgram» по репозиторию **не выполнялась**: затронуто 2 файла,
в них изменено 4 строки значений + добавлен один изолированный блок кода.

---

## 1. Итог по пунктам задания

| № | Требование | Статус | Где именно |
| --- | --- | --- | --- |
| 1 | Заменить надпись SWIFTGRAM в верхней плашке экрана настроек на `fourfour` | ✅ | `Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift:769` |
| 2 | Имя приложения на iPhone → `fourfour` | ✅ | `Telegram/BUILD:1740`, `Telegram/BUILD:1744` |
| 3 | Фон верхней плашки — чёрный `#000000` | ✅ | `Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift:143-187` |
| 4 | Интерфейс Telegram (чаты, сообщения, кнопки, остальные экраны) не меняется | ✅ | изменён только экран настроек fourfour; остальные файлы не тронуты |
| 5 | Сеть, авторизация, уведомления, функции не меняются | ✅ | в диффе нет ни одного файла этих подсистем |
| 6 | Найти точные файлы и внести только необходимые изменения | ✅ | см. §2 и §4 |
| 7 | Проверить Bundle Display Name, конфигурации сборки, ресурсы логотипа | ✅ | см. §4 (карта брендинга) |
| 8 | Сохранить оригиналы и настройки подписи, показать список файлов и результат сборки | ✅ / ⚠️ | оригиналы: `baseline/`; список файлов: §2; сборка IPA — только на macOS (нет Xcode в этой среде), команды и что проверено вместо сборки: [build/MACOS-BUILD.md](build/MACOS-BUILD.md), [build/VERIFICATION-LOG.txt](build/VERIFICATION-LOG.txt) |

---

## 2. Изменённые файлы (полный список)

### 2.1. `Telegram/BUILD` — отображаемое имя приложения (3 значения)

```diff
 plist_fragment(
     name = "AppNameInfoPlist",
     template =
     """
     <key>CFBundleDisplayName</key>
-    <string>Swiftgram</string>
+    <string>fourfour</string>
     """
 )

 plist_fragment(
     name = "TelegramInfoPlist",
     template =
     """
     <key>CFBundleDisplayName</key>
-    <string>Swiftgram</string>
+    <string>fourfour</string>
     <key>CFBundleIdentifier</key>
     <string>{telegram_bundle_id}</string>
     <key>CFBundleName</key>
-    <string>Swiftgram</string>
+    <string>fourfour</string>
     """
 )
```

* `TelegramInfoPlist` (строки 1740 и 1744) — это `Info.plist` **основного приложения** (`ios_application(name = "Swiftgram")`,
  `infoplists = [":TelegramInfoPlist", …]`). Именно `CFBundleDisplayName` даёт надпись под иконкой на домашнем экране iPhone,
  имя в переключателе приложений, в системных настройках, в системных запросах разрешений.
  `CFBundleName` (короткое имя, ≤15 символов) оставлен синхронным — он используется системой там, где нет `CFBundleDisplayName`.
* `AppNameInfoPlist` (строка 652) — имя для расширений (Share, Notification Content/Service, Siri Intents, Widget, Broadcast Upload).
  Если его не поменять, то в системном меню «Поделиться», в галерее виджетов и в Siri остался бы «Swiftgram».

### 2.2. `Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift` — верхняя плашка экрана настроек

1. **Надпись в верхней плашке** (`строка 769`):

```diff
-        let controllerState = ItemListControllerState(presentationData: ItemListPresentationData(presentationData), title: .text("Swiftgram"), …)
+        let controllerState = ItemListControllerState(presentationData: sgFourFourSettingsPresentationData(presentationData), title: .text("fourfour"), …)
```

2. **Чёрный фон плашки** — добавлен один локальный блок (`строки 143–187`), который формирует
   **копию активной темы только для этого экрана**:

```swift
// MARK: fourfour branding
// Фон верхней плашки (navigation bar) экрана настроек fourfour.
private let SGFourFourPlaqueBackgroundColor = UIColor(rgb: 0x000000)

private func sgFourFourSettingsPresentationData(_ presentationData: PresentationData) -> ItemListPresentationData {
    …
    // navigationBar: blurredBackgroundColor/opaqueBackgroundColor = #000000, текст и кнопки — белые
    // statusBarStyle: .white  (белые часы/индикаторы на чёрной плашке)
    // chat.inputPanel.panelControlColor = .white (кнопка «Назад» в стиле .glass)
    …
}
```

Почему так, а не «покрасить навбар глобально»: в Telegram-iOS верхняя панель рисуется из
`PresentationTheme.rootController.navigationBar`, а экран настроек — это `ItemListController`,
который берёт тему из `ItemListPresentationData`, формируемого в состоянии экрана.
Мы подменяем тему **только в состоянии этого экрана**, поэтому:

* фон плашки становится `#000000`, надпись и кнопка «Назад» — белые;
* цвета списка, ячеек, переключателей берутся из обычной темы (не изменяются);
* любой другой экран приложения работает с исходной темой без изменений.

---

## 3. Как применить изменения

Вариант A — патчем к чистому апстриму (рекомендуется):

```bash
./verify/apply_patch.sh            # скачает апстрим, сверит SHA-256 и применит патч
./verify/run_all.sh upstream/Telegram-iOS-master   # все проверки
```

Вариант B — вручную: скопировать файлы из `changed-files/` в соответствующие пути вашего чекаута:

```bash
cp changed-files/Telegram/BUILD                     <checkout>/Telegram/BUILD
cp changed-files/Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift \
                                                    <checkout>/Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift
```

Откат: `baseline/original/…` — это байт-в-байт оригинальные файлы апстрима.

```
../.github/workflows/fourfour-build.yml  сборка на macOS (GitHub Actions), публикует .ipa + имя из Info.plist
patches/0001-fourfour-rebrand.patch      патч (git apply / patch -p1)
changed-files/                           готовые изменённые файлы
baseline/original/                       оригиналы изменённых файлов
baseline/SHA256SUMS.txt                  хеши оригиналов и изменённых файлов
baseline/UNTOUCHED-CONFIG-SHA256.txt     хеши файлов подписи/bundle id (не менялись)
verify/check_branding.py                 45 проверок: значения, границы дифа, существование API
verify/check_swift_syntax.py             разбор Swift-файла грамматикой (tree-sitter)
verify/run_all.sh                        запуск всех проверок
verify/apply_patch.sh                    скачивание апстрима + применение патча
build/VERIFICATION-LOG.txt               лог проверок
build/MACOS-BUILD.md                     как собрать на macOS (Xcode/Bazel)
```

---

## 4. Карта брендинга: что проверено и почему не тронуто

| Файл / место | Что содержит | Влияет на отображаемое имя? | Изменено |
| --- | --- | --- | --- |
| `Telegram/BUILD` → `TelegramInfoPlist` (1740, 1744) | `CFBundleDisplayName`, `CFBundleName` основного приложения | **Да** — имя на домашнем экране | **Да** |
| `Telegram/BUILD` → `AppNameInfoPlist` (652) | `CFBundleDisplayName` расширений | **Да** (Share/Widget/Siri) | **Да** |
| `Telegram/BUILD` → `Share/NotificationContent/Widget/Intents/BroadcastUpload/SGActionRequestHandler/NotificationService` `CFBundleName` (993, 1085, 1192, 1305, 1438, 1577, 1671) | короткое внутреннее имя бандла расширения | Нет (в системном UI используется `CFBundleDisplayName` из `AppNameInfoPlist`) | Нет — минимальный дифф |
| `Telegram/BUILD` → `SGActionRequestHandlerInfoPlist` (1438–1440) | `CFBundleName` + `CFBundleDisplayName` «Open in Swiftgram» | Нет | Нет — расширение **отключено** в сборке (`# ":SGActionRequestHandler"` в списке extensions) |
| `Telegram/BUILD` (1802, 1806, 1808, 1812) | тексты разрешений (контакты, геолокация) с «Swiftgram» | Нет (это тексты диалогов, не имя) | Нет — по требованию «только необходимые изменения»; при желании правится тем же способом |
| `Telegram/Telegram-iOS/Info.plist`, `InfoBazel.plist` | `CFBundleDisplayName = ${APP_NAME}` | Нет — используется только устаревшей Xcode-сборкой (`APP_NAME` приходит из `Config-*.xcconfig`), bazel-сборка берёт `Telegram/BUILD` | Нет |
| `Telegram/Telegram-iOS/Config-Fork.xcconfig` (`APP_NAME=Telegram Fork`), `Config-AppStoreLLC.xcconfig` (`APP_NAME=Telegram`), `Config-Hockeyapp-Internal.xcconfig` | имя/bundle id/URL-схема официальных конфигураций | Нет для нашей сборки; там же лежат bundle id (подпись) | Нет |
| `Telegram/Telegram-iOS/*.lproj/InfoPlist.strings` (19 языков) | локализованные тексты разрешений | Нет — `CFBundleDisplayName` в них отсутствует, локализованного имени приложения нет | Нет |
| `Telegram/Telegram-iOS/en.lproj/Localizable.strings` → `"Application.Name" = "Swiftgram"` | строковый ресурс | Нет — по коду не используется (проверено поиском) | Нет |
| `Telegram/Telegram-iOS/Swiftgram.icon`, `DefaultAppIcon.xcassets/AppIconLLC.appiconset/Swiftgram.png`, `Telegram/Watch/App/.../AppIcon.appiconset/Swiftgram.png`, `Swiftgram/SGAppBadgeAssets/*`, `Swiftgram*/SwiftgramSettings.pdf` / `SwiftgramPro.pdf` / `SwiftgramContextMenu.pdf` | **ресурсы логотипа/иконки** | Нет — это изображения, на надпись под иконкой не влияют | Нет — задача просила менять только имя и плашку |
| `Telegram/WatchApp/project.yml` (54–55) | `CFBundleDisplayName: Swiftgram` приложения для Apple Watch | Да, но только для часов | Нет — watch-приложение подключается отдельным флагом `--embedWatchApp`, к iPhone-имени не относится |
| `Swiftgram/SGStrings/Strings/*/SGLocalizable.strings`, `PayWall` («Swiftgram Pro»), пункт «Swiftgram» в списке настроек, приветствие, e-mail-шаблоны | тексты интерфейса | Нет | Нет — задача просила только плашку |
| `Telegram/BUILD` → `ios_application(name = "Swiftgram")`, `xcodeproj(project_name = "Swiftgram")`, `//Swiftgram/...` | **внутренние идентификаторы** (таблички bazel, структура модулей) | Нет | Нет — по вашему требованию не ломать идентификаторы |
| bundle id / URL-схема / entitlements / provisioning (`Telegram/BUILD`, `build-system/*.json`) | **подпись и идентификация приложения** | Нет | Нет — не тронуто (см. `baseline/UNTOUCHED-CONFIG-SHA256.txt`) |

---

## 5. Что гарантированно не менялось (требования 4–5)

* В диффе **всего два файла**: `Telegram/BUILD` и `Swiftgram/SGSettingsUI/Sources/SGSettingsController.swift`.
  Ни один файл сетевого стека (`TelegramCore`, `MtProtoKit`), авторизации (`AuthorizationUI`),
  push-уведомлений (`NotificationService`, `SharedNotificationManager`), чатов/сообщений не затронут.
* В `SGSettingsController.swift` **удалена ровно одна строка** — прежний заголовок `"Swiftgram"`;
  всё остальное только добавлено (проверяется автоматически: `verify/check_branding.py`, проверка 3).
* Изменения видны только на одном экране — «Настройки → fourfour» (бывший «Настройки → Swiftgram»).
  Настройки, чаты, сообщения, кнопки и остальные экраны используют оригинальную тему и тексты.

---

## 6. Дополнительно: внутренние строки самого экрана настроек

Тема, из которой убрали чёрную плашку, применима и к другим местам — если нужно, меняется одной строкой:

| Что | Файл:строка | Как поменять |
| --- | --- | --- |
| Пункт «Swiftgram» в списке настроек (строка со значком ⚡) | `submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoSettingsItems.swift:229` | `text: "Swiftgram"` → `text: "fourfour"` |
| Заголовок экрана «Swiftgram Pro» | `Swiftgram/SGProUI/Sources/SGProUI.swift:174` | `title: .text("Swiftgram Pro")` → `…"fourfour Pro"` |
| Заголовок «Swiftgram Pro» на PayWall | `Swiftgram/SGPayWall/Sources/SGPayWall.swift:386` | `Text("Swiftgram Pro")` |
| Строка «SWIFTGRAM TONES» (звуки уведомлений) | `Telegram/Telegram-iOS/en.lproj/Localizable.strings:7562` | значение ключа |
| «UPDATE SWIFTGRAM» (кнопка в пузыре неподдерживаемого сообщения) | `…/en.lproj/Localizable.strings:3999` | значение ключа |

---

## 7. Что проверено и что проверяется сборкой

### 7.1. Проверено здесь (Linux, без Xcode) — лог: [build/VERIFICATION-LOG.txt](build/VERIFICATION-LOG.txt)

1. **Патч применяется к чистому апстриму** — `git apply --check` + побайтовое сравнение результата с `changed-files/`.
2. **Синтаксис Swift** — файл разобран грамматикой Swift (tree-sitter): `ERROR=0`, `MISSING=0`,
   столько же, сколько у оригинального файла.
3. **Значения в `Info.plist`-фрагментах** — XML каждого фрагмента разобран парсером plist:
   `CFBundleDisplayName = fourfour`, `CFBundleName = fourfour`.
4. **Границы изменений** — 6 изменённых строк в `Telegram/BUILD` (3 замена) и 1 удалённая строка в Swift-файле;
   `baseline/SHA256SUMS.txt` фиксирует хеши до/после.
5. **API** — 50 проверок: все использованные методы/типы существуют и объявлены `public`,
   метки аргументов и **порядок** именованных аргументов совпадают с объявлениями
   (проверка на порядок добавлена после того, как она поймала реальную ошибку порядка в первом варианте правки).

### 7.2. Сборка на macOS — GitHub Actions (`.github/workflows/fourfour-build.yml`)

Серьёзную сборку делает workflow на macOS-раннере GitHub Actions:

1. скачивает чистый апстрим и **сверяет SHA-256 архива** (`cb17299b…bed1`);
2. копирует файлы из `fourfour-rebrand/changed-files/`, печатает применённые изменения в лог;
3. ставит fake-сертификаты апстрима (`build-system/fake-codesigning`) — **Apple Developer аккаунт не нужен**;
4. собирает bazel-ом, как это делает CI самого апстрима
   (`build-system/Make/Make.py build --configurationPath=build-system/appstore-configuration.json --codesigningInformationPath=build-system/fake-codesigning --configuration=release_arm64`);
5. читает `CFBundleDisplayName`/`CFBundleName` из `Info.plist` **собранного приложения и из упакованного `.ipa`**,
   публикует их в Summary запуска и **падает с ошибкой**, если имя не `fourfour`;
6. загружает `.ipa` (unsigned) как артефакт `fourfour-ipa`.

Запуск: вручную (Actions → «fourfour build (macOS)» → Run workflow) или автоматически при push в ветку
(workflow лежит в `.github/workflows/fourfour-build.yml`, триггеры — `workflow_dispatch` и `push` с фильтром путей).

Ссылка на конкретный запуск: см. Actions в репозитории; результат последнего запуска приложен к отчёту
(скриншот/ссылка — в комментарии к PR). Что делать с полученным `.ipa`: подписать своим сертификатом
(AltStore/Sideloadly/`codesign`+provisioning) и установить на устройство.

### 7.3. Локальная сборка на своём Mac

Инструкции и чек-лист визуальной проверки — в [build/MACOS-BUILD.md](build/MACOS-BUILD.md).


---

## 8. Если «верхняя плашка» — это другой элемент

Сейчас переименована и окрашена в чёрный **верхняя панель экрана настроек fourfour**
(экран, который открывается из «Настройки → Swiftgram», заголовок по центру сверху).

Если имелся в виду другой элемент — правки точечные, скажите какой:

* **шапка вкладки «Настройки»** (большая шапка с аватаром, именем и телефоном) —
  `submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoHeaderNode.swift`
  (`isSettings`): там задаётся фон/«баннер» шапки (`backgroundBannerView`, wallpaper);
* **пункт «Swiftgram» в списке настроек** — `PeerInfoSettingsItems.swift:229` (см. §6);
* **имя приложения в системных настройках iOS** — уже закрыто пунктом 2 (Bundle Display Name).

Во всех случаях изменений будет не больше пары строк в одном файле.
