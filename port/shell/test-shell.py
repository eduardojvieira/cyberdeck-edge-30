#!/usr/bin/env python3
"""Isolated Fish profile checks; run on host and native ARM64, without real history."""
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parent
FISH = shutil.which("fish")
assert FISH, "Install Fish before testing"


def run(args, env):
    return subprocess.run(args, env=env, capture_output=True, text=True, timeout=10)


with tempfile.TemporaryDirectory(prefix="eqs-shell-") as temporary:
    home = Path(temporary)
    env = {
        "HOME": str(home), "XDG_CONFIG_HOME": str(home / "config"),
        "XDG_DATA_HOME": str(home / "data"), "XDG_CACHE_HOME": str(home / "cache"),
        "TERM": "xterm-256color", "LC_ALL": "C.UTF-8", "PATH": os.environ["PATH"],
        "STARSHIP_CONFIG": str(ROOT / "starship.toml"),
    }

    def fish(code, interactive=False, environment=None):
        return run([FISH, "--no-config", "--private", *(["-i"] if interactive else []),
                    "-c", 'source "$argv[1]"; ' + code, str(ROOT / "config.fish")],
                   environment or env)

    assert run([FISH, "-n", str(ROOT / "config.fish")], env).returncode == 0
    assert run(["bash", "-n", str(ROOT / "interactive.bash")], env).returncode == 0

    # Noninteractive source must not run tools, download plugins or clear output.
    traps = home / "traps"
    traps.mkdir()
    for name in ("starship", "zoxide", "fzf", "curl", "atuin", "carapace", "clear", "herdr"):
        tool = traps / name
        tool.write_text('#!/bin/sh\nprintf "%s\\n" "$0" >> "$PROBE"\n')
        tool.chmod(0o755)
    quiet_env = env | {"PATH": str(traps), "PROBE": str(home / "probe")}
    result = fish("printf QUIET_OK", environment=quiet_env)
    assert (result.returncode, result.stdout, result.stderr) == (0, "QUIET_OK", ""), result
    assert not (home / "probe").exists(), "Noninteractive initialization ran a tool"
    print("PASS: noninteractive output and side effects")

    # Homebrew is interactive-only: never change script/SSH command resolution.
    result = run([FISH, "--no-config", "--private", "-c",
                  'set before "$PATH"; source "$argv[1]"; '
                  'test "$PATH" = "$before"; and not set -q HOMEBREW_PREFIX; '
                  'and printf BREW_QUIET_OK', str(ROOT / "homebrew.fish")], env)
    assert (result.returncode, result.stdout, result.stderr) == (0, "BREW_QUIET_OK", ""), result
    print("PASS: Homebrew integration leaves noninteractive environments unchanged")

    # User-local GUI wrappers retain argument boundaries and scoped graphics flags.
    for launcher, binary, expected in (
        ("brew-browser", ".local/opt/brew-browser-0.7.2-eqs1/brew-browser",
         ["/usr/share/glvnd/egl_vendor.d/50_mesa.json", "1", "wayland"]),
        ("antigravity", ".local/opt/antigravity-2.12.2/Antigravity-arm64/antigravity",
         ["", "", "", "--ozone-platform=wayland", "--disable-gpu"]),
    ):
        probe = home / binary
        probe.parent.mkdir(parents=True, exist_ok=True)
        probe.write_text('#!/bin/sh\nprintf "%s\\0" "$__EGL_VENDOR_LIBRARY_FILENAMES" '
                         '"$LIBGL_ALWAYS_SOFTWARE" "$GDK_BACKEND" "$@"\n')
        probe.chmod(0o755)
        result = run(["sh", str(ROOT / launcher), "path with spaces", "--literal"], env)
        assert result.returncode == 0 and not result.stderr, result
        assert result.stdout.split("\0") == expected + ["path with spaces", "--literal", ""], result
    print("PASS: GUI launchers preserve arguments and scope rendering overrides")

    probe = home / ".local/opt/brew-browser-0.7.2-eqs1/brew-browser"
    probe.write_text('#!/bin/sh\nprintf "%s:%s" '
                     '"${WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS-unset}" "$WEBKIT_FORCE_SANDBOX"\n')
    result = run(["sh", str(ROOT / "brew-browser")], env | {
        "WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS": "1", "WEBKIT_FORCE_SANDBOX": "0"})
    assert (result.returncode, result.stdout, result.stderr) == (0, "unset:1", ""), result
    print("PASS: Brew Browser does not inherit Droidian sandbox bypasses")

    bare = home / "bare"
    bare.mkdir()
    result = fish("printf OPTIONAL_OK", True, env | {"PATH": str(bare)})
    assert result.returncode == 0 and "OPTIONAL_OK" in result.stdout and not result.stderr, result
    print("PASS: missing optional tools do not break startup")

    # A cancelled picker must not start nvim; option-like/multiline names stay one argument.
    editor = bare / "nvim"
    editor.write_text('#!/bin/sh\nprintf "%s\\0" "$@" > "$NVIM_ARGS"\n')
    editor.chmod(0o755)
    args = home / "editor-args"
    picker_env = env | {"PATH": str(bare), "NVIM_ARGS": str(args), "TEST_FILE": "-odd name\nsecond line"}
    result = fish("function fzfbat; return 130; end; fzfnvim", True, picker_env)
    assert result.returncode == 0 and not args.exists(), result
    result = fish('function fzfbat; printf "%s\\0" "$TEST_FILE"; end; fzfnvim', True, picker_env)
    assert result.returncode == 0 and not result.stderr, result
    assert args.read_bytes() == b"--\0-odd name\nsecond line\0"
    print("PASS: picker cancellation and filename boundaries")

    result = fish('functions -q z; and functions -q fish_prompt; and '
                  'test "$fish_key_bindings" = fish_vi_key_bindings; and '
                  'test "$fish_bind_mode" = insert; and printf INTERACTIVE_OK; '
                  'bind -M insert \\cr; functions ls', True)
    assert result.returncode == 0 and not result.stderr, result
    assert "INTERACTIVE_OK" in result.stdout and "fzf-history-widget" in result.stdout, result
    assert "ls --color=auto" in result.stdout and "gls" not in result.stdout, result
    print("PASS: real tool initialization, vi insert mode, Ctrl-R and Debian ls")

    result = run(["bash", "--noprofile", "--rcfile", str(ROOT / "interactive.bash"),
                  "-ic", "printf BASH_COMMAND_OK"], env)
    assert result.returncode == 0 and result.stdout == "BASH_COMMAND_OK", result
    print("PASS: explicit Bash command is not replaced by Fish")

    config = tomllib.loads((ROOT / "starship.toml").read_text())
    assert config["palette"] == "gentleman" and config["command_timeout"] <= 1000
    assert config["palettes"]["gentleman"]["blue"] == "#7FB4CA"
    for width in (40, 80):
        result = run(["starship", "prompt", "--path", str(home), "--terminal-width", str(width)], env)
        assert result.returncode == 0 and result.stdout.strip() and not result.stderr, result
    print("PASS: Gentleman prompt renders at 40/80 columns with bounded timeout")

    ghostty_config = ROOT / "ghostty.conf"
    if ghostty_config.exists():
        assert run(["sh", "-n", str(ROOT / "ghostty")], env).returncode == 0
        command = next(line.split("=", 1)[1].strip() for line in
                       ghostty_config.read_text().splitlines() if line.startswith("command ="))
        overrides = dict.fromkeys(("__EGL_VENDOR_LIBRARY_FILENAMES", "LIBGL_ALWAYS_SOFTWARE",
                                   "GDK_BACKEND", "GSK_RENDERER"), "TEST_ONLY")
        result = run([*shlex.split(command), "--no-config", "--private", "-c",
                      "for key in " + " ".join(overrides) +
                      "; if set -q $key; exit 1; end; end; printf CLEAN_CHILD"],
                     env | overrides)
        assert result.returncode == 0 and result.stdout == "CLEAN_CHILD" and not result.stderr, result
        if shutil.which("ghostty"):
            result = run(["ghostty", "+validate-config", f"--config-file={ghostty_config}"], env)
            assert result.returncode == 0 and not result.stdout and not result.stderr, result
        print("PASS: Ghostty launcher syntax, child environment isolation and available config validator")

print("PASS: shell checks; graphical appearance and keyboard input need separate target evidence")
