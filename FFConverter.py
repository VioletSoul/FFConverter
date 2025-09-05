import traceback
import os
import sys
import json
import csv
import yaml
import configparser
import pandas as pd
import xml.etree.ElementTree as ET
from tkinter import (
    Tk, filedialog, ttk, StringVar, Button, Text, END, messagebox, Label, Frame
)

SUPPORTED_FORMATS = ["csv", "xlsx", "json", "xml", "yaml", "ini", "txt", "md"]

def detect_format(filepath):
    ext = os.path.splitext(filepath)[-1].lower()
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
    # Fallback: try content
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
            if "[" in head and "]" in head:  # possible INI
                cp = configparser.ConfigParser()
                cp.read_string(head)
                return "ini"
    except Exception:
        pass
    return "txt"

def read_data(filepath, ftype):
    if ftype == "csv":
        return pd.read_csv(filepath)
    if ftype == "xlsx":
        return pd.read_excel(filepath)
    if ftype == "json":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Try to convert dict/list of dicts to dataframe if possible
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict):
            try:  # Try to flatten one-level dict
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
            else:  # Single-level XML
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
        return pd.DataFrame({"text": [l.strip() for l in lines if l.strip()]})
    raise ValueError(f"Неподдерживаемый формат: {ftype}")

def save_data_saveas(df, out_path, out_fmt):
    if out_fmt == "csv":
        df.to_csv(out_path, index=False)
    elif out_fmt == "xlsx":
        df.to_excel(out_path, index=False)
    elif out_fmt == "json":
        df.to_json(out_path, orient="records", force_ascii=False, indent=2)
    elif out_fmt == "xml":
        # Write as a records-root xml
        root = ET.Element("records")
        for _, row in df.iterrows():
            item = ET.SubElement(root, "record")
            for col, val in row.items():
                sub = ET.SubElement(item, str(col))
                sub.text = str(val)
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
        # Markdown table
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(df.to_markdown(index=False))
    elif out_fmt == "txt":
        with open(out_path, "w", encoding="utf-8") as f:
            for i, row in df.iterrows():
                f.write(" | ".join([str(x) for x in row.values]) + "\n")
    else:
        raise ValueError("Формат не поддерживается!")

class DataConverterGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Универсальный конвертер данных")
        self.file_path = ""
        self.in_format = StringVar()
        self.out_format = StringVar()
        self.status = StringVar(value="Готов к работе.")
        self.df = None
        self.log_lines = []
        self._build_gui()

    def _build_gui(self):
        frm = Frame(self.master)
        frm.pack(padx=10, pady=10)

        Button(frm, text="Выбрать файл", command=self.choose_file).grid(row=0, column=0, sticky="we")
        self.in_label = Label(frm, text="Исходный формат: не выбран")
        self.in_label.grid(row=0, column=1, padx=10)
        Label(frm, text="Конвертировать в:").grid(row=1, column=0, pady=8, sticky="we")
        self.format_combo = ttk.Combobox(frm, values=SUPPORTED_FORMATS, textvariable=self.out_format, width=15)
        self.format_combo.grid(row=1, column=1, sticky="w")
        Button(frm, text="Конвертировать", command=self.convert).grid(row=2, column=0, columnspan=2, pady=10, sticky="we")
        Label(frm, textvariable=self.status, fg="grey").grid(row=3, column=0, columnspan=2, pady=4, sticky="w")
        Label(frm, text="Результат / ошибки:").grid(row=4, column=0, columnspan=2, sticky="w")
        self.text = Text(frm, width=70, height=12, wrap="word")
        self.text.grid(row=5, column=0, columnspan=2, pady=2)

    def choose_file(self):
        path = filedialog.askopenfilename(title="Выберите файл", filetypes=[
            ("Все поддерживаемые", "*.csv *.xlsx *.json *.xml *.yaml *.yml *.ini *.txt *.md"),
            ("Все файлы", "*.*")
        ])
        if not path:
            return
        self.file_path = path
        fmt = detect_format(self.file_path)
        self.in_format.set(fmt)
        self.in_label.config(text=f"Исходный формат: {fmt.upper()}")
        self.status.set(f"Выбран файл: {os.path.basename(path)} ({fmt})")
        self.out_format.set('')
        self.text.delete(1.0, END)
        try:
            self.df = read_data(self.file_path, fmt)
            if isinstance(self.df, pd.DataFrame):
                preview = self.df.head(10).to_markdown(index=False)
            else:
                preview = str(self.df)[:1500]
            self.text.insert(END, "Просмотр первых строк:\n" + preview)
        except Exception as e:
            self.text.insert(END, f"Ошибка чтения файла: {e}")

    def convert(self):
        if not self.file_path or not self.in_format.get():
            messagebox.showerror("Ошибка", "Сначала выберите файл!")
            return
        target_fmt = self.out_format.get()
        if not target_fmt or target_fmt not in SUPPORTED_FORMATS:
            messagebox.showerror("Ошибка", "Выберите корректный формат!")
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=f".{target_fmt}",
            filetypes=[(f"{target_fmt.upper()}", f"*.{target_fmt}"), ("Все файлы", "*.*")]
        )
        if not save_path:
            return
        try:
            if not isinstance(self.df, pd.DataFrame):
                # Попытаться привести к DataFrame
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
            self.text.insert(END, f"\n\nОшибка: {e}\n")
            messagebox.showerror("Ошибка", f"Ошибка при конвертации: {e}")

if __name__ == "__main__":
    # Проверка наличия обязательных библиотек
    try:
        import pandas
        import yaml
        import openpyxl
    except ImportError as err:
        print(f"Необходима установка библиотек: {err.name}\nИспользуйте: pip install pandas pyyaml openpyxl")
        sys.exit(1)
    root = Tk()
    app = DataConverterGUI(root)
    root.mainloop()
