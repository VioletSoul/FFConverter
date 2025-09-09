# FFConverter — универсальный конвертер данных (GUI)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/UI-Tkinter-1f6feb.svg)](#)
[![Pandas](https://img.shields.io/badge/pandas-required-150458.svg)](https://pandas.pydata.org/)
[![OpenPyXL](https://img.shields.io/badge/openpyxl-required-019733.svg)](https://openpyxl.readthedocs.io/)
[![Tabulate](https://img.shields.io/badge/tabulate-required-4C9A2A.svg)](#)

FFConverter — это настольная утилита с графическим интерфейсом (Tkinter) для конвертации структурированных файлов между форматами: CSV, XLSX, JSON, XML, YAML, INI, TXT и Markdown. Также поддерживается открытие исходных файлов кода на разных языках и сохранение их как TXT или Markdown с предпросмотром.

## Основные возможности

- Автоопределение входного формата по расширению и лёгкому анализу содержимого (эвристики для JSON/XML/YAML/INI).
- Входные форматы: csv, xlsx, json, xml, yaml/yml, ini, txt, md; исходные файлы кода детектируются отдельно.
- Выходные форматы данных: csv, xlsx, json, xml, yaml, ini, txt, md.
- Исходники можно сохранять только в TXT или MD (без разбора, построчно).
- Предпросмотр с настраиваемым числом строк/строк и рендерингом DataFrame в Markdown для табличных данных (требуется tabulate).
- Чистый GUI: выбор файла, отображение определённого формата, комбобокс формата назначения, кнопка «Конвертировать», статус-бар, прокручиваемый предпросмотр.

## Требования

- Python 3.8+ для Windows/macOS/Linux.
- Пакеты: pandas, pyyaml, openpyxl, tabulate. Если пакеты отсутствуют, выполните:
  '''pip install pandas pyyaml openpyxl tabulate'''
- Внешние бинарные зависимости не нужны; конвертация реализована на Python с использованием pandas, PyYAML, OpenPyXL, ConfigParser и ElementTree.

## Установка

- Клонирование репозитория:
  '''git clone https://github.com/VioletSoul/FFConverter.git
  cd FFConverter'''
- (Опционально) Виртуальное окружение:
  '''python -m venv .venv
  .venv\Scripts\activate  # Windows
  source .venv/bin/activate  # macOS/Linux'''
- Установка зависимостей:
  '''pip install -r requirements.txt'''
  или явно:
  '''pip install pandas pyyaml openpyxl tabulate'''

## Запуск

- Старт приложения:
  '''python ffconverter.py'''
  Откроется окно «Универсальный конвертер данных». Нажмите «Выбрать файл», затем выберите целевой формат в комбобоксе и нажмите «Конвертировать».

## Определение формата

- По расширению: .csv, .xlsx, .json, .xml, .yaml/.yml, .ini, .txt, .md. Файлы исходников (.py, .cpp, .java, .cs, .js, .ts, .go, .rb, .swift, .sh, .bat, .pl, .php, .rs, .scala, .kt, .dart) распознаются как «код».
- Если расширение неоднозначно, анализируются первые ~2048 символов для распознавания JSON, XML, YAML или INI безопасными парсерами; иначе файл трактуется как TXT.

## Логика чтения (кратко)

- code: читается как список строк (без разбора).
- csv/xlsx: загружается в pandas DataFrame.
- json/yaml: list → DataFrame; dict → одна строка DataFrame, если возможно, иначе остаётся dict.
- xml: попытка простого извлечения таблицы итерацией по дочерним элементам; при неудаче — словарное представление корня или строка ошибки.
- ini: ConfigParser → dict секций; транcпонирование в DataFrame.
- txt/md: чтение построчно.

## Логика сохранения (кратко)

- csv: DataFrame.to_csv(index=False).
- xlsx: DataFrame.to_excel(index=False).
- json: DataFrame.to_json(orient="records", indent=2, UTF-8).
- xml: формирование структуры <records><record>…</record></records> с безопасными тегами и экранированным текстом.
- yaml: выгрузка записей DataFrame как списка словарей (Unicode поддерживается).
- ini: каждая строка DataFrame становится секцией с отображением столбец→значение.
- md: DataFrame.to_markdown(index=False) (требуется tabulate).
- txt: строки в виде «v1 | v2 | …».
- code: сохраняются исходные строки как TXT/MD.

## Особенности GUI

- Тёмная тема и кастомные шрифты для заголовков/предпросмотра.
- Предпросмотр первых N строк/строк (настраивается через Spinbox), живое обновление при изменении значения или потере фокуса.
- Для DataFrame — Markdown-рендеринг; для списков/кода — склеенные строки; для dict — «красивый» JSON.

## Примечания и ограничения

- Вложенные нетабличные JSON/YAML/XML могут потребовать нормализации; инструмент выполняет базовое приведение к DataFrame и при невозможности оставляет dict/list.
- XML-запись использует простую схему записей с санитизацией тегов и HTML-экранированием; атрибуты и глубокая иерархия не сохраняются полностью.
- Исходники не парсятся и не подсвечиваются — обрабатываются как простой текст.
- Предпросмотр таблиц в Markdown зависит от pandas.to_markdown и установленного tabulate.

## Устранение неполадок

- Нет необходимых пакетов — установите и перезапустите:
  '''pip install pandas pyyaml openpyxl tabulate'''
- Проблемы сохранения Excel — убедитесь, что установлен openpyxl и путь записи доступен.
- Ошибки парсинга YAML/JSON — проверьте UTF‑8 и валидность входных данных.
- Ошибки парсинга XML — проверьте корректность структуры; ElementTree не разбирает повреждённые/частично бинарные файлы.

## Разработка

- Однофайловое приложение на Tkinter (stdlib); помимо зависимостей, дополнительных настроек не требуется.
- Рекомендуются форматирование и линтинг; приветствуется рефакторинг обработчиков чтения/записи в отдельные модули.

## Лицензия

MIT License.
