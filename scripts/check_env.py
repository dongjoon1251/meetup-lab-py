"""실습 환경 점검. 실행: `python scripts/check_env.py`

[OK ] / [WARN] / [FAIL] 로 한 줄씩 출력하고, FAIL 이 없으면 마지막 줄에 `모두 OK` 를 출력한다.
"""

import importlib
import re
import shutil
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

MIN_PYTHON = (3, 11)
PACKAGES = ["fastapi", "uvicorn", "httpx", "pytest", "mcp", "meetup_lab"]
COPILOT_BUILTIN_VSCODE = (1, 140)  # 이 버전부터 Copilot Chat 내장

failures = 0


def report(level: str, message: str) -> None:
    global failures
    if level == "FAIL":
        failures += 1
    tag = {"OK": "[OK ]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[level]
    print(f"{tag} {message}")


def run(cmd: list[str]) -> subprocess.CompletedProcess | None:
    exe = shutil.which(cmd[0])
    if exe is None:
        return None
    try:
        return subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None


def check_python() -> None:
    version = ".".join(map(str, sys.version_info[:3]))
    need = ".".join(map(str, MIN_PYTHON))
    if sys.version_info[:2] >= MIN_PYTHON:
        report("OK", f"Python {version} >= {need}")
    else:
        report("FAIL", f"Python {version} >= {need}  → Python {need} 이상 설치 후 venv 다시 만들기")


def check_packages() -> None:
    for name in PACKAGES:
        try:
            importlib.import_module(name)
            report("OK", f"import {name}")
        except Exception as e:  # noqa: BLE001 — 어떤 이유로든 import 실패면 FAIL
            report("FAIL", f"import {name}  → python -m pip install -r requirements.txt ({type(e).__name__})")


def check_tools() -> None:
    report("OK" if shutil.which("git") else "FAIL", "git on PATH")
    report("OK" if shutil.which("gh") else "WARN", "gh on PATH" + ("" if shutil.which("gh") else "  → (선택) GitHub CLI 설치"))
    report("OK" if shutil.which("code") else "FAIL", "code on PATH" + ("" if shutil.which("code") else "  → VS Code 에서 'Shell Command: Install code command in PATH'"))

    auth = run(["gh", "auth", "status"])
    if auth is not None and auth.returncode == 0:
        report("OK", "gh auth status")
    else:
        report("WARN", "gh auth status  → (선택) gh auth login")


def check_copilot() -> None:
    label = "GitHub Copilot Chat"
    if shutil.which("code") is None:
        report("FAIL", f"{label}  → code 명령이 없어 확인 불가 (위 code on PATH 먼저)")
        return
    extensions = run(["code", "--list-extensions"])
    if extensions is not None and "github.copilot-chat" in extensions.stdout.lower():
        report("OK", label)
        return
    version = run(["code", "--version"])
    match = re.match(r"(\d+)\.(\d+)", version.stdout) if version is not None else None
    if match and tuple(map(int, match.groups())) >= COPILOT_BUILTIN_VSCODE:
        report("OK", label)
    else:
        report("FAIL", f"{label} (확장 또는 VS Code 내장)  → VS Code 를 최신 버전으로 업데이트")


def main() -> int:
    check_python()
    check_packages()
    check_tools()
    check_copilot()
    print()
    if failures:
        print(f"FAIL {failures}건 — 위 [FAIL] 줄의 안내대로 고친 뒤 다시 실행하세요.")
        return 1
    print("모두 OK — 실습 준비가 끝났습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
