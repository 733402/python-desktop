import json
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ModuleNotFoundError:  # pragma: no cover - depends on system packages
    tk = None
    ttk = None
    messagebox = None


DATA_FILE = Path(__file__).with_name("data.json")
MAX_SEARCH_HISTORY = 50
MAX_CALC_EXPRESSION_LENGTH = 100


class DataStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = {
            "users": ["Admin"],
            "active_user": "Admin",
            "notes": "",
            "files": {},
            "search_history": [],
        }
        self.load()

    def load(self):
        if not self.path.exists():
            self.save()
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                users = loaded.get("users")
                if isinstance(users, list):
                    valid_users = [u for u in users if isinstance(u, str) and u]
                    if valid_users:
                        self.data["users"] = valid_users

                active_user = loaded.get("active_user")
                if isinstance(active_user, str) and active_user in self.data["users"]:
                    self.data["active_user"] = active_user
                else:
                    self.data["active_user"] = self.data["users"][0]

                notes = loaded.get("notes")
                if isinstance(notes, str):
                    self.data["notes"] = notes

                files = loaded.get("files")
                if isinstance(files, dict):
                    self.data["files"] = {
                        name: content
                        for name, content in files.items()
                        if isinstance(name, str) and isinstance(content, str)
                    }

                search_history = loaded.get("search_history")
                if isinstance(search_history, list):
                    valid_searches = [q for q in search_history if isinstance(q, str)]
                    self.data["search_history"] = valid_searches[-MAX_SEARCH_HISTORY:]
        except (json.JSONDecodeError, OSError):
            self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")


