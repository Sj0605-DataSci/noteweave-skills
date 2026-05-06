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

from noteweave_skills import __version__

TEMPLATES = Path(__file__).parent / "templates"
_STAMP_FILE = ".noteweave-skills"  # written at project root after each install

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
# Version stamp helpers
# ---------------------------------------------------------------------------

def _read_stamp(project_root: Path) -> str | None:
    """Return the version string from the stamp file, or None if absent."""
    stamp = project_root / _STAMP_FILE
    try:
        return stamp.read_text().strip() if stamp.exists() else None
    except Exception:
        return None


def _write_stamp(project_root: Path) -> None:
    """Write current version to the stamp file."""
    try:
        (project_root / _STAMP_FILE).write_text(__version__ + "\n")
    except Exception:
        pass


def _check_stamp(project_root: Path) -> bool:
    """
    If a stamp exists and is outdated, warn the user and ask if they want
    to re-run the installer to update skills. Returns True if install should
    proceed (either no stamp, stamp matches, or user chose to update).
    """
    installed = _read_stamp(project_root)
    if installed is None:
        return True  # first time — no stamp yet
    if installed == __version__:
        print(f"  {_green('✓')} Skills already up to date (v{__version__}).")
        confirm = _ask(
            "  Re-install / overwrite existing skills? [y/n]: ",
            ["y", "n", "Y", "N"],
        ).lower()
        return confirm == "y"
    # Outdated stamp
    print(
        f"  {_yellow('!')} Skills were installed at v{installed}, "
        f"package is now v{__version__}."
    )
    confirm = _ask(
        "  Update skills to the latest version? [y/n]: ",
        ["y", "n", "Y", "N"],
    ).lower()
    return confirm == "y"


# ---------------------------------------------------------------------------
# Auto-detect IDE
# ---------------------------------------------------------------------------

def _detect_ide(project_root: Path) -> str | None:
    """Detect IDE from unambiguous project-level markers only."""
    if (project_root / ".cursor").is_dir():
        return "cursor"
    if (project_root / ".windsurfrules").exists():
        return "windsurf"
    if (project_root / "CLAUDE.md").exists():
        return "claude-code"
    if (project_root / ".zed").is_dir():
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
    print(f"  Package version: {_bold('v' + __version__)}")
    print()

    # Check stamp — warn if skills were installed with an older version
    if not _check_stamp(project_root):
        print()
        print("  Skipped. Run again any time to update.")
        print()
        return

    print()

    # Always ask — detection only sets the default hint
    detected = _detect_ide(project_root)
    detected_num = None
    if detected:
        detected_num = next(n for n, (_, k) in _IDES.items() if k == detected)

    print("  Which IDE are you using?")
    print()
    for num, (name, _) in _IDES.items():
        hint = f"  {_yellow('← detected')}" if num == detected_num else ""
        print(f"    {_bold(num)}) {name}{hint}")
    print()

    prompt = f"  Enter number [{detected_num}]: " if detected_num else "  Enter number: "
    raw = input(prompt).strip()
    if not raw and detected_num:
        choice = detected_num
    elif raw in _IDES:
        choice = raw
    else:
        while raw not in _IDES:
            raw = input(f"  Please enter one of {', '.join(_IDES.keys())}: ").strip()
            if not raw and detected_num:
                raw = detected_num
        choice = raw

    ide_key = _IDES[choice][1]

    print()
    print(f"  Installing skills...")
    print()

    _INSTALLERS[ide_key](project_root)

    # Write version stamp so future runs can detect outdated skills
    _write_stamp(project_root)

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
    print(f"  {_yellow('Tip:')} Add {_bold('.noteweave-skills')} to your .gitignore")
    print(f"       After {_bold('pip install --upgrade noteweave-skills')}, re-run this command")
    print(f"       to update your skill files — it will detect the version change automatically.")
    print()


if __name__ == "__main__":
    main()
