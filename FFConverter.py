import os
import sys
import json
import csv
import yaml
import configparser
import pandas as pd
import xml.etree.ElementTree as ET
import html
import re
import traceback
import threading
import logging
from datetime import datetime
from pathlib import Path
from tkinter import (
    Tk, filedialog, StringVar, Text, END, messagebox, Label, Frame, Scrollbar,
    VERTICAL, RIGHT, Y, HORIZONTAL, BOTTOM, X, Spinbox, IntVar, BooleanVar, Toplevel
)
from tkinter import ttk
import tkinter.font as tkFont

# Опционально попытаться импортировать drag & drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    DND_FILES = None
    TkinterDnD = None

# --- Константы ---
SUPPORTED_FORMATS = ["csv", "xlsx", "json", "xml", "yaml", "ini", "txt", "md"]
SOURCE_EXTS = [
    ".py", ".cpp", ".c", ".h", ".java", ".cs", ".js", ".ts", ".go", ".rb", ".swift",
    ".sh", ".bat", ".pl", ".php", ".rs", ".scala", ".kt", ".dart"
]
CODE_NAMES = {
    ".py": "python code", ".cpp": "cpp code", ".c": "c code", ".h": "c header",
    ".java": "java code", ".cs": "csharp code", ".js": "js code", ".ts": "ts code",
    ".go": "go code", ".rb": "ruby code", ".swift": "swift code", ".sh": "bash code",
    ".bat": "batch file", ".pl": "perl code", ".php": "php code", ".rs": "rust code",
    ".scala": "scala code", ".kt": "kotlin code", ".dart": "dart code"
}

# --- Стили GUI ---
BG_MAIN = "#232832"
BG_SEC = "#2b3040"
BG_ALT = "#262b36"
TXT_MAIN = "#d3dae3"
TXT_ACCENT = "#59d7ff"
BTN_BG = "#364356"
BTN_FG = "#ffffff"
BTN_HOVER = "#60bbff"

# --- Настройка логирования ---
class AppLogger:
    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"converter_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log_operation(self, operation, file_path, status="SUCCESS", error=None):
        if status == "SUCCESS":
            self.logger.info(f"{operation}: {file_path}")
        else:
            self.logger.error(f"{operation} FAILED: {file_path} - {error}")

# --- Управление конфигурацией ---
class AppConfig:
    def __init__(self):
        self.config_file = Path("settings.ini")
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        if not self.config_file.exists():
            self.create_default_config()

        self.config.read(self.config_file, encoding='utf-8')

    def create_default_config(self):
        self.config['GUI'] = {
            'window_width': '950',
            'window_height': '760',
            'theme': 'dark',
            'font_size': '11',
            'preview_lines': '20'
        }

        self.config['PATHS'] = {
            'last_directory': str(Path.home()),
            'auto_save_directory': ''
        }

        self.config['PROCESSING'] = {
            'max_file_size_mb': '100',
            'enable_validation': 'true',
            'show_progress': 'true'
        }

        self.save_config()

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        if section not in self.config:
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.save_config()

# --- Валидация данных ---
class DataValidator:
    @staticmethod
    def validate_file_size(filepath, max_size_mb=100):
        """Проверка размера файла"""
        try:
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            return size_mb <= max_size_mb, size_mb
        except Exception:
            return False, 0

    @staticmethod
    def validate_file_access(filepath):
        """Проверка доступности файла"""
        try:
            return os.path.exists(filepath) and os.access(filepath, os.R_OK)
        except Exception:
            return False

    @staticmethod
    def validate_output_path(filepath):
        """Проверка возможности записи"""
        try:
            parent_dir = os.path.dirname(filepath)
            return os.access(parent_dir, os.W_OK)
        except Exception:
            return False

# --- Вспомогательные функции для XML ---
def xml_safe_tag(tag):
    tag = re.sub(r'[^a-zA-Z0-9_\.]', '_', str(tag).strip())
    return tag if re.match(r'^[a-zA-Z_]', tag) else f"f_{tag}"

def xml_safe_text(val):
    return html.escape(str(val), quote=True)

