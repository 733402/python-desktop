import json
import hashlib
import hmac
import secrets
from getpass import getpass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import quote_plus


DATA_FILE = Path(__file__).with_name("data.json")
CONFIG_FILE = Path(__file__).with_name("config.json")


class DataStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = {
            "users": ["Admin"],
            "active_user": "Admin",
            "user_password_hashes": {},
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
            users = [user for user in self.data.get("users", []) if isinstance(user, str) and user]
            if not users:
                users = ["Admin"]
            self.data["users"] = users

            active_user = self.data.get("active_user")
            if active_user not in users:
                self.data["active_user"] = users[0]

            password_hashes = self.data.get("user_password_hashes")
            if not isinstance(password_hashes, dict):
                password_hashes = {}
            legacy_passwords = self.data.get("user_passwords")
            if not isinstance(legacy_passwords, dict):
                legacy_passwords = {}

            for user in users:
                stored_hash = password_hashes.get(user)
                if isinstance(stored_hash, str) and self._is_password_hash(stored_hash):
                    continue
                legacy_password = legacy_passwords.get(user)
                if isinstance(legacy_password, str):
                    password_hashes[user] = self.hash_password(legacy_password)
                elif user == "Admin":
                    password_hashes[user] = self.hash_password("admin")
                else:
                    password_hashes[user] = self.hash_password("")
            self.data["user_password_hashes"] = {user: password_hashes[user] for user in users}
            self.data.pop("user_passwords", None)
        except (json.JSONDecodeError, OSError):
            self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    @staticmethod
    def _is_password_hash(value: str) -> bool:
        parts = value.split(":")
        return (
            len(parts) == 2
            and len(parts[0]) == 32
            and len(parts[1]) == 64
            and all(ch in "0123456789abcdef" for ch in value)
        )

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000
        ).hex()
        return f"{salt}:{digest}"

    @staticmethod
    def verify_password(stored_hash: str, password: str) -> bool:
        if not DataStore._is_password_hash(stored_hash):
            return False
        salt, expected = stored_hash.split(":")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000
        ).hex()
        return hmac.compare_digest(digest, expected)


class TerminalApp:
    def __init__(self):
        self.store = DataStore(DATA_FILE)
        self.system_config = ConfigStore(CONFIG_FILE)

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
            print("6) Neofetch")
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
            elif choice == "6":
                self.open_neofetch()
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
                results = self._search_web(query)
                if not results:
                    print("No results found.")
                    continue
                print("Results:")
                for i, item in enumerate(results, start=1):
                    print(f"{i}) {item}")
            elif choice == "2":
                if not searches:
                    print("No search history.")
                else:
                    print("Recent searches:")
                    for q in searches[-50:]:
                        print(f"- {q}")
            else:
                print("Invalid option.")

    @staticmethod
    def _search_web(query: str):
        url = (
            "https://api.duckduckgo.com/?"
            f"q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        )
        try:
            with urlopen(url, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, ValueError):
            print("Search failed.")
            return []

        results = []
        abstract = payload.get("AbstractText")
        if abstract:
            heading = payload.get("Heading") or "Top result"
            results.append(f"{heading}: {abstract}")

        for item in payload.get("RelatedTopics", []):
            if len(results) >= 5:
                break
            if isinstance(item, dict) and item.get("Text"):
                results.append(item["Text"])
            elif isinstance(item, dict) and isinstance(item.get("Topics"), list):
                for nested in item["Topics"]:
                    if len(results) >= 5:
                        break
                    if isinstance(nested, dict) and nested.get("Text"):
                        results.append(nested["Text"])
        return results[:5]

    def open_users(self):
        users = self.store.data.setdefault("users", ["Admin"])
        password_hashes = self.store.data.setdefault("user_password_hashes", {})

        while True:
            active = self.store.data.get("active_user", users[0] if users else "Admin")
            print("\nUsers")
            for i, user in enumerate(users, start=1):
                marker = " *" if user == active else ""
                print(f"{i}) {user}{marker}")

            print("a) Add user")
            print("s) Set active user")
            print("p) Change user password")
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
                password = getpass("New password: ").strip()
                if not password:
                    print("Password is required.")
                    continue
                users.append(username)
                password_hashes[username] = DataStore.hash_password(password)
                self.store.save()
                print(f"Added user: {username}")
            elif choice == "s":
                username = self._read("Username to activate: ")
                if username not in users:
                    print("User not found.")
                    continue
                password = getpass("Password: ").strip()
                if not DataStore.verify_password(password_hashes.get(username, ""), password):
                    print("Incorrect password.")
                    continue
                self.store.data["active_user"] = username
                self.store.save()
                print(f"Active user set to: {username}")
            elif choice == "p":
                username = self._read("Username: ")
                if username not in users:
                    print("User not found.")
                    continue
                current = getpass("Current password: ").strip()
                if not DataStore.verify_password(password_hashes.get(username, ""), current):
                    print("Incorrect password.")
                    continue
                updated = getpass("New password: ").strip()
                if not updated:
                    print("Password is required.")
                    continue
                password_hashes[username] = DataStore.hash_password(updated)
                self.store.save()
                print("Password updated.")
            else:
                print("Invalid option.")

    def open_neofetch(self):
        cfg = self.system_config.data
        active_user = self.store.data.get("active_user", "Admin")
        host = cfg.get("hostname", "pydesktop")
        lines = [
            f"{active_user}@{host}",
            "-" * (len(active_user) + len(host) + 1),
            f"OS: {cfg.get('os', 'PyDesktop OS')}",
            f"Kernel: {cfg.get('kernel', '6.6.0-pydesktop')}",
            f"CPU: {cfg.get('cpu', 'Python Virtual CPU')}",
            f"GPU: {cfg.get('gpu', 'Python Virtual GPU')}",
            f"RAM: {cfg.get('ram', '8 GB')}",
            f"Shell: {cfg.get('shell', 'python')}",
        ]
        art = [
            "    ____        ",
            "   / __ \\__  __ ",
            "  / /_/ / / / / ",
            " / ____/ /_/ /  ",
            "/_/    \\__, /   ",
            "      /____/    ",
        ]
        print("\nNeofetch")
        width = max(len(part) for part in art)
        for i in range(max(len(art), len(lines))):
            left = art[i] if i < len(art) else ""
            right = lines[i] if i < len(lines) else ""
            print(f"{left:<{width}}  {right}")

    def on_close(self):
        self.store.save()


class ConfigStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = {
            "hostname": "pydesktop",
            "os": "PyDesktop OS x86_64",
            "kernel": "6.6.0-pydesktop",
            "cpu": "Intel Core i9-14900KS (fake)",
            "gpu": "NVIDIA RTX 5090 (fake)",
            "ram": "64 GB DDR5 (fake)",
            "shell": "python",
        }
        self.load()

    def load(self):
        if not self.path.exists():
            self.save()
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                for key, value in loaded.items():
                    if isinstance(value, str):
                        self.data[key] = value
        except (json.JSONDecodeError, OSError):
            self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")


if __name__ == "__main__":
    try:
        TerminalApp().run()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
