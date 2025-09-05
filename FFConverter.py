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
from tkinter import (
    Tk, filedialog, StringVar, Text, END, messagebox, Label, Frame, Scrollbar,
    VERTICAL, RIGHT, Y, HORIZONTAL, BOTTOM, X, Spinbox, IntVar
)
from tkinter import ttk
import tkinter.font as tkFont

SUPPORTED_FORMATS = ["csv", "xlsx", "json", "xml", "yaml", "ini", "txt", "md"]
SOURCE_EXTS = [
    ".py", ".cpp", ".c", ".h", ".java", ".cs", ".js", ".ts", ".go", ".rb", ".swift",
    ".sh", ".bat", ".pl", ".php", ".rs", ".scala", ".kt", ".dart"
]

BG_MAIN = "#232832"
BG_SEC = "#2b3040"
BG_ALT = "#262b36"
TXT_MAIN = "#d3dae3"
TXT_ACCENT = "#59d7ff"
BTN_BG = "#364356"
BTN_FG = "#ffffff"
BTN_HOVER = "#60bbff"

def xml_safe_tag(tag):
    tag = re.sub(r'[^a-zA-Z0-9_\.]', '_', str(tag).strip())
    return tag if re.match(r'^[a-zA-Z_]', tag) else f"f_{tag}"

def xml_safe_text(val):
    return html.escape(str(val), quote=True)

def detect_format(filepath):
    ext = os.path.splitext(filepath)[-1].lower()
    if ext in SOURCE_EXTS:
        return "code"
    if ext == ".csv":
        return "csv"
    if ext == ".xlsx":
        return "xlsx"
    if ext == ".json":
        return "json"
    if ext == ".xml":
        return "xml"
    if ext in [".yaml", ".yml"]:
        return "yaml"
    if ext == ".ini":
        return "ini"
    if ext in [".txt"]:
        return "txt"
    if ext in [".md", ".markdown"]:
        return "md"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            head = f.read(2048)
            if head.strip().startswith("{"):
                json.loads(head)
                return "json"
            if head.strip().startswith("<"):
                ET.fromstring(head)
                return "xml"
            if "version:" in head or "apiVersion:" in head:
                yaml.safe_load(head)
                return "yaml"
            if "[" in head and "]" in head:
                cp = configparser.ConfigParser()
                cp.read_string(head)
                return "ini"
    except Exception:
        pass
    return "txt"

def read_data(filepath, ftype):
    if ftype == "code":
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.readlines()
        return content
    if ftype == "csv":
        return pd.read_csv(filepath)
    if ftype == "xlsx":
        return pd.read_excel(filepath)
    if ftype == "json":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            try:
                return pd.DataFrame([data])
            except Exception:
                return data
        return data
    if ftype == "xml":
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            records = []
            for child in root:
                record = {}
                for element in child:
                    record[element.tag] = element.text
                if record:
                    records.append(record)
            if records:
                return pd.DataFrame(records)
            else:
                return {elem.tag: elem.text for elem in root}
        except Exception as e:
            return str(e)
    if ftype == "yaml":
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            try:
                return pd.DataFrame([data])
            except Exception:
                return data
        return data
    if ftype == "ini":
        cp = configparser.ConfigParser()
        cp.read(filepath, encoding="utf-8")
        data = {section: dict(cp[section]) for section in cp.sections()}
        return pd.DataFrame(data).transpose()
    if ftype == "txt" or ftype == "md":
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return lines
    raise ValueError(f"Неподдерживаемый формат: {ftype}")

def save_data_saveas(df, out_path, out_fmt):
    if out_fmt == "csv":
        df.to_csv(out_path, index=False)
    elif out_fmt == "xlsx":
        df.to_excel(out_path, index=False)
    elif out_fmt == "json":
        df.to_json(out_path, orient="records", force_ascii=False, indent=2)
    elif out_fmt == "xml":
        root = ET.Element("records")
        for _, row in df.iterrows():
            item = ET.SubElement(root, "record")
            for col, val in row.items():
                tag = xml_safe_tag(col)
                sub = ET.SubElement(item, tag)
                sub.text = xml_safe_text(val)
        tree = ET.ElementTree(root)
        tree.write(out_path, encoding="utf-8", xml_declaration=True)
    elif out_fmt == "yaml":
        df_records = df.to_dict(orient="records")
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(df_records, f, allow_unicode=True)
    elif out_fmt == "ini":
        cp = configparser.ConfigParser()
        for idx, row in df.iterrows():
            section = str(idx)
            cp[section] = {str(col): str(row[col]) for col in df.columns}
        with open(out_path, "w", encoding="utf-8") as f:
            cp.write(f)
    elif out_fmt == "md":
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(df.to_markdown(index=False))
    elif out_fmt == "txt":
        with open(out_path, "w", encoding="utf-8") as f:
            for i, row in df.iterrows():
                f.write(" | ".join([str(x) for x in row.values]) + "\n")
    else:
        raise ValueError("Формат не поддерживается!")

