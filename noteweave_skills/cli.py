"""
noteweave_skills/cli.py — Interactive installer.

Asks the user which IDE they use, then drops the right skill files
into the current working directory.

Entry point: `noteweave-skills` (or `python -m noteweave_skills`)
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

TEMPLATES = Path(__file__).parent / "templates"

# IDE options shown in the menu
_IDES = {
    "1": ("Cursor", "cursor"),
    "2": ("Claude Code", "claude-code"),
    "3": ("Windsurf", "windsurf"),
    "4": ("Zed", "zed"),
    "5": ("Other (copies shared NOTEWEAVE.md)", "other"),
}

_CYAN  = "\033[96m"
_GREEN = "\033[92m"
_BOLD  = "\033[1m"
_RESET = "\033[0m"
_YELLOW = "\033[93m"


def _print(msg: str = "") -> None:
    print(msg)


def _bold(s: str) -> str:
    return f"{_BOLD}{s}{_RESET}"


def _cyan(s: str) -> str:
    return f"{_CYAN}{s}{_RESET}"


def _green(s: str) -> str:
    return f"{_GREEN}{s}{_RESET}"


def _yellow(s: str) -> str:
    return f"{_YELLOW}{s}{_RESET}"


def _ask(prompt: str, choices: list[str] | None = None) -> str:
    while True:
        val = input(prompt).strip()
        if not choices or val in choices:
            return val
        print(f"  Please enter one of: {', '.join(choices)}")


# ---------------------------------------------------------------------------
# IDE-specific installers
# ---------------------------------------------------------------------------

def _install_cursor(project_root: Path) -> None:
    skills_dir = project_root / ".cursor" / "skills"
    src = TEMPLATES / "cursor" / "skills"
    if not src.exists():
        print(f"  Template not found: {src}")
        return

    for skill_dir in src.iterdir():
        if not skill_dir.is_dir():
            continue
        dest = skills_dir / skill_dir.name
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_dir / "skill.md", dest / "skill.md")
        print(f"  {_green('✓')} {dest.relative_to(project_root)}/skill.md")

    print()
    print(_bold("Skills installed for Cursor."))
    print("They appear as /noteweave-search, /noteweave-analyze, /noteweave-write")
    print("in Cursor chat, and auto-trigger when context matches.")


def _install_claude_code(project_root: Path) -> None:
    src = TEMPLATES / "shared" / "NOTEWEAVE.md"
    dest = project_root / "NOTEWEAVE.md"
    shutil.copy2(src, dest)
    print(f"  {_green('✓')} NOTEWEAVE.md")

    # Check for existing CLAUDE.md and offer to append import
    claude_md = project_root / "CLAUDE.md"
    if claude_md.exists():
        content = claude_md.read_text()
        import_line = "@NOTEWEAVE.md"
        if import_line not in content:
            add = _ask(
                f"\n  Found CLAUDE.md. Add '{import_line}' to it? [y/n]: ",
                ["y", "n", "Y", "N"],
            ).lower()
            if add == "y":
                with claude_md.open("a") as f:
                    f.write(f"\n\n{import_line}\n")
                print(f"  {_green('✓')} Added @NOTEWEAVE.md to CLAUDE.md")
        else:
            print(f"  {_yellow('→')} @NOTEWEAVE.md already in CLAUDE.md, skipping")
    else:
        print()
        print(_yellow("  No CLAUDE.md found. To activate, add this line to your CLAUDE.md:"))
        print("  @NOTEWEAVE.md")

    print()
    print(_bold("Skills installed for Claude Code."))


def _install_windsurf(project_root: Path) -> None:
    src = TEMPLATES / "shared" / "NOTEWEAVE.md"
    dest_md = project_root / "NOTEWEAVE.md"
    shutil.copy2(src, dest_md)
    print(f"  {_green('✓')} NOTEWEAVE.md")

    rules_file = project_root / ".windsurfrules"
    snippet = "\n\n# Noteweave Research API\n@NOTEWEAVE.md\n"

    if rules_file.exists():
        content = rules_file.read_text()
        if "NOTEWEAVE" not in content:
            add = _ask(
                f"\n  Found .windsurfrules. Append Noteweave reference? [y/n]: ",
                ["y", "n", "Y", "N"],
            ).lower()
            if add == "y":
                with rules_file.open("a") as f:
                    f.write(snippet)
                print(f"  {_green('✓')} Appended to .windsurfrules")
        else:
            print(f"  {_yellow('→')} .windsurfrules already references NOTEWEAVE, skipping")
    else:
        rules_file.write_text(snippet.strip() + "\n")
        print(f"  {_green('✓')} Created .windsurfrules")

    print()
    print(_bold("Skills installed for Windsurf."))
    print("Windsurf will now include the Noteweave API context in every session.")


def _install_zed(project_root: Path) -> None:
    src = TEMPLATES / "shared" / "NOTEWEAVE.md"
    dest = project_root / "NOTEWEAVE.md"
    shutil.copy2(src, dest)
    print(f"  {_green('✓')} NOTEWEAVE.md")

    zed_dir = project_root / ".zed"
    zed_dir.mkdir(exist_ok=True)
    settings_file = zed_dir / "settings.json"

    import json

    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text())
        except Exception:
            settings = {}
    else:
        settings = {}

    existing_prompt = settings.get("assistant", {}).get("default_model_prompt", "")
    noteweave_note = "See NOTEWEAVE.md in this project for Noteweave research API usage."

    if "NOTEWEAVE" not in existing_prompt:
        settings.setdefault("assistant", {})
        settings["assistant"]["default_model_prompt"] = (
            (existing_prompt + "\n\n" if existing_prompt else "") + noteweave_note
        )
        settings_file.write_text(json.dumps(settings, indent=2))
        print(f"  {_green('✓')} Added Noteweave note to .zed/settings.json")
    else:
        print(f"  {_yellow('→')} .zed/settings.json already references NOTEWEAVE, skipping")

    print()
    print(_bold("Skills installed for Zed."))
    print("Zed's AI assistant will now be aware of the Noteweave API.")


def _install_other(project_root: Path) -> None:
    src = TEMPLATES / "shared" / "NOTEWEAVE.md"
    dest = project_root / "NOTEWEAVE.md"
    shutil.copy2(src, dest)
    print(f"  {_green('✓')} NOTEWEAVE.md")
    print()
    print(_bold("NOTEWEAVE.md dropped in project root."))
    print("Add it to your IDE's context/rules file to activate.")


_INSTALLERS = {
    "cursor":     _install_cursor,
    "claude-code": _install_claude_code,
    "windsurf":   _install_windsurf,
    "zed":        _install_zed,
    "other":      _install_other,
}


# ---------------------------------------------------------------------------
# Auto-detect IDE
# ---------------------------------------------------------------------------

def _detect_ide(project_root: Path) -> str | None:
    if (project_root / ".cursor").exists():
        return "cursor"
    if (project_root / "CLAUDE.md").exists() or shutil.which("claude"):
        return "claude-code"
    if (project_root / ".windsurfrules").exists():
        return "windsurf"
    if (project_root / ".zed").exists():
        return "zed"
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    project_root = Path.cwd()

    print()
    print(_bold(_cyan("  Noteweave Skills Installer")))
    print(_cyan("  ─────────────────────────────────────────"))
    print(f"  Installing into: {_bold(str(project_root))}")
    print()

    # Auto-detect
    detected = _detect_ide(project_root)
    ide_key: str

    if detected:
        ide_name = next(n for _, (n, k) in _IDES.items() if k == detected)
        print(f"  Detected IDE: {_bold(ide_name)}")
        confirm = _ask(f"  Install skills for {ide_name}? [y/n]: ", ["y", "n", "Y", "N"]).lower()
        if confirm == "y":
            ide_key = detected
        else:
            detected = None  # fall through to manual selection

    if not detected:
        print("  Which IDE are you using?")
        print()
        for num, (name, _) in _IDES.items():
            print(f"    {_bold(num)}) {name}")
        print()
        choice = _ask("  Enter number: ", list(_IDES.keys()))
        ide_key = _IDES[choice][1]

    print()
    print(f"  Installing skills...")
    print()

    _INSTALLERS[ide_key](project_root)

    # Token reminder
    print()
    print(_cyan("  ─────────────────────────────────────────"))
    print(f"  {_bold('Next step:')} set your Noteweave token")
    print()
    print("  1. Get token:  https://apps.noteweave.io/dashboard/tokens → Generate Token")
    print("  2. Set it:     export NOTEWEAVE_TOKEN=\"nw_ext_...\"")
    print("     or add to   .env:  NOTEWEAVE_TOKEN=nw_ext_...")
    print()
    print(f"  {_green('Done!')} Your AI agent now knows how to use the Noteweave research API.")
    print()


if __name__ == "__main__":
    main()
