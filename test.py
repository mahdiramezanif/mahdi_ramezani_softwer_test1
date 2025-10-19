import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import json
import os
import uuid

# -----------------------------
# Constants & Config
# -----------------------------
APP_TITLE = "🚀 Advanced Task Manager"
DATA_FILE = "tasks.json"

GREEN = "#2eab5f"
RED = "#e9533d"
BLUE = "#1787e0"
PURPLE = "#7e2bd5"
DARK_BG = "#2c3e50"
LIGHT_BG = "#f8f9fa"

CATEGORIES = ["General", "Home", "Work", "Study", "Shopping"]
PRIORITIES = ["Low", "Medium", "High", "Urgent"]

# -----------------------------
# Priority "grey circle" levels (lighter -> darker)
# -----------------------------
PRIORITY_CIRCLE = {
    "Low": "○",     # lightest
    "Medium": "◔",
    "High": "◑",
    "Urgent": "●"   # darkest
}


class AdvancedTodoApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("860x700")
        self.root.minsize(820, 620)
        self.root.configure(bg=LIGHT_BG)

        # Main data source (never mutated destructively by filters)
        # {"id": str, "text": str, "done": bool, "created": str, "priority": str, "category": str}
        self.tasks = []

        # UI / filter vars
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All")            # All | Pending | Completed
        self.category_filter_var = tk.StringVar(value="All")   # All | <Cat>
        self.priority_var = tk.StringVar(value="Medium")       # add/edit
        self.category_var = tk.StringVar(value=CATEGORIES[0])  # add/edit
        self.task_text_var = tk.StringVar()

        self.setup_styles()
        self.setup_ui()
        self.load_tasks()
        self.render()
        self.update_stats()

    # -----------------------------
    # Styles
    # -----------------------------
    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except tk.TclError:
            style.theme_use("clam")
        style.configure("Header.TFrame", background=DARK_BG)
        style.configure("Light.TFrame", background=LIGHT_BG)
        style.configure("TButton", padding=6)
        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    # -----------------------------
    # Phase 2: Header & Search
    # -----------------------------
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg=DARK_BG, height=100)
        header_frame.pack(side='top', fill='x', padx=15, pady=15)
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="🚀 Advanced Task Manager",
                 font=('Arial', 18, 'bold'), bg=DARK_BG, fg='white').pack(pady=20)

        # Search & Filters
        search_frame = tk.Frame(self.root, bg=LIGHT_BG)
        search_frame.pack(side='top', fill='x', padx=20, pady=(0, 10))

        tk.Label(search_frame, text="🔍 Search:",
                 font=('Arial', 10, 'bold'), bg=LIGHT_BG).grid(row=0, column=0, sticky='w')

        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                     font=('Arial', 10), width=25, bd=1, relief='solid')
        self.search_entry.grid(row=0, column=1, padx=5)
        self.search_entry.bind('<KeyRelease>', self.filter_tasks)

        tk.Label(search_frame, text="Status:",
                 font=('Arial', 10, 'bold'), bg=LIGHT_BG).grid(row=0, column=2, padx=(20, 5))
        status_combo = ttk.Combobox(search_frame, textvariable=self.filter_var,
                                    values=["All", "Pending", "Completed"], state="readonly", width=12)
        status_combo.grid(row=0, column=3, padx=5)
        status_combo.bind('<<ComboboxSelected>>', self.filter_tasks)

        tk.Label(search_frame, text="Category:",
                 font=('Arial', 10, 'bold'), bg=LIGHT_BG).grid(row=0, column=4, padx=(20, 5))
        category_combo = ttk.Combobox(search_frame, textvariable=self.category_filter_var,
                                      values=["All"] + CATEGORIES, state="readonly", width=12)
        category_combo.grid(row=0, column=5, padx=5)
        category_combo.bind('<<ComboboxSelected>>', self.filter_tasks)

        # Add options
        options_frame = tk.Frame(self.root, bg=LIGHT_BG)
        options_frame.pack(side='top', fill='x', padx=20, pady=(0, 10))

        tk.Label(options_frame, text="Task:", font=('Arial', 10, 'bold'),
                 bg=LIGHT_BG).pack(side='left', padx=(0, 6))
        task_entry = tk.Entry(options_frame, textvariable=self.task_text_var,
                              font=('Arial', 10), width=32, bd=1, relief='solid')
        task_entry.pack(side='left', padx=(0, 12))
        task_entry.bind("<Return>", lambda e: self.add_task())

        tk.Label(options_frame, text="Category:", font=('Arial', 10),
                 bg=LIGHT_BG).pack(side='left', padx=(0, 6))
        cat_combo = ttk.Combobox(options_frame, textvariable=self.category_var,
                                 values=CATEGORIES, state="readonly", width=12)
        cat_combo.pack(side='left', padx=(0, 12))

        tk.Label(options_frame, text="Priority:", font=('Arial', 10),
                 bg=LIGHT_BG).pack(side='left', padx=(0, 10))
        priority_combo = ttk.Combobox(options_frame, textvariable=self.priority_var,
                                      values=PRIORITIES, state="readonly", width=10)
        priority_combo.pack(side='left')

        add_btn = tk.Button(options_frame, text="Add Task", bg=GREEN, fg="white",
                            activebackground=GREEN, relief="flat", padx=12, pady=6,
                            command=self.add_task)
        add_btn.pack(side='left', padx=(12, 0))

        # -----------------------------
        # Phase 4: Treeview
        # -----------------------------
        list_frame = tk.Frame(self.root, bg=LIGHT_BG)
        list_frame.pack(side='top', fill='both', expand=True, padx=20, pady=(0, 0))

        self.tree = ttk.Treeview(
            list_frame,
            columns=('Status', 'Priority', 'Category', 'Task', 'Time'),
            show='headings', height=15, selectmode="extended"
        )
        self.tree.heading('Status', text='📊 Status')
        self.tree.heading('Priority', text='🎯 Priority')
        self.tree.heading('Category', text='📁 Category')
        self.tree.heading('Task', text='📝 Task')
        self.tree.heading('Time', text='⏰ Created')

        self.tree.column('Status', width=90, anchor='center')
        self.tree.column('Priority', width=90, anchor='center')
        self.tree.column('Category', width=110, anchor='center')
        self.tree.column('Task', width=420, anchor='w')
        self.tree.column('Time', width=150, anchor='center')

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind("<Double-1>", self.on_double_click_toggle)
        self.tree.bind("<Button-3>", self.open_context_menu)

        # Bottom actions (anchored so it never gets cut off)
        bottom = tk.Frame(self.root, bg=LIGHT_BG, height=64)
        bottom.pack(side='bottom', fill='x', padx=20, pady=12)
        bottom.pack_propagate(False)

        btns = tk.Frame(bottom, bg=LIGHT_BG)
        btns.pack(side='left')

        tk.Button(btns, text="Mark Done", bg=BLUE, fg="white",
                  activebackground=BLUE, relief="flat", padx=10, pady=8,
                  command=self.mark_done).pack(side='left', padx=6)
        tk.Button(btns, text="Edit Task", bg="#6c5ce7", fg="white",
                  activebackground="#6c5ce7", relief="flat", padx=10, pady=8,
                  command=self.edit_task).pack(side='left', padx=6)
        tk.Button(btns, text="Delete", bg=RED, fg="white",
                  activebackground=RED, relief="flat", padx=10, pady=8,
                  command=self.delete_selected).pack(side='left', padx=6)
        tk.Button(btns, text="Clear All", bg=PURPLE, fg="white",
                  activebackground=PURPLE, relief="flat", padx=10, pady=8,
                  command=self.clear_all).pack(side='left', padx=6)
        tk.Button(btns, text="Show Stats", bg="#0984e3", fg="white",
                  activebackground="#0984e3", relief="flat", padx=10, pady=8,
                  command=self.show_stats).pack(side='left', padx=6)
        tk.Button(btns, text="Save", bg=GREEN, fg="white",
                  activebackground=GREEN, relief="flat", padx=10, pady=8,
                  command=self.save_tasks).pack(side='left', padx=6)

        self.stats_label = tk.Label(bottom, text="", font=("Arial", 10, "bold"),
                                    bg=LIGHT_BG, fg="#2d3436")
        self.stats_label.pack(side='right')

    # -----------------------------
    # Rendering & Helpers
    # -----------------------------
    def values_from_task(self, t: dict):
        status = "✅" if t.get("done") else "⏰"
        # Use grey-circle shades for priority (lighter -> darker)
        priority_icon = PRIORITY_CIRCLE.get(t.get("priority", "Medium"), PRIORITY_CIRCLE["Medium"])
        return (status, priority_icon, t.get("category", "General"),
                t.get("text", ""), t.get("created", ""))

    def render(self, filtered_list=None):
        self.tree.delete(*self.tree.get_children())
        rows = filtered_list if filtered_list is not None else self.tasks
        for t in rows:
            self.tree.insert('', 'end', iid=t["id"], values=self.values_from_task(t))

    def get_selected_task_ids(self):
        return list(self.tree.selection())

    def find_task_by_id(self, tid):
        for t in self.tasks:
            if t["id"] == tid:
                return t
        return None

    # -----------------------------
    # CRUD
    # -----------------------------
    def add_task(self):
        text = self.task_text_var.get().strip()
        if not text:
            return
        created = datetime.now().strftime("%Y-%m-%d %H:%M")
        task = {
            "id": str(uuid.uuid4()),
            "text": text,
            "done": False,
            "created": created,
            "priority": self.priority_var.get(),
            "category": self.category_var.get()
        }
        self.tasks.append(task)
        self.task_text_var.set("")
        self.apply_filters_and_render()
        self.update_stats()

    def edit_task(self):
        sel = self.get_selected_task_ids()
        if not sel:
            messagebox.showinfo("Edit Task", "Please select a task to edit.")
            return
        if len(sel) > 1:
            messagebox.showinfo("Edit Task", "Please select only one task to edit.")
            return
        tid = sel[0]
        task = self.find_task_by_id(tid)
        if not task:
            return

        edit = tk.Toplevel(self.root)
        edit.title("Edit Task")
        edit.grab_set()
        edit.resizable(False, False)
        edit.configure(bg=LIGHT_BG)
        pad = {'padx': 10, 'pady': 6}

        tk.Label(edit, text="Task:", bg=LIGHT_BG).grid(row=0, column=0, sticky='e', **pad)
        text_var = tk.StringVar(value=task["text"])
        tk.Entry(edit, textvariable=text_var, width=44).grid(row=0, column=1, **pad)

        tk.Label(edit, text="Category:", bg=LIGHT_BG).grid(row=1, column=0, sticky='e', **pad)
        cat_var = tk.StringVar(value=task["category"])
        ttk.Combobox(edit, textvariable=cat_var, values=CATEGORIES,
                     state="readonly", width=18).grid(row=1, column=1, sticky='w', **pad)

        tk.Label(edit, text="Priority:", bg=LIGHT_BG).grid(row=2, column=0, sticky='e', **pad)
        pr_var = tk.StringVar(value=task["priority"])
        ttk.Combobox(edit, textvariable=pr_var, values=PRIORITIES,
                     state="readonly", width=18).grid(row=2, column=1, sticky='w', **pad)

        done_var = tk.BooleanVar(value=task["done"])
        tk.Checkbutton(edit, text="Completed", variable=done_var,
                       bg=LIGHT_BG).grid(row=3, column=1, sticky='w', **pad)

        def save_edit():
            task["text"] = text_var.get().strip()
            task["category"] = cat_var.get()
            task["priority"] = pr_var.get()
            task["done"] = bool(done_var.get())
            self.apply_filters_and_render()
            self.update_stats()
            edit.destroy()

        tk.Button(edit, text="Save", bg=GREEN, fg="white",
                  activebackground=GREEN, relief="flat", padx=10,
                  command=save_edit).grid(row=4, column=1, sticky='e', **pad)

    def delete_selected(self):
        sel = self.get_selected_task_ids()
        if not sel:
            return
        if not messagebox.askyesno("Confirm", f"Delete {len(sel)} selected task(s)?"):
            return
        self.tasks = [t for t in self.tasks if t["id"] not in sel]
        self.apply_filters_and_render()
        self.update_stats()

    def clear_all(self):
        if not self.tasks:
            return
        if messagebox.askyesno("Confirm", "Delete all tasks?"):
            self.tasks.clear()
            self.render()
            self.update_stats()

    def mark_done(self):
        sel = self.get_selected_task_ids()
        if not sel:
            return
        for tid in sel:
            t = self.find_task_by_id(tid)
            if t:
                t["done"] = True
        self.apply_filters_and_render()
        self.update_stats()

    def on_double_click_toggle(self, _event=None):
        item = self.tree.identify_row(self.root.winfo_pointery())
        if not item:
            return
        t = self.find_task_by_id(item)
        if not t:
            return
        t["done"] = not t["done"]
        self.apply_filters_and_render()
        self.update_stats()

    def open_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item and item not in self.tree.selection():
            self.tree.selection_set(item)
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Mark Done", command=self.mark_done)
        menu.add_command(label="Edit", command=self.edit_task)
        menu.add_separator()
        menu.add_command(label="Delete", command=self.delete_selected)
        menu.tk_popup(event.x_root, event.y_root)

    # -----------------------------
    # Filters & Search (non-destructive)
    # -----------------------------
    def filter_tasks(self, event=None):
        self.apply_filters_and_render()

    def apply_filters_and_render(self):
        search_text = (self.search_var.get() or "").lower()
        status_filter = self.filter_var.get()            # All | Pending | Completed
        category_filter = self.category_filter_var.get() # All | <Cat>

        filtered = []
        for t in self.tasks:
            if search_text and search_text not in t["text"].lower():
                continue
            status = "Completed" if t.get("done") else "Pending"
            if status_filter != "All" and status_filter != status:
                continue
            if category_filter != "All" and t.get("category", "General") != category_filter:
                continue
            filtered.append(t)

        self.render(filtered_list=filtered if (search_text or status_filter != "All" or category_filter != "All")
                    else None)

    # -----------------------------
    # Stats & Persistence
    # -----------------------------
    def show_stats(self):
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.get('done', False))
        pending = total - completed

        category_stats = {}
        for t in self.tasks:
            cat = t.get('category', 'General')
            category_stats[cat] = category_stats.get(cat, 0) + 1

        stats_text = f"📊 Statistics:\n"
        stats_text += f"✅ Completed: {completed}\n"
        stats_text += f"⏰ Pending: {pending}\n"
        stats_text += f"📈 Total: {total}\n"
        stats_text += ("📁 Categories: " + ", ".join([f"{k}({v})" for k, v in category_stats.items()])) if category_stats else "📁 Categories: -"

        messagebox.showinfo("Detailed Statistics", stats_text)

    def save_tasks(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Saved", "Tasks saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save tasks: {e}")

    def load_tasks(self):
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            normed = []
            for t in data:
                t.setdefault("id", str(uuid.uuid4()))
                t.setdefault("text", "")
                t.setdefault("done", False)
                t.setdefault("created", datetime.now().strftime("%Y-%m-%d %H:%M"))
                t.setdefault("priority", "Medium")
                t.setdefault("category", "General")
                normed.append(t)
            self.tasks = normed
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks: {e}")

    def update_stats(self):
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.get('done', False))
        pending = total - completed
        self.stats_label.config(text=f"📊 Tasks: {completed} Completed | {pending} Pending | {total} Total")


if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedTodoApp(root)
    root.mainloop()
