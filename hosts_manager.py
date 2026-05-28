#!/usr/bin/env python3
"""
hosts_manager.py — Manage the system hosts file (Windows or Linux).

Requires administrator / root privileges to write.
"""

import os
import subprocess
import sys

# Enable ANSI escape codes on Windows
if sys.platform == "win32":
    os.system("")

HOSTS_PATH = (
    r"C:\Windows\System32\drivers\etc\hosts"
    if sys.platform == "win32"
    else "/etc/hosts"
)


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    BLUE   = "\033[34m"
    GREEN2 = "\033[32m"

# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def header(title: str) -> None:
    bar = "─" * 52
    print(f"\n{C.BOLD}{C.BLUE}{bar}{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}  {title}{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}{bar}{C.RESET}\n")


def ok(msg: str) -> None:
    print(f"\n{C.GREEN}  ✓  {msg}{C.RESET}")


def err(msg: str) -> None:
    print(f"{C.RED}  ✗  {msg}{C.RESET}")


def ask(prompt: str) -> str:
    return input(f"{C.YELLOW}  {prompt}{C.RESET}").strip()


def validate_ip(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Hosts file parsing
#
# A line is treated as a host entry — active or commented — if, after
# stripping leading '#' and whitespace, the first token is a valid IP.
# This naturally skips all standard header comments (copyright notices,
# usage instructions, etc.) without any hard-coded line-count heuristic.
# ---------------------------------------------------------------------------
def parse_entry(line: str) -> dict | None:
    """
    Returns {ip, names, commented} if the line is a host entry, else None.
    """
    stripped = line.strip()
    commented = False

    if stripped.startswith("#"):
        content = stripped.lstrip("#").strip()
        commented = True
    else:
        content = stripped

    if not content:
        return None

    parts = content.split()
    if len(parts) >= 2 and validate_ip(parts[0]):
        return {"ip": parts[0], "names": parts[1:], "commented": commented}
    return None


def load_hosts() -> tuple[list[str], list[dict]]:
    """
    Returns (raw_lines, records).

    raw_lines — every line in the file, newlines preserved.
    records   — host entries (active AND commented-out), each with line_idx.
    """
    try:
        with open(HOSTS_PATH, "r") as fh:
            raw_lines = fh.readlines()
    except FileNotFoundError:
        err(f"Hosts file not found: {HOSTS_PATH}")
        sys.exit(1)
    except PermissionError:
        err(f"Cannot read {HOSTS_PATH} — try running as administrator / root.")
        sys.exit(1)

    records: list[dict] = []
    for i, line in enumerate(raw_lines):
        entry = parse_entry(line)
        if entry is not None:
            entry["line_idx"] = i
            records.append(entry)

    return raw_lines, records


def save_hosts(raw_lines: list[str]) -> None:
    try:
        with open(HOSTS_PATH, "w") as fh:
            fh.writelines(raw_lines)
    except PermissionError:
        err(f"Cannot write {HOSTS_PATH} — try running as administrator / root.")
        sys.exit(1)


def record_to_line(ip: str, names: list[str], commented: bool = False) -> str:
    body = f"{ip}\t{' '.join(names)}"
    return f"# {body}\n" if commented else f"{body}\n"


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------
def list_records(records: list[dict]) -> None:
    print(f"  {C.BOLD}{'#':<4} {'Status':<3}     {'IP Address':<20} Hostnames{C.RESET}")
    print(f"  {C.DIM}{'─' * 60}{C.RESET}")
    for i, rec in enumerate(records, 1):
        if rec["commented"]:
            status = f"{C.DIM}off     {C.RESET}"
            ip_col = f"{C.DIM}{rec['ip']:<20}{C.RESET}"
            names_col = f"{C.DIM}{', '.join(rec['names'])}{C.RESET}"
        else:
            status = f"{C.GREEN} on     {C.RESET}"
            ip_col = f"{C.GREEN2}{rec['ip']:<20}{C.RESET}"
            names_col = ", ".join(rec["names"])
        print(
            f"  {C.BOLD}{C.YELLOW}{i:<4}{C.RESET}"
            f"{status}  "
            f"{ip_col}"
            f"{names_col}"
        )
    print()


def pick_record(records: list[dict], action: str = "select") -> int:
    while True:
        raw = ask(f"Select entry to {action} (1–{len(records)}): ")
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(records):
                return idx
        except ValueError:
            pass
        err(f"Enter a number between 1 and {len(records)}")


# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------
def add_record(raw_lines: list[str]) -> None:
    header("Add New Entry")

    while True:
        ip = ask("IP address: ")
        if validate_ip(ip):
            break
        err("Invalid IP — use dotted-quad format, e.g. 192.168.1.10")

    print(f"\n{C.DIM}  Enter hostnames one at a time. Blank line when done.{C.RESET}")
    names: list[str] = []
    while True:
        name = ask(f"Hostname {len(names) + 1}: ")
        if not name:
            if names:
                break
            err("At least one hostname is required.")
        else:
            names.append(name)

    new_line = record_to_line(ip, names)

    if raw_lines and not raw_lines[-1].endswith("\n"):
        raw_lines.append("\n")
    raw_lines.append(new_line)

    save_hosts(raw_lines)
    ok(f"Added:  {C.CYAN}{new_line.rstrip()}{C.RESET}")


# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------
def edit_ip(current: str) -> str:
    new = ask(f"IP address  [{C.CYAN}{current}{C.YELLOW}]: ")
    if not new:
        return current
    while not validate_ip(new):
        err("Invalid IP — use dotted-quad format.")
        new = ask(f"IP address  [{C.CYAN}{current}{C.YELLOW}]: ")
        if not new:
            return current
    return new


def edit_names(current: list[str]) -> list[str]:
    print(f"\n{C.DIM}  Current hostnames: {', '.join(current)}{C.RESET}")
    print(f"{C.DIM}  Enter replacements one at a time, or press Enter on the first{C.RESET}")
    print(f"{C.DIM}  prompt to keep them all unchanged.{C.RESET}")

    first = ask(f"Hostname 1  [{C.CYAN}{current[0]}{C.YELLOW}]: ")
    if not first:
        return current

    names = [first]
    while True:
        name = ask(f"Hostname {len(names) + 1}: ")
        if not name:
            break
        names.append(name)
    return names


def edit_record(raw_lines: list[str], records: list[dict]) -> None:
    if not records:
        err("No entries found in the hosts file.")
        return

    header("Edit Entry")
    list_records(records)

    idx = pick_record(records, "edit")
    rec = records[idx]

    print(f"\n{C.BOLD}  Editing entry {idx + 1}{C.RESET}  "
          f"{C.DIM}(press Enter to leave a field unchanged){C.RESET}\n")

    new_ip    = edit_ip(rec["ip"])
    new_names = edit_names(rec["names"])

    new_line = record_to_line(new_ip, new_names, rec["commented"])
    raw_lines[rec["line_idx"]] = new_line

    save_hosts(raw_lines)
    ok(f"Updated:  {C.CYAN}{new_line.rstrip()}{C.RESET}")


# ---------------------------------------------------------------------------
# Toggle comment / uncomment
# ---------------------------------------------------------------------------
def toggle_record(raw_lines: list[str], records: list[dict]) -> None:
    if not records:
        err("No entries found in the hosts file.")
        return

    header("Toggle Entry On / Off")
    list_records(records)

    idx = pick_record(records, "toggle")
    rec = records[idx]

    new_commented = not rec["commented"]
    new_line = record_to_line(rec["ip"], rec["names"], new_commented)
    raw_lines[rec["line_idx"]] = new_line

    save_hosts(raw_lines)
    state = f"{C.DIM}disabled (commented out){C.RESET}" if new_commented else f"{C.GREEN}enabled (active){C.RESET}"
    ok(f"Entry {state}:  {C.CYAN}{rec['ip']}  {' '.join(rec['names'])}{C.RESET}")


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------
def delete_record(raw_lines: list[str], records: list[dict]) -> None:
    if not records:
        err("No entries found in the hosts file.")
        return

    header("Delete Entry")
    list_records(records)

    idx = pick_record(records, "delete")
    rec = records[idx]
    line = raw_lines[rec["line_idx"]].rstrip()

    print(f"\n  {C.RED}About to permanently delete:{C.RESET}  {C.CYAN}{line}{C.RESET}")
    confirm = ask("Are you sure? (y/n): ")
    if confirm.lower() != "y":
        print(f"\n{C.DIM}  Cancelled.{C.RESET}")
        return

    del raw_lines[rec["line_idx"]]
    save_hosts(raw_lines)
    ok(f"Deleted:  {C.CYAN}{line}{C.RESET}")


# ---------------------------------------------------------------------------
# Open in external editor
# ---------------------------------------------------------------------------
def open_editor() -> None:
    header("Open in Editor")
    if sys.platform == "win32":
        print(f"  Opening {C.CYAN}{HOSTS_PATH}{C.RESET} in Notepad …\n")
        subprocess.Popen(["notepad.exe", HOSTS_PATH])
    else:
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
        print(f"  Opening {C.CYAN}{HOSTS_PATH}{C.RESET} in {editor} …\n")
        subprocess.call([editor, HOSTS_PATH])
    ok("Editor launched. Return here when you are done.")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------
def main() -> None:
    header("Hosts File Manager")
    print(f"  {C.WHITE}Manage IP-to-hostname mappings in your system hosts file.{C.RESET}")
    print(f"  {C.DIM}File: {HOSTS_PATH}{C.RESET}\n")

    raw_lines, records = load_hosts()
    print(f"  {C.BOLD}Current entries:{C.RESET}\n")
    if records:
        list_records(records)
    else:
        print(f"  {C.DIM}(no entries found){C.RESET}\n")

    while True:
        raw_lines, records = load_hosts()

        print(f"  {C.BOLD}{C.WHITE}1{C.RESET}  Add a new entry")
        print(f"  {C.BOLD}{C.WHITE}2{C.RESET}  Edit an existing entry")
        print(f"  {C.BOLD}{C.WHITE}3{C.RESET}  Toggle entry on / off  {C.DIM}(comment / uncomment){C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}4{C.RESET}  Delete an entry")
        print(f"  {C.BOLD}{C.WHITE}5{C.RESET}  Open hosts file in editor")
        print(f"  {C.BOLD}{C.WHITE}6{C.RESET}  Exit")
        print()

        choice = ask("Select option (1–6): ")

        if choice == "1":
            add_record(raw_lines)
        elif choice == "2":
            edit_record(raw_lines, records)
        elif choice == "3":
            toggle_record(raw_lines, records)
        elif choice == "4":
            delete_record(raw_lines, records)
        elif choice == "5":
            open_editor()
        elif choice == "6":
            print(f"\n{C.DIM}  Goodbye.{C.RESET}\n")
            sys.exit(0)
        else:
            err("Please enter 1, 2, 3, 4, 5, or 6")
            continue

        raw_lines, records = load_hosts()
        print(f"\n  {C.BOLD}Current entries:{C.RESET}\n")
        if records:
            list_records(records)
        else:
            print(f"  {C.DIM}(no entries found){C.RESET}\n")


if __name__ == "__main__":
    main()
