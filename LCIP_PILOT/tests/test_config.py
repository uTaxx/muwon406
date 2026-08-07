import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_validate_config_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_config.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_bootstrap_project_dry_run_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "bootstrap_project.py"), "--dry-run"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout


def test_bootstrap_project_validates_registries_on_boot():
    """Round 8: "RegistryManager는 Project Boot 시 전체 Registry를 검증한다."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "bootstrap_project.py"), "--dry-run"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Registry 검증" in result.stdout
    assert "전체 통과" in result.stdout


def test_no_duplicate_topic_ids():
    from _common import load_yaml

    topics = load_yaml("config/topics.yaml")["topics"]
    ids = [t["topic_id"] for t in topics]
    assert len(ids) == len(set(ids))
