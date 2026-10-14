import tkinter as tk
from tkinter import scrolledtext
import argparse
import sys
import xml.etree.ElementTree as ET
import tkinter as tk
import shlex

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--vfs-path")
    p.add_argument("--startup-script")
    p.add_argument("--config")
    return p.parse_args()

def load_config(path):
    """Читает XML. При ошибке бросает исключение с текстом."""
    root = ET.parse(path).getroot()
    result = {}
    for tag in ("vfs_path", "startup_script"):
        node = root.find(tag)
        if node is not None and node.text:
            result[tag] = node.text.strip()
    return result

class Emulator:
    def __init__(self, root: tk, params, vfs_name="home"):
        self.root = root
        self.vfs_name = vfs_name
        self.root.title(f"VFS: {vfs_name}")
        self.root.geometry("800x600")
        self.output = scrolledtext.ScrolledText(root, state='disabled', wrap='word')
        self.output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        input_frame = tk.Frame(root)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.prompt_label = tk.Label(input_frame, text=f"{vfs_name}$ ")
        self.prompt_label.pack(side=tk.LEFT)
        self.entry = tk.Entry(input_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.process_command)
        self.params = params

        self.print_output("=== Параметры эмулятора ===")
        for k, v in params.items():
            self.print_output(f"  {k} = {v}")
        self.print_output("")

        self.run_startup()
    def process_command(self, event=None):
        cmd_line = self.entry.get().strip()
        if not cmd_line:
            return
        self.entry.delete(0, tk.END)
        self.print_output(f"{self.vfs_name}$ {cmd_line}")

        try:
            args = shlex.split(cmd_line)
        except ValueError as e:
            self.print_output(f"Ошибка разбора: {e}")
            return

        if not args:
            return

        cmd = args[0]
        cmd_args = args[1:]

        if cmd == "exit":
            self.root.quit()
        elif cmd == "ls":
            self.print_output(f"ls: команда-заглушка. Аргументы: {cmd_args}")
        elif cmd == "cd":
            self.print_output(f"cd: команда-заглушка. Аргументы: {cmd_args}")
        else:
            self.print_output(f"Ошибка: неизвестная команда '{cmd}'")
    def print_output(self, text):
        self.output.config(state='normal')
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state='disabled')
    def run_startup(self):
        path = self.params.get("startup_script")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            self.print_output(f"Ошибка: стартовый скрипт не найден: {path}")
            return

        self.print_output(f"--- Выполнение скрипта: {path} ---")
        for i, raw in enumerate(lines, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            self.print_output(f"{self.vfs_name}$ {line}")
            try:
                self.execute_from_script(line)
            except Exception as e:
                self.print_output(f"Ошибка в строке {i}: {e}")
                break
        self.print_output("--- Скрипт завершён ---\n")

    def execute_from_script(self, line):
        try:
            args = shlex.split(line)
        except ValueError as e:
            self.print_output(f"Ошибка разбора: {e}")
            return
        if not args:
            return
        cmd, rest = args[0], args[1:]
        if cmd == "exit":
            return
        elif cmd == "ls":
            self.print_output(f"ls: команда-заглушка. Аргументы: {rest}")
        elif cmd == "cd":
            self.print_output(f"cd: команда-заглушка. Аргументы: {rest}")
        else:
            self.print_output(f"Ошибка: неизвестная команда '{cmd}'")



def main():
    args = parse_args()

    cfg = {}
    if args.config:
        try:
            cfg = load_config(args.config)
        except FileNotFoundError:
            print(f"Ошибка: конфиг не найден: {args.config}", file=sys.stderr)
            sys.exit(1)
        except ET.ParseError as e:
            print(f"Ошибка: некорректный XML в {args.config}: {e}", file=sys.stderr)
            sys.exit(1)

    # Приоритет: CLI важнее конфига
    params = {
        "vfs_path": args.vfs_path or cfg.get("vfs_path"),
        "startup_script": args.startup_script or cfg.get("startup_script"),
        "config": args.config,
    }

    root = tk.Tk()
    Emulator(root, params)
    root.mainloop()
    
if __name__ == "__main__":
    main()