class DesktopApp:
    def __init__(self):
        if tk is None:
            raise RuntimeError(
                "tkinter is not available. Install Tk for your platform (for example, python3-tk on Debian/Ubuntu)."
            )
        self.store = DataStore(DATA_FILE)
        self.root = tk.Tk()
        self.root.title("PyWindows Desktop")
        self.root.geometry("1000x650")
        self.root.configure(bg="#0a3d91")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.status_var = tk.StringVar(value="Ready")
        self.clock_var = tk.StringVar(value="")
        self._build_layout()
        self._tick_clock()

    def _build_layout(self):
        title_bar = tk.Frame(self.root, bg="#0b2f6b", height=44)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        tk.Label(
            title_bar,
            text="PyWindows",
            font=("Segoe UI", 15, "bold"),
            bg="#0b2f6b",
            fg="white",
        ).pack(side="left", padx=14)

        desktop_area = tk.Frame(self.root, bg="#0a3d91")
        desktop_area.pack(fill="both", expand=True, padx=16, pady=16)

        launchers = [
            ("🧮\nCalculator", self.open_calculator),
            ("📝\nNotebook", self.open_notebook),
            ("📁\nFiles", self.open_files),
            ("🌐\nWeb Search", self.open_web_search),
            ("👤\nUsers", self.open_users),
        ]

        for i, (name, command) in enumerate(launchers):
            btn = tk.Button(
                desktop_area,
                text=name,
                command=command,
                width=14,
                height=4,
                relief="raised",
                bg="#f4f7ff",
                activebackground="#d7e6ff",
                font=("Segoe UI", 10),
            )
            btn.grid(row=i, column=0, padx=8, pady=6, sticky="w")

        taskbar = tk.Frame(self.root, bg="#121212", height=38)
        taskbar.pack(fill="x", side="bottom")
        taskbar.pack_propagate(False)

        self.start_button = tk.Button(
            taskbar,
            text="⊞ Start",
            command=self.open_start_menu,
            bg="#1e1e1e",
            fg="white",
            bd=0,
            activebackground="#313131",
            activeforeground="white",
            padx=10,
            pady=5,
        )
        self.start_button.pack(side="left", padx=(6, 2), pady=3)

        self.user_var = tk.StringVar(
            value=f"User: {self.store.data.get('active_user', 'Admin')}"
        )
        user_label = tk.Label(
            taskbar,
            textvariable=self.user_var,
            fg="white",
            bg="#121212",
            padx=10,
        )
        user_label.pack(side="left", padx=(10, 0))
        self.user_label = user_label

        clock = tk.Label(
            taskbar,
            textvariable=self.clock_var,
            fg="#e3e3e3",
            bg="#121212",
            padx=10,
        )
        clock.pack(side="right")

        status = tk.Label(
            taskbar,
            textvariable=self.status_var,
            fg="#e3e3e3",
            bg="#121212",
            padx=10,
        )
        status.pack(side="right", padx=(0, 6))

    def update_status(self, message: str):
        self.status_var.set(message)

    def _tick_clock(self):
        self.clock_var.set(datetime.now().strftime("%H:%M:%S  %d-%b-%Y"))
        self.root.after(1000, self._tick_clock)

    def open_start_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Calculator", command=self.open_calculator)
        menu.add_command(label="Notebook", command=self.open_notebook)
        menu.add_command(label="Files", command=self.open_files)
        menu.add_command(label="Web Search", command=self.open_web_search)
        menu.add_command(label="Users", command=self.open_users)
        menu.add_separator()
        menu.add_command(label="Exit", command=self.on_close)
        x = self.start_button.winfo_rootx()
        y = self.start_button.winfo_rooty() - 210
        menu.tk_popup(x, y)
        menu.grab_release()

    def open_calculator(self):
        window = tk.Toplevel(self.root)
        window.title("Calculator")
        window.geometry("320x420")

        expression = tk.StringVar()
        tk.Entry(window, textvariable=expression, font=("Segoe UI", 16), justify="right").pack(fill="x", padx=10, pady=10)

        def press(value):
            expression.set(expression.get() + value)

        def clear():
            expression.set("")

        def evaluate():
            expr = expression.get().strip()
            if not expr:
                return
            if len(expr) > MAX_CALC_EXPRESSION_LENGTH:
                messagebox.showerror("Error", "Expression too long")
                return
            allowed = set("0123456789+-*/.() ")
            if any(ch not in allowed for ch in expr):
                messagebox.showerror("Error", "Invalid expression")
                return
            if "**" in expr or "//" in expr:
                messagebox.showerror("Error", "Invalid expression")
                return
            try:
                result = eval(expr, {"__builtins__": {}}, {})
                expression.set(str(result))
                self.update_status("Calculator: result ready")
            except Exception:
                messagebox.showerror("Error", "Calculation failed")

        buttons = [
            "7", "8", "9", "/",
            "4", "5", "6", "*",
            "1", "2", "3", "-",
            "0", ".", "(", ")",
            "C", "=", "+",
        ]

        frame = tk.Frame(window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        row, col = 0, 0
        for token in buttons:
            cmd = clear if token == "C" else evaluate if token == "=" else lambda t=token: press(t)
            ttk.Button(frame, text=token, command=cmd).grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            col += 1
            if col == 4:
                row += 1
                col = 0

        for i in range(5):
            frame.rowconfigure(i, weight=1)
        for i in range(4):
            frame.columnconfigure(i, weight=1)

    def open_notebook(self):
        window = tk.Toplevel(self.root)
        window.title("Notebook")
        window.geometry("620x460")

        text = tk.Text(window, wrap="word", font=("Consolas", 11))
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", self.store.data.get("notes", ""))

        def save_notes():
            self.store.data["notes"] = text.get("1.0", "end").rstrip("\n")
            self.store.save()
            self.update_status("Notebook: saved")

        ttk.Button(window, text="Save", command=save_notes).pack(pady=(0, 10))

    def open_files(self):
        window = tk.Toplevel(self.root)
        window.title("Files")
        window.geometry("640x460")

        left = tk.Frame(window)
        left.pack(side="left", fill="y", padx=(10, 5), pady=10)

        right = tk.Frame(window)
        right.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

        file_list = tk.Listbox(left, width=24)
        file_list.pack(fill="y", expand=True)

        editor = tk.Text(right, wrap="word", font=("Consolas", 11))
        editor.pack(fill="both", expand=True)

        name_var = tk.StringVar()
        ttk.Entry(left, textvariable=name_var).pack(fill="x", pady=(10, 5))

        files = self.store.data.setdefault("files", {})

        def refresh_files(select_name=None):
            file_list.delete(0, "end")
            names = sorted(files.keys())
            for filename in names:
                file_list.insert("end", filename)
            if select_name and select_name in names:
                index = names.index(select_name)
                file_list.selection_set(index)
                file_list.event_generate("<<ListboxSelect>>")

        def on_select(_=None):
            selected = file_list.curselection()
            if not selected:
                return
            filename = file_list.get(selected[0])
            editor.delete("1.0", "end")
            editor.insert("1.0", files.get(filename, ""))
            name_var.set(filename)

        def create_or_save():
            filename = name_var.get().strip()
            if not filename:
                messagebox.showwarning("Files", "Enter a file name")
                return
            files[filename] = editor.get("1.0", "end").rstrip("\n")
            self.store.save()
            refresh_files(select_name=filename)
            self.update_status(f"Files: saved {filename}")

        def delete_file():
            filename = name_var.get().strip()
            if filename in files:
                del files[filename]
                self.store.save()
                editor.delete("1.0", "end")
                name_var.set("")
                refresh_files()
                self.update_status(f"Files: deleted {filename}")

        ttk.Button(left, text="Create/Save", command=create_or_save).pack(fill="x", pady=2)
        ttk.Button(left, text="Delete", command=delete_file).pack(fill="x", pady=2)

        file_list.bind("<<ListboxSelect>>", on_select)
        refresh_files()

    def open_web_search(self):
        window = tk.Toplevel(self.root)
        window.title("Web Search")
        window.geometry("540x360")

        query_var = tk.StringVar()
        row = tk.Frame(window)
        row.pack(fill="x", padx=10, pady=10)

        ttk.Entry(row, textvariable=query_var).pack(side="left", fill="x", expand=True)

        history = tk.Listbox(window)
        history.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        searches = self.store.data.setdefault("search_history", [])

        def refresh_history():
            history.delete(0, "end")
            for query in searches[-50:]:
                history.insert("end", query)

        def search():
            query = query_var.get().strip()
            if not query:
                return
            searches.append(query)
            if len(searches) > MAX_SEARCH_HISTORY:
                del searches[:-MAX_SEARCH_HISTORY]
            self.store.save()
            refresh_history()
            webbrowser.open_new_tab(f"https://www.google.com/search?q={quote_plus(query)}")
            self.update_status("Web Search: opened browser")

        ttk.Button(row, text="Search", command=search).pack(side="left", padx=(8, 0))
        refresh_history()

    def open_users(self):
        window = tk.Toplevel(self.root)
        window.title("Users")
        window.geometry("420x320")

        users = self.store.data.setdefault("users", ["Admin"])
        active = self.store.data.get("active_user", users[0])

        users_box = tk.Listbox(window)
        users_box.pack(fill="both", expand=True, padx=10, pady=10)

        name_var = tk.StringVar()
        ttk.Entry(window, textvariable=name_var).pack(fill="x", padx=10)

        def refresh_users(select_name=None):
            users_box.delete(0, "end")
            for u in users:
                users_box.insert("end", u)
            if select_name and select_name in users:
                users_box.selection_set(users.index(select_name))

        def add_user():
            username = name_var.get().strip()
            if not username:
                return
            if username not in users:
                users.append(username)
                self.store.save()
                refresh_users(select_name=username)
                self.update_status(f"Users: added {username}")

        def set_active():
            selected = users_box.curselection()
            if not selected:
                return
            username = users_box.get(selected[0])
            self.store.data["active_user"] = username
            self.store.save()
            self.user_var.set(f"User: {username}")
            self.update_status(f"Users: active user is {username}")

        ttk.Button(window, text="Add User", command=add_user).pack(fill="x", padx=10, pady=(8, 4))
        ttk.Button(window, text="Set Active User", command=set_active).pack(fill="x", padx=10)

        refresh_users(select_name=active)

    def on_close(self):
        self.store.save()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        DesktopApp().run()
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1)
