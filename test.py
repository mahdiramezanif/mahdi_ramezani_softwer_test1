import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

APP_TITLE = "To-Do List v2 - With Timestamp"
GREEN = "#2eab5f"
RED = "#e9533d"
BLUE = "#1787e0"
PURPLE = "#7e2bd5"

class TodoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("600x520")
        self.minsize(480, 420)

        # memory-only store
        self.todos = []  # [{"title": str, "done": bool, "ts": str}, ...]
        self.selected_index = None

        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self, padding=(8, 8, 8, 0))
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)

        self.entry = ttk.Entry(top)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.add_btn = tk.Button(top, text="Add Task", bg=GREEN, fg="white",
                                 activebackground=GREEN, relief="flat", padx=14, pady=6,
                                 command=self.add_task)
        self.add_btn.grid(row=0, column=1)

        mid = ttk.Frame(self, padding=8)
        mid.grid(row=1, column=0, sticky="nsew")
        mid.rowconfigure(0, weight=1)
        mid.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(mid, activestyle="none")
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(mid, orient="vertical", command=self.listbox.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.listbox.config(yscrollcommand=scroll.set)

        bottom = ttk.Frame(self, padding=(8, 0, 8, 8))
        bottom.grid(row=2, column=0, sticky="ew")
        for i in range(3):
            bottom.columnconfigure(i, weight=1)

        self.delete_btn = tk.Button(bottom, text="Delete Task", bg=RED, fg="white",
                                    activebackground=RED, relief="flat", padx=10, pady=8,
                                    command=self.delete_task)
        self.done_btn   = tk.Button(bottom, text="Mark Done",  bg=BLUE, fg="white",
                                    activebackground=BLUE, relief="flat", padx=10, pady=8,
                                    command=self.mark_done)
        self.clear_btn  = tk.Button(bottom, text="Clear All",  bg=PURPLE, fg="white",
                                    activebackground=PURPLE, relief="flat", padx=10, pady=8,
                                    command=self.clear_all)

        self.delete_btn.grid(row=0, column=0, sticky="ew", padx=(0,8), pady=(8,0))
        self.done_btn.grid(row=0, column=1, sticky="ew", padx=(0,8), pady=(8,0))
        self.clear_btn.grid(row=0, column=2, sticky="ew", pady=(8,0))

    def _bind_events(self):
        self.entry.bind("<Return>", lambda e: self.add_task())
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Double-Button-1>", lambda e: self.toggle_selected())

    def _on_select(self, _event=None):
        sel = self.listbox.curselection()
        self.selected_index = sel[0] if sel else None

    def _render(self):
        self.listbox.delete(0, tk.END)
        for t in self.todos:
            prefix = "✔ " if t["done"] else ""
            line = f"{prefix}{t['title']} - [{t['ts']}]"
            self.listbox.insert(tk.END, line)

    def add_task(self):
        title = self.entry.get().strip()
        if not title: 
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.todos.append({"title": title, "done": False, "ts": ts})
        self.entry.delete(0, tk.END)
        self._render()

    def mark_done(self):
        if self.selected_index is None:
            return
        self.todos[self.selected_index]["done"] = True
        self._render()

    def toggle_selected(self):
        if self.selected_index is None:
            return
        t = self.todos[self.selected_index]
        t["done"] = not t["done"]
        self._render()

    def delete_task(self):
        if self.selected_index is None:
            return
        del self.todos[self.selected_index]
        self.selected_index = None
        self._render()

    def clear_all(self):
        if not self.todos:
            return
        if messagebox.askyesno("Confirm", "Delete all tasks?"):
            self.todos.clear()
            self.selected_index = None
            self._render()

if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
