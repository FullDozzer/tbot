# Апстрим, к которому применяются изменения

| Параметр | Значение |
| --- | --- |
| Репозиторий | `https://github.com/Swiftgram/Telegram-iOS` |
| Ветка | `master` |
| Коммит (HEAD на момент работы) | `cf8b23beaaac4126a396337ac2d5be13f9f76b66` |
| Дата коммита | 2026-07-29 |
| Архив исходников | `https://codeload.github.com/Swiftgram/Telegram-iOS/tar.gz/refs/heads/master` |
| SHA-256 архива | `cb17299b5c37329645c32720f58a6516e32e757b0aebefa934863a73f43cbed1` |
| Файлов в дереве | 30 264 |
| Размер дерева | ≈ 461 МБ (в git не хранится — см. «Почему исходники не в репозитории» в README.md) |

Полный исходный код в git этого репозитория **не коммитится** (461 МБ, десятки тысяч файлов).
Вместо этого сохраняются:

* `patches/` — патч(и), которые применяются к чистому апстриму;
* `changed-files/` — готовые версии изменённых файлов (можно просто скопировать);
* `baseline/original/` — копии **оригинальных** версий этих файлов (для отката и сверки).

Проверить, что базовая версия скачана правильно:

```bash
curl -L -o swiftgram.tar.gz \
  https://codeload.github.com/Swiftgram/Telegram-iOS/tar.gz/refs/heads/master
shasum -a 256 swiftgram.tar.gz
# cb17299b5c37329645c32720f58a6516e32e757b0aebefa934863a73f43cbed1
mkdir -p upstream && tar -xzf swiftgram.tar.gz -C upstream
```