# --- Логика обработки данных ---
def _normalize_data_to_df(data):
    """Преобразует словари или списки в DataFrame."""
    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, dict):
        try:
            return pd.DataFrame([data])
        except Exception:
            return data
    return data

def _read_csv(path):
    return pd.read_csv(path)

def _read_xlsx(path):
    return pd.read_excel(path)

def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _normalize_data_to_df(data)

def _read_xml(path):
    try:
        return pd.read_xml(path, parser='etree')
    except (ValueError, ET.ParseError):
        tree = ET.parse(path)
        root = tree.getroot()
        records = [
            {element.tag: element.text for element in child}
            for child in root if list(child)
        ]
        if records:
            return pd.DataFrame(records)
        return {elem.tag: elem.text for elem in root}

def _read_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return _normalize_data_to_df(data)

def _read_ini(path):
    cp = configparser.ConfigParser()
    cp.read(path, encoding="utf-8")
    data = {section: dict(cp[section]) for section in cp.sections()}
    return pd.DataFrame(data).transpose()

def _read_text_based(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()

READERS = {
    "csv": _read_csv, "xlsx": _read_xlsx, "json": _read_json,
    "xml": _read_xml, "yaml": _read_yaml, "ini": _read_ini,
    "txt": _read_text_based, "md": _read_text_based, "code": _read_text_based
}

def _write_csv(df, path):
    df.to_csv(path, index=False)

def _write_xlsx(df, path):
    df.to_excel(path, index=False)

def _write_json(df, path):
    df.to_json(path, orient="records", force_ascii=False, indent=2)

def _write_xml(df, path):
    root = ET.Element("records")
    for _, row in df.iterrows():
        item = ET.SubElement(root, "record")
        for col, val in row.items():
            tag = xml_safe_tag(col)
            sub = ET.SubElement(item, tag)
            sub.text = xml_safe_text(val)
    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)

def _write_yaml(df, path):
    df_records = df.to_dict(orient="records")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(df_records, f, allow_unicode=True)

def _write_ini(df, path):
    cp = configparser.ConfigParser()
    for idx, row in df.iterrows():
        section = str(row.name) if df.index.name else str(idx)
        cp[section] = {str(col): str(row[col]) for col in df.columns}
    with open(path, "w", encoding="utf-8") as f:
        cp.write(f)

