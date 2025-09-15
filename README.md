# FFConverter — Universal Data Converter v2.0 (GUI)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-3776AB.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/UI-Tkinter-1f6feb.svg)](#)
[![Version](https://img.shields.io/badge/version-2.0-brightgreen.svg)](#)
[![Pandas](https://img.shields.io/badge/pandas-required-150458.svg)](https://pandas.pydata.org/)
[![OpenPyXL](https://img.shields.io/badge/openpyxl-required-019733.svg)](https://openpyxl.readthedocs.io/)
[![Tabulate](https://img.shields.io/badge/tabulate-required-4C9A2A.svg)](#)
[![DragDrop](https://img.shields.io/badge/drag%26drop-optional-orange.svg)](#)

FFConverter v2.0 is an advanced desktop GUI application built with Tkinter for converting structured data files between multiple formats: CSV, XLSX, JSON, XML, YAML, INI, TXT, and Markdown. It features drag & drop support, comprehensive settings management, data validation, logging system, and supports opening source code files in many programming languages with preview capabilities.

## Key Features

### Core Functionality
- **Auto-detection** of input format by file extension and intelligent content probing (JSON/XML/YAML/INI heuristics)
- **Supported input formats**: csv, xlsx, json, xml, yaml/yml, ini, txt, md; source code files detected separately
- **Supported output formats**: csv, xlsx, json, xml, yaml, ini, txt, md
- **Source code support**: Python, C/C++, Java, C#, JavaScript, TypeScript, Go, Ruby, Swift, Shell, Batch, Perl, PHP, Rust, Scala, Kotlin, Dart
- **Code files** can be saved only as TXT or MD (preserves lines; no parsing)

### Advanced GUI Features
- **Dark theme UI** with modern styling and custom color scheme
- **Drag & Drop support** (optional tkinterdnd2 dependency)
- **Live preview panel** with adjustable number of lines/rows and DataFrame-to-Markdown rendering
- **Progress indicators** with threaded operations for better responsiveness
- **Settings window** with configurable GUI and processing options
- **Status updates** and comprehensive error handling

### System Features
- **Configuration management** with persistent settings (settings.ini)
- **Comprehensive logging** with daily log files and operation tracking
- **Data validation** with file size limits and access checks
- **Threading** for non-blocking file operations
- **Error recovery** with detailed error reporting and traceback

## Requirements

- **Python 3.8+** on Windows/macOS/Linux
- **Required packages**: pandas, pyyaml, openpyxl, tabulate, lxml
- **Optional packages**: tkinterdnd2 (for drag & drop functionality)
- No external binaries needed; all conversions are handled in Python using pandas, PyYAML, OpenPyXL, ConfigParser, and ElementTree

## Installation

# 1) Clone the repository
git clone https://github.com/VioletSoul/FFConverter.git
cd FFConverter

# 2) (Optional) Create & activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3) Install required dependencies
pip install pandas pyyaml openpyxl tabulate lxml

# 4) (Optional) Install drag & drop support
pip install tkinterdnd2

If dependencies are missing, the app will display detailed installation instructions and exit gracefully.

## Running

python ffconverter.py

This launches a Tkinter window titled "Универсальный конвертер данных v2.0". You can:
- Use "📁 Выбрать файл" button to open a supported file
- **Drag and drop** files directly onto the window (if tkinterdnd2 is installed)
- Choose the target format in the dropdown and click "🔄 Конвертировать"
- Access settings via "⚙ Настройки" button

## Configuration & Settings

The application features a comprehensive settings system accessible through the settings window:

### GUI Settings
- **Window size**: Customizable width and height
- **Font size**: Adjustable for better readability (8-20px)
- **Preview lines**: Configure number of lines shown in preview (5-100)

### Processing Settings
- **File size limits**: Maximum file size in MB (default: 100MB)
- **Data validation**: Enable/disable file validation checks
- **Progress indicators**: Show/hide progress bars during operations

Settings are automatically saved to `settings.ini` and persist between sessions.

## Logging System

FFConverter v2.0 includes comprehensive logging:
- **Daily log files** stored in `logs/` directory
- **Operation tracking** for file reads, writes, and errors
- **Automatic log rotation** with date-based filenames
- **Detailed error reporting** with full tracebacks

Log files are named as: `converter_YYYYMMDD.log`

## Format Detection

- **Extension-based detection** for quick routing: .csv, .xlsx, .json, .xml, .yaml/.yml, .ini, .txt, .md
- **Source code detection** for programming languages: .py, .cpp, .c, .h, .java, .cs, .js, .ts, .go, .rb, .swift, .sh, .bat, .pl, .php, .rs, .scala, .kt, .dart
- **Content-based fallback**: Probes first ~2048 characters to identify JSON, XML, YAML, or INI via safe parsers
- **Smart defaults** to TXT when format is ambiguous

## Data Processing Logic

### Reading Logic
- **Code files**: Read as list of lines (no parsing, preserves formatting)
- **CSV/XLSX**: Loaded into pandas DataFrame with automatic encoding detection
- **JSON/YAML**: Lists → DataFrame; dicts → DataFrame row if possible, else preserved as dict
- **XML**: Attempts table extraction by iterating child elements into records; falls back to dict-like root mapping
- **INI**: ConfigParser to dict of sections; transposed into DataFrame for tabular view
- **TXT/MD**: Read as raw lines for preview and conversion

### Saving Logic
- **CSV**: `DataFrame.to_csv(index=False)` with UTF-8 encoding
- **XLSX**: `DataFrame.to_excel(index=False)` via openpyxl
- **JSON**: `DataFrame.to_json(orient="records", indent=2)` with Unicode support
- **XML**: Builds `<records><record>…</record></records>` with XML-safe tags and escaped text
- **YAML**: Dumps DataFrame records as list of dicts with Unicode support
- **INI**: Each DataFrame row becomes a section with column→value mapping
- **Markdown**: `DataFrame.to_markdown(index=False)` requires tabulate
- **TXT**: `DataFrame.to_string(index=False)` for aligned text tables
- **Code preservation**: Source code saved verbatim to TXT/MD only

## GUI Enhancements

### Visual Design
- **Dark theme** with custom color scheme for better user experience
- **Modern styling** with custom fonts and improved spacing
- **Responsive layout** that adapts to different window sizes
- **Professional appearance** with accent colors and consistent design

### User Experience
- **Live preview updates** when changing preview line count
- **Threaded operations** prevent GUI freezing during file processing
- **Progress indicators** show operation status
- **Comprehensive error messages** with user-friendly explanations
- **Drag & drop visual feedback** when supported

## Architecture

### Core Classes

class AppLogger:          # Logging system with daily rotation
class AppConfig:          # Configuration management (settings.ini)
class DataValidator:      # File validation and security checks
class SettingsWindow:     # GUI settings management window
class DataConverterGUI:   # Main application window and logic

### Key Constants

SUPPORTED_FORMATS = ["csv", "xlsx", "json", "xml", "yaml", "ini", "txt", "md"]
SOURCE_EXTS = [".py", ".cpp", ".c", ".h", ".java", ".cs", ".js", ".ts", ".go",
".rb", ".swift", ".sh", ".bat", ".pl", ".php", ".rs", ".scala",
".kt", ".dart"]

## Usage Notes and Limitations

- **Complex nested data**: Converting deeply nested JSON/YAML/XML may require manual flattening
- **XML schema limitations**: Simple record-based output; attributes and complex hierarchies not preserved
- **Source code handling**: Files treated as plain text without syntax highlighting or parsing
- **Memory considerations**: Large files are processed entirely in memory; size limits configurable
- **Unicode support**: Full UTF-8 support for international characters in all formats

## Advanced Features

### Data Validation
- **File accessibility checks** before processing
- **Size validation** with configurable limits (default 100MB)
- **Format verification** with intelligent error recovery
- **Path validation** for output directories

### Performance Optimizations
- **Threaded file operations** for responsive UI
- **Efficient memory usage** with streaming where possible
- **Progress tracking** for long-running operations
- **Configurable processing limits** to prevent system overload

### Error Handling
- **Graceful degradation** when optional features unavailable
- **Detailed error messages** with actionable solutions
- **Comprehensive logging** for debugging and troubleshooting
- **User-friendly notifications** via message boxes

## Troubleshooting

### Dependency Issues

# Install all required packages
pip install pandas pyyaml openpyxl tabulate lxml

# For drag & drop support
pip install tkinterdnd2

### Common Problems
- **Excel save issues**: Ensure openpyxl is installed and output path is writable
- **YAML/JSON errors**: Verify UTF-8 encoding and valid syntax
- **XML parse errors**: Ensure well-formed XML structure
- **Memory errors**: Reduce file size limits in settings or split large files
- **Permission errors**: Check file and directory permissions
- **Drag & drop not working**: Install tkinterdnd2 package

### Log Analysis
Check the `logs/` directory for detailed operation logs and error information:

# View recent logs
tail -f logs/converter_20250915.log

## Development

### Architecture Features
- **Single-file architecture** using Tkinter standard library with modular class design
- **Extensible format support** through handler dictionaries
- **Configuration-driven behavior** for easy customization
- **Comprehensive error handling** with logging integration
- **Clean separation** of GUI, logic, and utility functions

### Adding New Formats

To add support for new formats, update these dictionaries:

READERS = {"format": reader_function}
WRITERS = {"format": writer_function}
SUPPORTED_FORMATS.append("new_format")

### Customization
- Modify color constants for different themes
- Adjust default settings in `AppConfig.create_default_config()`
- Extend validation rules in `DataValidator` class

## Version History

### v2.0 New Features
- **Settings management system** with persistent configuration
- **Comprehensive logging** with daily rotation and operation tracking
- **Data validation** with file size limits and security checks
- **Drag & drop support** (optional tkinterdnd2 integration)
- **Threading** for non-blocking file operations
- **Progress indicators** with visual feedback
- **Enhanced error handling** with detailed reporting
- **Modern dark theme** with improved UI/UX
- **Modular architecture** with separated concerns

## License

MIT License. See LICENSE for details.

## Support

If you encounter issues:
1. Check the `logs/` directory for error details
2. Verify all dependencies are installed
3. Review the troubleshooting section
4. Open an issue on GitHub with log files and system information
