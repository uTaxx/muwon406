import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_secret_scan_passes_on_clean_repo():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "secret_scan.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_secret_scan_detects_planted_secret(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import secret_scan

    # 패턴 문자열을 두 조각으로 나눠서 만든다 — 이 테스트 파일 자체가 secret_scan의
    # 검사 대상이 되어 자기 자신을 오탐하지 않도록 하기 위함.
    fake_key = "sk-ant-" + "abcdefghijklmnopqrstuvwxyz0123456789"
    planted = tmp_path / "leaked.py"
    planted.write_text(f'ANTHROPIC_API_KEY = "{fake_key}"\n')

    findings = secret_scan.scan(tmp_path)
    assert findings, "심어둔 가짜 Secret을 탐지하지 못함"