def _write_md(df, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(df.to_markdown(index=False))

def _write_txt(df, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(df.to_string(index=False))

WRITERS = {
    "csv": _write_csv, "xlsx": _write_xlsx, "json": _write_json,
    "xml": _write_xml, "yaml": _write_yaml, "ini": _write_ini,
    "md": _write_md, "txt": _write_txt
}

def read_data(filepath, ftype):
    reader = READERS.get(ftype)
    if not reader:
        raise ValueError(f"Неподдерживаемый формат для чтения: {ftype}")
    return reader(filepath)

def save_data(df, out_path, out_fmt):
    writer = WRITERS.get(out_fmt)
    if not writer:
        raise ValueError(f"Неподдерживаемый формат для сохранения: {out_fmt}")
    writer(df, out_path)

def save_code(content, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(content)

# --- Функции определения формата ---
def detect_format(filepath):
    ext = os.path.splitext(filepath)[-1].lower()
    if ext in SOURCE_EXTS: return "code"
    if ext == ".csv": return "csv"
    if ext == ".xlsx": return "xlsx"
    if ext == ".json": return "json"
    if ext == ".xml": return "xml"
    if ext in [".yaml", ".yml"]: return "yaml"
    if ext == ".ini": return "ini"
    if ext == ".txt": return "txt"
    if ext in [".md", ".markdown"]: return "md"

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            head = f.read(2048).strip()
            if head.startswith("{"):
                try: json.loads(head); return "json"
                except json.JSONDecodeError: pass
            if head.startswith("<"):
                try: ET.fromstring(head); return "xml"
                except ET.ParseError: pass
            try: yaml.safe_load(head); return "yaml"
            except (yaml.YAMLError, AttributeError): pass
            if "[" in head and "]" in head:
                cp = configparser.ConfigParser()
                try: cp.read_string(head); return "ini"
                except configparser.Error: pass
    except Exception:
        pass
    return "txt"

def get_pretty_format(filepath, fmt):
    if fmt == "code":
        ext = os.path.splitext(filepath)[-1].lower()
        return CODE_NAMES.get(ext, f"{ext[1:]} code" if ext.startswith('.') else "code")
    return fmt

# --- Окно настроек ---
class SettingsWindow:
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.window = None

    def show(self):
        if self.window and self.window.winfo_exists():
            self.window.focus()
            return

        self.window = Toplevel(self.parent)  # ✅ Исправлено: используем Toplevel, а не ttk.Toplevel
        self.window.title("Настройки")
        self.window.geometry("400x500")
        self.window.configure(bg=BG_SEC)
        self.window.grab_set()  # Модальное окно

        # Создание вкладок
        notebook = ttk.Notebook(self.window)

        # Вкладка GUI
        gui_frame = Frame(notebook, bg=BG_SEC, padx=20, pady=20)
        self.create_gui_settings(gui_frame)
        notebook.add(gui_frame, text="Интерфейс")

        # Вкладка обработки
        processing_frame = Frame(notebook, bg=BG_SEC, padx=20, pady=20)
        self.create_processing_settings(processing_frame)
        notebook.add(processing_frame, text="Обработка")

        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Кнопки
        button_frame = Frame(self.window, bg=BG_SEC)
        button_frame.pack(fill="x", padx=20, pady=10)

        ttk.Button(button_frame, text="Сохранить", command=self.save_settings).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.window.destroy).pack(side="right", padx=5)

    def create_gui_settings(self, parent):
        # Размер окна
        Label(parent, text="Размер окна:", bg=BG_SEC, fg=TXT_ACCENT).pack(anchor="w", pady=5)

        size_frame = Frame(parent, bg=BG_SEC)
        size_frame.pack(fill="x", pady=5)

        self.width_var = StringVar(value=self.config.get('GUI', 'window_width'))
        self.height_var = StringVar(value=self.config.get('GUI', 'window_height'))

        ttk.Entry(size_frame, textvariable=self.width_var, width=10).pack(side="left")
        Label(size_frame, text=" x ", bg=BG_SEC, fg=TXT_MAIN).pack(side="left")
        ttk.Entry(size_frame, textvariable=self.height_var, width=10).pack(side="left")

        # Размер шрифта
        Label(parent, text="Размер шрифта:", bg=BG_SEC, fg=TXT_ACCENT).pack(anchor="w", pady=(15,5))
        self.font_size_var = StringVar(value=self.config.get('GUI', 'font_size'))
        ttk.Spinbox(parent, from_=8, to=20, textvariable=self.font_size_var, width=10).pack(anchor="w")

        # Строки предпросмотра
        Label(parent, text="Строк в предпросмотре:", bg=BG_SEC, fg=TXT_ACCENT).pack(anchor="w", pady=(15,5))
        self.preview_lines_var = StringVar(value=self.config.get('GUI', 'preview_lines'))
        ttk.Spinbox(parent, from_=5, to=100, textvariable=self.preview_lines_var, width=10).pack(anchor="w")

    def create_processing_settings(self, parent):
        # Максимальный размер файла
        Label(parent, text="Максимальный размер файла (МБ):", bg=BG_SEC, fg=TXT_ACCENT).pack(anchor="w", pady=5)
        self.max_size_var = StringVar(value=self.config.get('PROCESSING', 'max_file_size_mb'))
        ttk.Entry(parent, textvariable=self.max_size_var, width=10).pack(anchor="w")

        # Включить валидацию
        self.validation_var = BooleanVar(value=self.config.get('PROCESSING', 'enable_validation') == 'true')
        ttk.Checkbutton(parent, text="Включить валидацию файлов", variable=self.validation_var).pack(anchor="w", pady=10)

        # Показывать прогресс
        self.progress_var = BooleanVar(value=self.config.get('PROCESSING', 'show_progress') == 'true')
        ttk.Checkbutton(parent, text="Показывать прогресс-бар", variable=self.progress_var).pack(anchor="w", pady=5)

    def save_settings(self):
        # Сохранение настроек GUI
        self.config.set('GUI', 'window_width', self.width_var.get())
        self.config.set('GUI', 'window_height', self.height_var.get())
        self.config.set('GUI', 'font_size', self.font_size_var.get())
        self.config.set('GUI', 'preview_lines', self.preview_lines_var.get())

        # Сохранение настроек обработки
        self.config.set('PROCESSING', 'max_file_size_mb', self.max_size_var.get())
        self.config.set('PROCESSING', 'enable_validation', str(self.validation_var.get()).lower())
        self.config.set('PROCESSING', 'show_progress', str(self.progress_var.get()).lower())

        messagebox.showinfo("Настройки", "Настройки сохранены! Перезапустите приложение для применения некоторых изменений.")
        self.window.destroy()

# --- GUI Класс ---
class DataConverterGUI:
    def __init__(self, master):
        self.master = master

        # Инициализация компонентов
        self.config = AppConfig()
        self.logger = AppLogger()
        self.validator = DataValidator()

        # Настройка окна
        window_width = self.config.get('GUI', 'window_width', '950')
        window_height = self.config.get('GUI', 'window_height', '760')

        self.master.title("Универсальный конвертер данных v2.0")
        self.master.geometry(f"{window_width}x{window_height}")
        self.master.configure(bg=BG_MAIN)

        # Переменные состояния
        self.file_path = ""
        self.in_format = StringVar()
        self.out_format = StringVar()
        self.status = StringVar(value="Готов к работе.")
        self.data_content = None
        self.n_preview = IntVar(value=int(self.config.get('GUI', 'preview_lines', '20')))
        self.pretty_format = ""

        # Настройка Drag & Drop только если доступно
        if DND_AVAILABLE:
            try:
                self.master.drop_target_register(DND_FILES)
                self.master.dnd_bind('<<Drop>>', self.on_drop)
                self.drag_drop_status = "Drag & Drop включен"
            except:
                self.drag_drop_status = "Drag & Drop недоступен"
        else:
            self.drag_drop_status = "Drag & Drop недоступен (установите tkinterdnd2)"

        self._build_gui()

        # Логирование запуска
        self.logger.log_operation("APPLICATION_START", f"Converter v2.0 - {self.drag_drop_status}")

    def on_drop(self, event):
        """Обработка перетаскивания файлов"""
        if DND_AVAILABLE:
            files = self.master.tk.splitlist(event.data)
            if files:
                self.process_file(files[0])

    def _build_gui(self):
        font_size = int(self.config.get('GUI', 'font_size', '11'))
        heading_font = tkFont.Font(family="Arial", size=18, weight="bold")
        label_font = tkFont.Font(family="Arial", size=12)
        text_font = tkFont.Font(family="Consolas", size=font_size)

        # Стили
        style = ttk.Style(self.master)
        style.theme_use("clam")
        style.configure("Accent.TButton", background=BTN_BG, foreground=BTN_FG,
                        font=label_font, borderwidth=1, focusthickness=2, relief="flat")
        style.map("Accent.TButton", background=[("active", BTN_HOVER)],
                  foreground=[("active", BTN_FG)])

        # Заголовок
        header_frame = Frame(self.master, bg=BG_MAIN)
        header_frame.pack(fill="x", pady=(16, 12), padx=19)

        Label(header_frame, text="Универсальный конвертер данных v2.0",
              font=heading_font, bg=BG_MAIN, fg=TXT_ACCENT, anchor="w").pack(side="left")

        ttk.Button(header_frame, text="⚙ Настройки",
                   command=self.show_settings, style="Accent.TButton").pack(side="right")

        # Основная панель управления
        control_frame = Frame(self.master, bg=BG_SEC, pady=9, padx=14)
        control_frame.pack(fill="x", padx=19, pady=(0, 13))

        # Первая строка - выбор файла
        row1 = Frame(control_frame, bg=BG_SEC)
        row1.pack(fill="x", pady=4)

        self.btn_file = ttk.Button(row1, text="📁 Выбрать файл",
                                   command=self.choose_file, style="Accent.TButton")
        self.btn_file.pack(side="left", padx=(0,12))

        drag_text = "или перетащите файл" if DND_AVAILABLE else ""
        self.in_label = Label(row1, text=f"Исходный формат: не выбран {drag_text}",
                              font=label_font, bg=BG_SEC, fg=TXT_ACCENT)
        self.in_label.pack(side="left", padx=8)

        # Вторая строка - конвертация
        row2 = Frame(control_frame, bg=BG_SEC)
        row2.pack(fill="x", pady=9)

        Label(row2, text="Конвертировать в:", font=label_font,
              bg=BG_SEC, fg=TXT_ACCENT).pack(side="left")

        self.format_combo = ttk.Combobox(row2, values=SUPPORTED_FORMATS,
                                         textvariable=self.out_format, width=14,
                                         font=label_font, state="readonly")
        self.format_combo.pack(side="left", padx=(8,21))

        self.btn_convert = ttk.Button(row2, text="🔄 Конвертировать",
                                      command=self.convert, style="Accent.TButton")
        self.btn_convert.pack(side="left")

        # Прогресс-бар
        self.progress = ttk.Progressbar(self.master, mode='indeterminate')
        self.progress.pack(fill="x", padx=19, pady=(0,7))
        self.progress.pack_forget()  # Скрыть по умолчанию

        # Статус-бар (сохраняем ссылку на виджет)
        self.status_label = Label(self.master, textvariable=self.status, fg=TXT_ACCENT,
                                  font=label_font, anchor="w", padx=12, bg=BG_MAIN)
        self.status_label.pack(fill="x", pady=(0,7), padx=10)

        # Панель предпросмотра
        preview_frame = Frame(self.master, bg=BG_MAIN)
        preview_frame.pack(fill="both", expand=True, padx=18, pady=(0,8))

        preview_top = Frame(preview_frame, bg=BG_MAIN)
        preview_top.pack(fill="x")

        self.preview_label = Label(preview_top, text=f"Просмотр первых {self.n_preview.get()} строк:",
                                   bg=BG_MAIN, font=label_font, anchor="w", fg=TXT_ACCENT)
        self.preview_label.pack(side="left", pady=(3,2))

        self.preview_format_label = Label(preview_top, text="", bg=BG_MAIN,
                                          fg="#b5e3ff", font=label_font)
        self.preview_format_label.pack(side="left", padx=(7,0))

        Label(preview_top, text=" Кол-во строк:", bg=BG_MAIN,
              fg=TXT_ACCENT, font=label_font).pack(side="left")

        self.spin_preview = Spinbox(preview_top, from_=5, to=500, width=5,
                                    textvariable=self.n_preview, bg=BG_ALT, fg=TXT_MAIN,
                                    font=label_font, relief="flat", command=self.update_preview)
        self.spin_preview.pack(side="left", padx=(3,9), pady=(1,1))
        self.spin_preview.bind("<Return>", lambda e: self.update_preview())

        # Текстовая область с прокруткой
        self.text = Text(preview_frame, width=125, height=35, font=text_font,
                         bg=BG_ALT, relief="ridge", borderwidth=2, fg=TXT_MAIN,
                         insertbackground=TXT_MAIN, wrap="none")

        yscroll = Scrollbar(preview_frame, orient=VERTICAL, command=self.text.yview,
                            bg=BG_ALT, troughcolor=BG_MAIN)
        xscroll = Scrollbar(self.master, orient=HORIZONTAL, command=self.text.xview,
                            bg=BG_ALT, troughcolor=BG_MAIN)

        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        yscroll.pack(in_=preview_frame, side=RIGHT, fill=Y)
        xscroll.pack(side=BOTTOM, fill=X, padx=18, pady=(0,8))
        self.text.pack(in_=preview_frame, side="left", fill="both", expand=True)

    def show_settings(self):
        """Показать окно настроек"""
        SettingsWindow(self.master, self.config).show()

    def show_progress(self):
        """Показать прогресс-бар"""
        if self.config.get('PROCESSING', 'show_progress', 'true') == 'true':
            self.progress.pack(fill="x", padx=19, pady=(0,7), before=self.status_label)
            self.progress.start(10)

    def hide_progress(self):
        """Скрыть прогресс-бар"""
        self.progress.stop()
        self.progress.pack_forget()

    def _set_ui_state(self, is_busy):
        """Включает/выключает элементы GUI во время операций."""
        state = "disabled" if is_busy else "normal"
        self.btn_file.config(state=state)
        self.btn_convert.config(state=state)
        self.format_combo.config(state="readonly" if not is_busy else "disabled")
        self.spin_preview.config(state=state)

        if is_busy:
            self.show_progress()
        else:
            self.hide_progress()

    def process_file(self, path):
        """Обработка выбранного файла"""
        if not path:
            return

        # Валидация
        if self.config.get('PROCESSING', 'enable_validation', 'true') == 'true':
            if not self.validator.validate_file_access(path):
                messagebox.showerror("Ошибка", "Файл недоступен для чтения!")
                return

            max_size = float(self.config.get('PROCESSING', 'max_file_size_mb', '100'))
            is_valid, size_mb = self.validator.validate_file_size(path, max_size)
            if not is_valid:
                messagebox.showerror("Ошибка",
                                     f"Файл слишком большой ({size_mb:.1f} МБ). Максимум: {max_size} МБ")
                return

        self.file_path = path
        self.status.set(f"Чтение файла: {os.path.basename(path)}...")
        self._set_ui_state(is_busy=True)

        threading.Thread(target=self._load_file_thread, args=(path,), daemon=True).start()

    def update_preview(self):
        self.text.delete(1.0, END)
        try:
            n = max(1, self.n_preview.get())
        except Exception:
            n = 20
            self.n_preview.set(n)

        self.preview_label.config(text=f"Просмотр первых {n} строк:")
        self.preview_format_label.config(text=f" [{self.pretty_format}]" if self.pretty_format else "")

        if self.data_content is None:
            return

        try:
            content = self.data_content
            fmt = self.in_format.get()
            preview = ""

            if fmt == "code" or isinstance(content, list):
                preview = "".join(content[:n])
            elif isinstance(content, pd.DataFrame):
                preview = content.head(n).to_markdown(index=False)
            elif isinstance(content, dict):
                preview = json.dumps(content, ensure_ascii=False, indent=3)
            else:
                preview = str(content)[:5000]

            self.text.insert(END, preview)
        except Exception as e:
            self.text.insert(END, f"Ошибка обновления предпросмотра: {e}\n\n{traceback.format_exc()}")

    def choose_file(self):
        """Диалог выбора файла"""
        initial_dir = self.config.get('PATHS', 'last_directory', str(Path.home()))

        path = filedialog.askopenfilename(
            title="Выберите файл",
            initialdir=initial_dir,
            filetypes=[
                ("Все поддерживаемые", "*.csv *.xlsx *.json *.xml *.yaml *.yml *.ini *.txt *.md *.py *.cpp *.c *.h *.java *.cs *.js *.ts *.go *.rb *.swift *.sh *.bat *.pl *.php *.rs *.scala *.kt *.dart"),
                ("Все файлы", "*.*")
            ]
        )

        if path:
            self.config.set('PATHS', 'last_directory', os.path.dirname(path))
            self.process_file(path)

    def _load_file_thread(self, path):
        """Поток загрузки файла"""
        try:
            fmt = detect_format(path)
            data = read_data(path, fmt)
            self.logger.log_operation("FILE_READ", path)
            self.master.after(0, self._finish_loading, fmt, data, path)
        except Exception as e:
            error_info = f"Ошибка чтения файла: {e}\n\n{traceback.format_exc()}"
            self.logger.log_operation("FILE_READ", path, "ERROR", str(e))
            self.master.after(0, self._operation_error, error_info)

    def _finish_loading(self, fmt, data, path):
        """Завершение загрузки файла"""
        self.data_content = data
        self.pretty_format = get_pretty_format(path, fmt)
        self.in_format.set(fmt)

        self.in_label.config(text=f"Исходный формат: {self.pretty_format}")
        self.status.set(f"Файл загружен: {os.path.basename(path)} ({self.pretty_format})")

        self.format_combo["values"] = ["txt", "md"] if fmt == "code" else SUPPORTED_FORMATS
        self.out_format.set('')

        self.update_preview()
        self._set_ui_state(is_busy=False)

    def convert(self):
        """Начало процесса конвертации"""
        if not self.file_path or not self.in_format.get():
            messagebox.showerror("Ошибка", "Сначала выберите и загрузите файл!")
            return

        target_fmt = self.out_format.get()
        if not target_fmt:
            messagebox.showerror("Ошибка", "Выберите корректный формат для конвертации!")
            return

        current_fmt = self.in_format.get()
        if current_fmt == "code" and target_fmt not in ["txt", "md"]:
            messagebox.showerror("Ошибка", "Исходный код можно сохранять только как .txt или .md!")
            return

        # Диалог сохранения
        initial_dir = self.config.get('PATHS', 'last_directory', str(Path.home()))

        save_path = filedialog.asksaveasfilename(
            defaultextension=f".{target_fmt}",
            initialdir=initial_dir,
            filetypes=[(f"{target_fmt.upper()}", f"*.{target_fmt}"), ("Все файлы", "*.*")]
        )

        if not save_path:
            return

        # Валидация пути сохранения
        if self.config.get('PROCESSING', 'enable_validation', 'true') == 'true':
            if not self.validator.validate_output_path(save_path):
                messagebox.showerror("Ошибка", "Нет прав на запись в выбранную директорию!")
                return

        self.config.set('PATHS', 'last_directory', os.path.dirname(save_path))
        self.status.set(f"Конвертация в {target_fmt}...")
        self._set_ui_state(is_busy=True)

        threading.Thread(target=self._save_file_thread, args=(save_path, target_fmt), daemon=True).start()

    def _save_file_thread(self, save_path, target_fmt):
        """Поток сохранения файла"""
        try:
            current_fmt = self.in_format.get()
            if current_fmt == "code":
                save_code(self.data_content, save_path)
            else:
                df = self.data_content
                if not isinstance(df, pd.DataFrame):
                    df = _normalize_data_to_df(df)
                    if not isinstance(df, pd.DataFrame):
                        raise TypeError("Не удалось привести структуру данных к табличному виду для сохранения.")
                save_data(df, save_path, target_fmt)

            self.logger.log_operation("FILE_SAVE", save_path)
            self.master.after(0, self._finish_saving, save_path)
        except Exception as e:
            error_info = f"Ошибка конвертации: {e}\n\n{traceback.format_exc()}"
            self.logger.log_operation("FILE_SAVE", save_path, "ERROR", str(e))
            self.master.after(0, self._operation_error, error_info)

    def _finish_saving(self, save_path):
        """Завершение сохранения"""
        self.status.set(f"Успех! Сохранено в {os.path.basename(save_path)}")
        self.text.insert(END, f"\n\n--- Успешно сохранено в: {save_path} ---\n")
        self._set_ui_state(is_busy=False)
        messagebox.showinfo("Успех", f"Файл успешно сохранен по пути:\n{save_path}")

    def _operation_error(self, error_info):
        """Обработка ошибок операций"""
        self.status.set("Произошла ошибка.")
        self.text.delete(1.0, END)
        self.text.insert(END, error_info)
        self._set_ui_state(is_busy=False)
        messagebox.showerror("Ошибка", error_info)

# --- Точка входа ---
if __name__ == "__main__":
    # Проверка зависимостей
    missing_packages = []
    try:
        import pandas
    except ImportError:
        missing_packages.append("pandas")

    try:
        import yaml
    except ImportError:
        missing_packages.append("pyyaml")

    try:
        import openpyxl
    except ImportError:
        missing_packages.append("openpyxl")

    try:
        import tabulate
    except ImportError:
        missing_packages.append("tabulate")

    try:
        import lxml
    except ImportError:
        missing_packages.append("lxml")

    # Определяем класс root в зависимости от доступности tkinterdnd2
    if DND_AVAILABLE:
        root_class = TkinterDnD.Tk
    else:
        root_class = Tk

    if missing_packages:
        message = f"Необходима установка библиотек: {', '.join(missing_packages)}\nИспользуйте: pip install {' '.join(missing_packages)}"
        print(message)
        try:
            root = Tk()
            root.withdraw()
            messagebox.showerror("Критическая ошибка", message)
        except Exception:
            pass
        sys.exit(1)

    # Запуск приложения
    root = root_class()
    app = DataConverterGUI(root)
    root.mainloop()
