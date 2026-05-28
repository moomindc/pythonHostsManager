# Hosts Manager

A simple interactive CLI tool for managing your system hosts file on Windows and Linux.

## Features

- List all host entries (active and commented-out) with colour-coded status
- Add new IP-to-hostname mappings
- Edit existing entries
- Toggle entries on/off (comment/uncomment) without deleting them
- Delete entries
- Open the hosts file directly in an external editor

## Requirements

- Python 3.10+
- Administrator (Windows) or root (Linux) privileges to write the hosts file

## Usage

```
sudo python hosts_manager.py        # Linux / macOS
# Run as Administrator on Windows
python hosts_manager.py
```

The tool presents a numbered menu. Use the number keys to navigate:

```
1  Add a new entry
2  Edit an existing entry
3  Toggle entry on / off  (comment / uncomment)
4  Delete an entry
5  Open hosts file in editor
6  Exit
```

## Hosts file location

| Platform | Path |
|----------|------|
| Windows  | `C:\Windows\System32\drivers\etc\hosts` |
| Linux    | `/etc/hosts` |
