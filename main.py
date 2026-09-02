import json
from pathlib import Path
from urllib.parse import quote_plus


DATA_FILE = Path(__file__).with_name("data.json")


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
                self.data.update(loaded)
        except (json.JSONDecodeError, OSError):
            self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")


class TerminalApp:
    def __init__(self):
        self.store = DataStore(DATA_FILE)

    @staticmethod
    def _read(prompt: str = "") -> str:
        return input(prompt).strip()

    @staticmethod
    def _read_multiline(prompt: str) -> str:
        print(prompt)
        print("Finish by entering a single '.' on a line.")
        lines = []
        while True:
            line = input()
            if line == ".":
                break
            lines.append(line)
        return "\n".join(lines)

    def run(self):
        while True:
            active_user = self.store.data.get("active_user", "Admin")
            print("\n=== PyDesktop Terminal ===")
            print(f"Active user: {active_user}")
            print("1) Calculator")
            print("2) Notebook")
            print("3) Files")
            print("4) Web Search")
            print("5) Users")
            print("0) Exit")

            choice = self._read("Select: ")
            if choice == "1":
                self.open_calculator()
            elif choice == "2":
                self.open_notebook()
            elif choice == "3":
                self.open_files()
            elif choice == "4":
                self.open_web_search()
            elif choice == "5":
                self.open_users()
            elif choice == "0":
                self.on_close()
                break
            else:
                print("Invalid option.")

    def open_calculator(self):
        allowed = set("0123456789+-*/.() ")
        print("\nCalculator (press Enter on empty line to go back)")
        while True:
            expr = self._read("expr> ")
            if not expr:
                return
            if any(ch not in allowed for ch in expr):
                print("Invalid expression.")
                continue
            try:
                result = eval(expr, {"__builtins__": {}}, {})
                print(f"= {result}")
            except Exception:
                print("Calculation failed.")

    def open_notebook(self):
        notes = self.store.data.get("notes", "")
        print("\nCurrent notes:")
        print("-" * 30)
        print(notes if notes else "(empty)")
        print("-" * 30)

        choice = self._read("Overwrite notes? (y/N): ").lower()
        if choice != "y":
            return

        updated = self._read_multiline("Enter new notes:")
        self.store.data["notes"] = updated
        self.store.save()
        print("Notes saved.")

    def open_files(self):
        files = self.store.data.setdefault("files", {})

        while True:
            print("\nFiles")
            names = sorted(files.keys())
            if names:
                for i, name in enumerate(names, start=1):
                    print(f"{i}) {name}")
            else:
                print("(no files)")

            print("a) Create/Save file")
            print("v) View file")
            print("d) Delete file")
            print("b) Back")

            choice = self._read("Select: ").lower()
            if choice == "b":
                return
            if choice == "a":
                filename = self._read("File name: ")
                if not filename:
                    print("File name is required.")
                    continue
                current = files.get(filename, "")
                if current:
                    print("Current content:")
                    print(current)
                    print("-" * 30)
                content = self._read_multiline("Enter file content:")
                files[filename] = content
                self.store.save()
                print(f"Saved: {filename}")
            elif choice == "v":
                filename = self._read("File name to view: ")
                if filename not in files:
                    print("File not found.")
                    continue
                print("-" * 30)
                print(files[filename] or "(empty)")
                print("-" * 30)
            elif choice == "d":
                filename = self._read("File name to delete: ")
                if filename not in files:
                    print("File not found.")
                    continue
                del files[filename]
                self.store.save()
                print(f"Deleted: {filename}")
            else:
                print("Invalid option.")

    def open_web_search(self):
        searches = self.store.data.setdefault("search_history", [])

        while True:
            print("\nWeb Search")
            print("1) New search")
            print("2) View search history")
            print("0) Back")
            choice = self._read("Select: ")

            if choice == "0":
                return
            if choice == "1":
                query = self._read("Query: ")
                if not query:
                    print("Query is required.")
                    continue
                searches.append(query)
                self.store.save()
                url = f"https://www.google.com/search?q={quote_plus(query)}"
                print(f"Saved query. Open this URL manually:\n{url}")
            elif choice == "2":
                if not searches:
                    print("No search history.")
                else:
                    print("Recent searches:")
                    for q in searches[-50:]:
                        print(f"- {q}")
            else:
                print("Invalid option.")

    def open_users(self):
        users = self.store.data.setdefault("users", ["Admin"])

        while True:
            active = self.store.data.get("active_user", users[0] if users else "Admin")
            print("\nUsers")
            for i, user in enumerate(users, start=1):
                marker = " *" if user == active else ""
                print(f"{i}) {user}{marker}")

            print("a) Add user")
            print("s) Set active user")
            print("b) Back")

            choice = self._read("Select: ").lower()
            if choice == "b":
                return
            if choice == "a":
                username = self._read("New username: ")
                if not username:
                    print("Username is required.")
                    continue
                if username in users:
                    print("User already exists.")
                    continue
                users.append(username)
                self.store.save()
                print(f"Added user: {username}")
            elif choice == "s":
                username = self._read("Username to activate: ")
                if username not in users:
                    print("User not found.")
                    continue
                self.store.data["active_user"] = username
                self.store.save()
                print(f"Active user set to: {username}")
            else:
                print("Invalid option.")

    def on_close(self):
        self.store.save()


if __name__ == "__main__":
    try:
        TerminalApp().run()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