def save_code(content, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(content)

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
        self.df = None
        self.n_preview = IntVar(value=20)
        self._build_gui()

    def _build_gui(self):
        heading_font = tkFont.Font(family="Arial", size=18, weight="bold")
        label_font = tkFont.Font(family="Arial", size=12)
        text_font = tkFont.Font(family="Consolas", size=11)
        style = ttk.Style(self.master)
        style.theme_use("clam")
        style.configure(
            "Accent.TButton", background=BTN_BG, foreground=BTN_FG, font=label_font, borderwidth=1, focusthickness=2, relief="flat"
        )
        style.map(
            "Accent.TButton", background=[("active", BTN_HOVER)], foreground=[("active", BTN_FG)]
        )
        Label(self.master, text="Универсальный конвертер данных",
              font=heading_font, bg=BG_MAIN, fg=TXT_ACCENT, anchor="w").pack(fill="x", pady=(16, 12))
        frm = Frame(self.master, bg=BG_SEC, pady=9, padx=14)
        frm.pack(fill="x", padx=19, pady=(0, 13))
        self.btn_file = ttk.Button(frm, text="Выбрать файл", command=self.choose_file, style="Accent.TButton")
        self.btn_file.grid(row=0, column=0, sticky="w", padx=(0,12), pady=4)
        self.in_label = Label(frm, text="Исходный формат: не выбран", font=label_font, bg=BG_SEC, fg=TXT_ACCENT)
        self.in_label.grid(row=0, column=1, padx=8, pady=4, sticky="w")
        Label(frm, text="Конвертировать в:", font=label_font, bg=BG_SEC, fg=TXT_ACCENT).grid(row=1, column=0, pady=9, sticky="w")
        self.format_combo = ttk.Combobox(frm, values=SUPPORTED_FORMATS, textvariable=self.out_format,
                                         width=14, font=label_font, state="readonly")
        self.format_combo.grid(row=1, column=1, sticky="w", padx=8)
        self.btn_convert = ttk.Button(frm, text="Конвертировать", command=self.convert, style="Accent.TButton")
        self.btn_convert.grid(row=1, column=2, padx=(21,0), pady=4)
        Label(self.master, textvariable=self.status, fg=TXT_ACCENT, font=label_font, anchor="w",
              padx=12, bg=BG_MAIN).pack(fill="x", pady=(0,7), padx=10)

        # Предпросмотр
        preview_frame = Frame(self.master, bg=BG_MAIN)
        preview_frame.pack(fill="both", expand=True, padx=18, pady=(0,8))
        preview_top = Frame(preview_frame, bg=BG_MAIN)
        preview_top.pack(fill="x")
        self.preview_label = Label(preview_top, text="Просмотр первых 20 строк:",
                                   bg=BG_MAIN, font=label_font, anchor="w", fg=TXT_ACCENT)
        self.preview_label.pack(side="left", pady=(3,2))
        Label(preview_top, text=" Кол-во строк:", bg=BG_MAIN, fg=TXT_ACCENT, font=label_font).pack(side="left")
        self.spin_preview = Spinbox(preview_top, from_=5, to=500, width=5, textvariable=self.n_preview,
                                    bg=BG_ALT, fg=TXT_MAIN, font=label_font, relief="raised", command=self.update_preview)
        self.spin_preview.pack(side="left", padx=(3,9), pady=(1,1))
        self.spin_preview.bind("<Return>", lambda e: self.update_preview())
        self.spin_preview.bind("<FocusOut>", lambda e: self.update_preview())

        self.text = Text(preview_frame, width=125, height=35, font=text_font,
                         bg=BG_ALT, relief="ridge", borderwidth=2, fg=TXT_MAIN, insertbackground=TXT_MAIN)
        self.text.pack(side="left", fill="both", expand=True, padx=(0,4))
        yscroll = Scrollbar(preview_frame, orient=VERTICAL, command=self.text.yview, bg=BG_ALT, troughcolor=BG_MAIN)
        yscroll.pack(side=RIGHT, fill=Y)
        self.text.config(yscrollcommand=yscroll.set)
        xscroll = Scrollbar(preview_frame, orient=HORIZONTAL, command=self.text.xview, bg=BG_ALT, troughcolor=BG_MAIN)
        xscroll.pack(side=BOTTOM, fill=X)
        self.text.config(xscrollcommand=xscroll.set, wrap="none")

    def update_preview(self):
        self.text.delete(1.0, END)
        n = self.n_preview.get()
        try:
            n = max(1, int(n))
        except Exception:
            n = 20
            self.n_preview.set(n)
        fmt = self.in_format.get()
        label_str = f"Просмотр первых {n} строк:"
        self.preview_label.config(text=label_str)
        try:
            if self.df is None:
                return
            if fmt == "code":
                preview = "".join(self.df[:n])
            elif isinstance(self.df, pd.DataFrame):
                preview = self.df.head(n).to_markdown(index=False)
            elif isinstance(self.df, list):
                preview = "".join(self.df[:n])
            elif isinstance(self.df, (dict,)):
                preview = json.dumps(self.df, ensure_ascii=False, indent=3)
            else:
                preview = str(self.df)[:3000]
            self.text.insert(END, label_str + "\n" + preview)
        except Exception as e:
            self.text.insert(END, f"Ошибка обновления предпросмотра: {e}\n\n{traceback.format_exc()}")

    def choose_file(self):
        path = filedialog.askopenfilename(title="Выберите файл", filetypes=[
            ("Все поддерживаемые", "*.csv *.xlsx *.json *.xml *.yaml *.yml *.ini *.txt *.md *.py *.cpp *.c *.h *.java *.cs *.js *.ts *.go *.rb *.swift *.sh *.bat *.pl *.php *.rs *.scala *.kt *.dart"),
            ("Все файлы", "*.*")
        ])
        if not path:
            return
        self.file_path = path
        fmt = detect_format(self.file_path)
        self.in_format.set(fmt)
        self.in_label.config(text=f"Исходный формат: {fmt.upper()}")
        self.status.set(f"Выбран файл: {os.path.basename(path)} ({fmt})")
        # Ограничить форматы назначения для исходных файлов только txt и md
        if fmt == "code":
            self.format_combo["values"] = ["txt", "md"]
        else:
            self.format_combo["values"] = SUPPORTED_FORMATS
        self.out_format.set('')
        try:
            self.df = read_data(self.file_path, fmt)
        except Exception as e:
            self.df = None
            self.text.delete(1.0, END)
            self.text.insert(END, f"Ошибка чтения файла: {e}\n\n{traceback.format_exc()}")
            return
        self.update_preview()

    def convert(self):
        if not self.file_path or not self.in_format.get():
            messagebox.showerror("Ошибка", "Сначала выберите файл!")
            return
        target_fmt = self.out_format.get()
        fmt = self.in_format.get()
        if fmt == "code" and target_fmt not in ["txt", "md"]:
            messagebox.showerror("Ошибка", "Исходный код можно сохранять только как .txt или .md!")
            return
        if not target_fmt or (target_fmt not in SUPPORTED_FORMATS and target_fmt not in ["txt", "md"]):
            messagebox.showerror("Ошибка", "Выберите корректный формат!")
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=f".{target_fmt}",
            filetypes=[(f"{target_fmt.upper()}", f"*.{target_fmt}"), ("Все файлы", "*.*")]
        )
        if not save_path:
            return
        try:
            if fmt == "code":
                save_code(self.df, save_path)
                self.status.set(f"Исходник сохранён как {save_path}")
                self.text.insert(END, f"\n\nСохранено в: {save_path}\n")
                return
            if not isinstance(self.df, pd.DataFrame):
                if isinstance(self.df, dict):
                    df = pd.DataFrame([self.df])
                elif isinstance(self.df, list):
                    df = pd.DataFrame(self.df)
                else:
                    messagebox.showerror("Ошибка", "Не удалось привести структуру данных к табличному виду.")
                    return
            else:
                df = self.df
            save_data_saveas(df, save_path, target_fmt)
            self.status.set(f"Успех! Сохранено в {save_path}")
            self.text.insert(END, f"\n\nСохранено в: {save_path}\n")
        except Exception as e:
            self.status.set("Ошибка при конвертации.")
            self.text.insert(END, f"\n\nОшибка: {e}\n\n{traceback.format_exc()}")
            messagebox.showerror("Ошибка", f"Ошибка при конвертации: {e}\n\n{traceback.format_exc()}")

if __name__ == "__main__":
    try:
        import pandas
        import yaml
        import openpyxl
        import tabulate
    except ImportError as err:
        print(f"Необходима установка библиотек: {err.name}\nИспользуйте: pip install pandas pyyaml openpyxl tabulate")
        sys.exit(1)
    root = Tk()
    app = DataConverterGUI(root)
    root.mainloop()
