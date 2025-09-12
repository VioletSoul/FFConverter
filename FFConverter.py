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
from tkinter import (
    Tk, filedialog, StringVar, Text, END, messagebox, Label, Frame, Scrollbar,
    VERTICAL, RIGHT, Y, HORIZONTAL, BOTTOM, X, Spinbox, IntVar
)
from tkinter import ttk
import tkinter.font as tkFont

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

# --- Вспомогательные функции для XML ---
def xml_safe_tag(tag):
    tag = re.sub(r'[^a-zA-Z0-9_\.]', '_', str(tag).strip())
    return tag if re.match(r'^[a-zA-Z_]', tag) else f"f_{tag}"

def xml_safe_text(val):
    return html.escape(str(val), quote=True)

# --- Логика обработки данных (Архитектура "Стратегия") ---

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
        # Новый, более надежный способ
        return pd.read_xml(path, parser='etree')
    except (ValueError, ET.ParseError):
        # Старый способ как запасной вариант для простых структур
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

# --- GUI Класс ---
class DataConverterGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Универсальный конвертер данных")
        self.master.geometry("950x760")
        self.master.configure(bg=BG_MAIN)

        self.file_path = ""
        self.in_format = StringVar()
        self.out_format = StringVar()
        self.status = StringVar(value="Готов к работе.")
        self.data_content = None
        self.n_preview = IntVar(value=20)
        self.pretty_format = ""

        self._build_gui()

    def _build_gui(self):
        heading_font = tkFont.Font(family="Arial", size=18, weight="bold")
        label_font = tkFont.Font(family="Arial", size=12)
        text_font = tkFont.Font(family="Consolas", size=11)

        style = ttk.Style(self.master)
        style.theme_use("clam")
        style.configure("Accent.TButton", background=BTN_BG, foreground=BTN_FG, font=label_font, borderwidth=1, focusthickness=2, relief="flat")
        style.map("Accent.TButton", background=[("active", BTN_HOVER)], foreground=[("active", BTN_FG)])

        Label(self.master, text="Универсальный конвертер данных", font=heading_font, bg=BG_MAIN, fg=TXT_ACCENT, anchor="w").pack(fill="x", pady=(16, 12), padx=19)

        frm = Frame(self.master, bg=BG_SEC, pady=9, padx=14)
        frm.pack(fill="x", padx=19, pady=(0, 13))

        self.btn_file = ttk.Button(frm, text="Выбрать файл", command=self.choose_file, style="Accent.TButton")
        self.btn_file.grid(row=0, column=0, sticky="w", padx=(0,12), pady=4)

        self.in_label = Label(frm, text="Исходный формат: не выбран", font=label_font, bg=BG_SEC, fg=TXT_ACCENT)
        self.in_label.grid(row=0, column=1, padx=8, pady=4, sticky="w")

        Label(frm, text="Конвертировать в:", font=label_font, bg=BG_SEC, fg=TXT_ACCENT).grid(row=1, column=0, pady=9, sticky="w")

        self.format_combo = ttk.Combobox(frm, values=SUPPORTED_FORMATS, textvariable=self.out_format, width=14, font=label_font, state="readonly")
        self.format_combo.grid(row=1, column=1, sticky="w", padx=8)

        self.btn_convert = ttk.Button(frm, text="Конвертировать", command=self.convert, style="Accent.TButton")
        self.btn_convert.grid(row=1, column=2, padx=(21,0), pady=4)

        Label(self.master, textvariable=self.status, fg=TXT_ACCENT, font=label_font, anchor="w", padx=12, bg=BG_MAIN).pack(fill="x", pady=(0,7), padx=10)

        preview_frame = Frame(self.master, bg=BG_MAIN)
        preview_frame.pack(fill="both", expand=True, padx=18, pady=(0,8))

        preview_top = Frame(preview_frame, bg=BG_MAIN)
        preview_top.pack(fill="x")

        self.preview_label = Label(preview_top, text="Просмотр первых 20 строк:", bg=BG_MAIN, font=label_font, anchor="w", fg=TXT_ACCENT)
        self.preview_label.pack(side="left", pady=(3,2))

        self.preview_format_label = Label(preview_top, text="", bg=BG_MAIN, fg="#b5e3ff", font=label_font)
        self.preview_format_label.pack(side="left", padx=(7,0))

        Label(preview_top, text=" Кол-во строк:", bg=BG_MAIN, fg=TXT_ACCENT, font=label_font).pack(side="left")

        self.spin_preview = Spinbox(preview_top, from_=5, to=500, width=5, textvariable=self.n_preview, bg=BG_ALT, fg=TXT_MAIN, font=label_font, relief="flat", command=self.update_preview)
        self.spin_preview.pack(side="left", padx=(3,9), pady=(1,1))
        self.spin_preview.bind("<Return>", lambda e: self.update_preview())

        self.text = Text(preview_frame, width=125, height=35, font=text_font, bg=BG_ALT, relief="ridge", borderwidth=2, fg=TXT_MAIN, insertbackground=TXT_MAIN, wrap="none")
        yscroll = Scrollbar(preview_frame, orient=VERTICAL, command=self.text.yview, bg=BG_ALT, troughcolor=BG_MAIN)
        xscroll = Scrollbar(self.master, orient=HORIZONTAL, command=self.text.xview, bg=BG_ALT, troughcolor=BG_MAIN)
        self.text.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        yscroll.pack(in_=preview_frame, side=RIGHT, fill=Y)
        xscroll.pack(side=BOTTOM, fill=X, padx=18, pady=(0,8))
        self.text.pack(in_=preview_frame, side="left", fill="both", expand=True)

    def _set_ui_state(self, is_busy):
        """Включает/выключает элементы GUI во время операций."""
        state = "disabled" if is_busy else "normal"
        self.btn_file.config(state=state)
        self.btn_convert.config(state=state)
        self.format_combo.config(state="readonly" if not is_busy else "disabled")
        self.spin_preview.config(state=state)

    def update_preview(self):
        self.text.delete(1.0, END)
        try:
            n = max(1, self.n_preview.get())
        except Exception:
            n = 20; self.n_preview.set(n)

        self.preview_label.config(text=f"Просмотр первых {n} строк:")
        self.preview_format_label.config(text=f" [{self.pretty_format}]" if self.pretty_format else "")

        if self.data_content is None: return

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
        path = filedialog.askopenfilename(title="Выберите файл", filetypes=[
            ("Все поддерживаемые", "*.csv *.xlsx *.json *.xml *.yaml *.yml *.ini *.txt *.md *.py *.cpp *.c *.h *.java *.cs *.js *.ts *.go *.rb *.swift *.sh *.bat *.pl *.php *.rs *.scala *.kt *.dart"),
            ("Все файлы", "*.*")])
        if not path: return

        self.file_path = path
        self.status.set(f"Чтение файла: {os.path.basename(path)}...")
        self._set_ui_state(is_busy=True)

        threading.Thread(target=self._load_file_thread, args=(path,), daemon=True).start()

    def _load_file_thread(self, path):
        try:
            fmt = detect_format(path)
            data = read_data(path, fmt)
            self.master.after(0, self._finish_loading, fmt, data, path)
        except Exception as e:
            error_info = f"Ошибка чтения файла: {e}\n\n{traceback.format_exc()}"
            self.master.after(0, self._operation_error, error_info)

    def _finish_loading(self, fmt, data, path):
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
        if not self.file_path or not self.in_format.get():
            messagebox.showerror("Ошибка", "Сначала выберите и загрузите файл!"); return

        target_fmt = self.out_format.get()
        if not target_fmt:
            messagebox.showerror("Ошибка", "Выберите корректный формат для конвертации!"); return

        current_fmt = self.in_format.get()
        if current_fmt == "code" and target_fmt not in ["txt", "md"]:
            messagebox.showerror("Ошибка", "Исходный код можно сохранять только как .txt или .md!"); return

        save_path = filedialog.asksaveasfilename(
            defaultextension=f".{target_fmt}",
            filetypes=[(f"{target_fmt.upper()}", f"*.{target_fmt}"), ("Все файлы", "*.*")])
        if not save_path: return

        self.status.set(f"Конвертация в {target_fmt}...")
        self._set_ui_state(is_busy=True)

        threading.Thread(target=self._save_file_thread, args=(save_path, target_fmt), daemon=True).start()

    def _save_file_thread(self, save_path, target_fmt):
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

            self.master.after(0, self._finish_saving, save_path)
        except Exception as e:
            error_info = f"Ошибка конвертации: {e}\n\n{traceback.format_exc()}"
            self.master.after(0, self._operation_error, error_info)

    def _finish_saving(self, save_path):
        self.status.set(f"Успех! Сохранено в {os.path.basename(save_path)}")
        self.text.insert(END, f"\n\n--- Успешно сохранено в: {save_path} ---\n")
        self._set_ui_state(is_busy=False)
        messagebox.showinfo("Успех", f"Файл успешно сохранен по пути:\n{save_path}")

    def _operation_error(self, error_info):
        self.status.set("Произошла ошибка.")
        self.text.delete(1.0, END)
        self.text.insert(END, error_info)
        self._set_ui_state(is_busy=False)
        messagebox.showerror("Ошибка", error_info)

# --- Точка входа ---
if __name__ == "__main__":
    try:
        import pandas
        import yaml
        import openpyxl
        import tabulate
    except ImportError as err:
        message = f"Необходима установка библиотек: {err.name}\nИспользуйте: pip install pandas pyyaml openpyxl tabulate lxml"
        print(message)
        # Попытка показать ошибку в GUI, если tkinter уже доступен
        try:
            root = Tk()
            root.withdraw()
            messagebox.showerror("Критическая ошибка", message)
        except Exception:
            pass
        sys.exit(1)

    root = Tk()
    app = DataConverterGUI(root)
    root.mainloop()

