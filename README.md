# FFConverter — Universal Data Converter (GUI)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/UI-Tkinter-1f6feb.svg)](#)
[![Pandas](https://img.shields.io/badge/pandas-required-150458.svg)](https://pandas.pydata.org/)
[![OpenPyXL](https://img.shields.io/badge/openpyxl-required-019733.svg)](https://openpyxl.readthedocs.io/)
[![Tabulate](https://img.shields.io/badge/tabulate-required-4C9A2A.svg)](#)

FFConverter is a desktop GUI tool built with Tkinter for converting structured data files between formats: CSV, XLSX, JSON, XML, YAML, INI, TXT, and Markdown. It also supports opening source code files in many languages and saving them as TXT or Markdown with preview. [8][9]

## Key Features

- Auto-detect input format by file extension and lightweight content probing (JSON/XML/YAML/INI heuristics). [9]
- Supported input formats: csv, xlsx, json, xml, yaml/yml, ini, txt, md; source code files detected separately. [9]
- Supported output formats for data: csv, xlsx, json, xml, yaml, ini, txt, md. [9]
- Source code files can be saved only as TXT or MD (preserves lines; no parsing). [9]
- Preview panel with adjustable number of lines/rows and DataFrame-to-Markdown rendering for tabular data. Requires tabulate for Markdown preview. [3][4]
- Clean GUI: file chooser, detected input label, target format combobox, convert button, status bar, scrollable preview. [8]

## Requirements

- Python 3.8+ on Windows/macOS/Linux. [9]
- Packages: pandas, pyyaml, openpyxl, tabulate. The script checks and prompts to install them at startup if missing. [3][4]
- No external binaries needed; all conversions are handled in Python using pandas, PyYAML, OpenPyXL, ConfigParser, and ElementTree. [9]

## Installation

```
# 1) Clone the repository
git clone https://github.com/VioletSoul/FFConverter.git
cd FFConverter

# 2) (Optional) Create & activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3) Install dependencies
pip install -r requirements.txt  # if the file exists
# or explicitly:
pip install pandas pyyaml openpyxl tabulate
```
[9][3][4]

If dependencies are missing, the app prints an instruction like:
```
pip install pandas pyyaml openpyxl tabulate
```
and exits, as enforced in the script’s __main__ block. [9]

## Running

```
python ffconverter.py
```
This launches a Tkinter window titled “Универсальный конвертер данных”. Use “Выбрать файл” to open a supported file, then choose the target format in the combobox and click “Конвертировать”. [8][9]

## Format Detection

- Uses extension for quick routing: .csv, .xlsx, .json, .xml, .yaml/.yml, .ini, .txt, .md. Source files like .py, .cpp, .java, .cs, .js, .ts, .go, .rb, .swift, .sh, .bat, .pl, .php, .rs, .scala, .kt, .dart are treated as “code”. [9]
- If extension is ambiguous, the tool probes the first ~2048 characters to identify JSON, XML, YAML, or INI via safe parsers; otherwise defaults to TXT. [9]

## Reading Logic (Summary)

- code: read as a list of lines (no parsing). [9]
- csv/xlsx: loaded into pandas DataFrame. [9]
- json/yaml: list → DataFrame; dict → DataFrame row if possible, else keep dict. [9]
- xml: attempts simple table extraction by iterating child elements into records; falls back to dict-like root map or error string. [9]
- ini: ConfigParser to dict of sections; transposed into DataFrame. [9]
- txt/md: read as lines. [9]

## Saving Logic (Summary)

- csv: DataFrame.to_csv(index=False). [9]
- xlsx: DataFrame.to_excel(index=False). [9]
- json: DataFrame.to_json(orient="records", indent=2, UTF-8). [9]
- xml: builds <records><record>…</record></records> with XML-safe tags and escaped text. [9]
- yaml: dumps DataFrame records as list of dicts with unicode. [9]
- ini: each DataFrame row becomes a section with column→value mapping. [9]
- md: DataFrame.to_markdown(index=False) requires tabulate installed. [3][4]
- txt: each row rendered as a pipe-separated line “v1 | v2 | …”. [9]
- code: saved verbatim lines to TXT/MD only. [9]

## GUI Highlights

- Theme and colors for dark UI; custom fonts for headings and preview. [8]
- Preview shows first N lines/rows (configurable via Spinbox), with live updates on value change or focus out. [8]
- For DataFrames, preview uses Markdown rendering; for lists/lines and code, shows concatenated lines; for dicts, shows pretty JSON. [3][4]

## Usage Notes and Limitations

- Converting non-tabular nested JSON/YAML/XML may need flattening; the tool attempts basic DataFrame coercion but may fall back to dict/list where appropriate. [9]
- XML writing uses simple record-based schema with tag sanitization and HTML-escaped text; attributes/nested hierarchies are not preserved beyond flat records. [9]
- Source code files are not parsed or syntax-highlighted; they are treated as plain text. [9]
- Markdown previews of tables depend on pandas.to_markdown which requires the tabulate package. [3][4]

## Troubleshooting

- Missing packages: install as instructed and restart.
```
pip install pandas pyyaml openpyxl tabulate
```
[3][4]

- Excel save issues: ensure openpyxl is installed and the output path is writable. [3]
- YAML/JSON parse errors: verify encoding is UTF‑8 and input is valid; malformed files will raise parse exceptions. [9]
- XML parse errors: ensure well-formed XML; partial/binary files can’t be parsed by ElementTree. [9]

## Development

- Single-file GUI app using Tkinter standard library; no special setup beyond dependencies. [8][9]
- Linting/formatting recommended but not required; contributions can refactor reading/writing handlers into modules. [9]

## License

MIT License. See LICENSE for details. [9]
```
