# python-desktop

A simple Python terminal app (`main.py`) that provides desktop-like utilities from the command line.

## Apps included
- Calculator
- Notebook (saved notes)
- Files (create/edit/delete simple text files)
- Web Search (stores search history and shows in-terminal results)
- Users (add users with passwords + set active user)
- Neofetch (shows fake system profile from `config.json`)

All app data is persisted in `data.json`.
User passwords are stored as salted password hashes in `data.json` (`Admin` defaults to password `admin`).
System profile data is stored in `config.json` and can be edited to customize fake CPU, GPU, RAM, and other values.

## Run
```bash
python main.py
```

No graphical desktop session is required.
