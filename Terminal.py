import tkinter as tk
from tkinter import scrolledtext
import shlex

class Emulator:
    def __init__(self, root: tk, vfs_name="Iamdumbconsole"):
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
        self.entry.focus()
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

if __name__ == "__main__":
    root = tk.Tk()
    Emulator(root)
    root.mainloop()