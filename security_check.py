#!/usr/bin/env python3
"""
Dependency security scanner.

Runs ``pip-audit`` (preferred) or ``safety check`` to detect
known-vulnerable Python packages in the current environment.

Usage::

    python security_check.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys


def _run_pip_audit() -> int:
    """Run pip-audit and return the process exit code."""
    print("🔍 Running pip-audit …\n")
    result = subprocess.run(
        [sys.executable, "-m", "pip_audit"],
        capture_output=False,
    )
    return result.returncode


def _run_safety() -> int:
    """Run safety check and return the process exit code."""
    print("🔍 Running safety check …\n")
    result = subprocess.run(
        [sys.executable, "-m", "safety", "check", "--full-report"],
        capture_output=False,
    )
    return result.returncode


def main() -> None:
    """Auto-detect available scanner and run it."""
    if shutil.which("pip-audit") or _module_available("pip_audit"):
        code = _run_pip_audit()
    elif shutil.which("safety") or _module_available("safety"):
        code = _run_safety()
    else:
        print(
            "⚠️  No security scanner found.\n\n"
            "Install one of:\n"
            "  pip install pip-audit\n"
            "  pip install safety\n"
        )
        sys.exit(1)

    if code == 0:
        print("\n✅ No known vulnerabilities found.")
    else:
        print("\n❌ Vulnerabilities detected — review the report above.")
    sys.exit(code)


def _module_available(name: str) -> bool:
    """Return True if a Python module is importable."""
    import importlib.util
    return importlib.util.find_spec(name) is not None


if __name__ == "__main__":
    main()
