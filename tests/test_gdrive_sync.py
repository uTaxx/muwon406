"""구글 계정 없이도 gdrive_sync.py의 로직(신규 파일이면 create, 있으면
update, 없으면 새 상태로 시작)이 맞는지 Drive API를 모킹해서 검증한다."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "gdrive_sync.py"

_spec = importlib.util.spec_from_file_location("gdrive_sync", SCRIPT_PATH)
gdrive_sync = importlib.util.module_from_spec(_spec)
sys.modules["gdrive_sync"] = gdrive_sync
_spec.loader.exec_module(gdrive_sync)


def make_fake_service(existing_file_id: str | None):
    service = MagicMock()
    service.files.return_value.list.return_value.execute.return_value = {
        "files": [{"id": existing_file_id, "name": "muwon.db"}] if existing_file_id else []
    }
    return service


@patch.dict("os.environ", {"GDRIVE_SA_KEY_JSON": '{"type": "service_account"}'})
@patch("gdrive_sync.service_account.Credentials.from_service_account_info")
@patch("gdrive_sync.build")
@patch("gdrive_sync.MediaFileUpload")
def test_upload_creates_new_file_when_absent(mock_media, mock_build, mock_creds, tmp_path):
    service = make_fake_service(existing_file_id=None)
    mock_build.return_value = service

    local_file = tmp_path / "muwon.db"
    local_file.write_bytes(b"fake-db-bytes")

    gdrive_sync.upload("FOLDER123", "muwon.db", str(local_file))

    service.files.return_value.create.assert_called_once()
    create_kwargs = service.files.return_value.create.call_args.kwargs
    assert create_kwargs["body"] == {"name": "muwon.db", "parents": ["FOLDER123"]}
    service.files.return_value.update.assert_not_called()


@patch.dict("os.environ", {"GDRIVE_SA_KEY_JSON": '{"type": "service_account"}'})
@patch("gdrive_sync.service_account.Credentials.from_service_account_info")
@patch("gdrive_sync.build")
@patch("gdrive_sync.MediaFileUpload")
def test_upload_updates_existing_file(mock_media, mock_build, mock_creds, tmp_path):
    service = make_fake_service(existing_file_id="EXISTING456")
    mock_build.return_value = service

    local_file = tmp_path / "muwon.db"
    local_file.write_bytes(b"fake-db-bytes")

    gdrive_sync.upload("FOLDER123", "muwon.db", str(local_file))

    service.files.return_value.update.assert_called_once()
    update_kwargs = service.files.return_value.update.call_args.kwargs
    assert update_kwargs["fileId"] == "EXISTING456"
    service.files.return_value.create.assert_not_called()


@patch.dict("os.environ", {"GDRIVE_SA_KEY_JSON": '{"type": "service_account"}'})
@patch("gdrive_sync.service_account.Credentials.from_service_account_info")
@patch("gdrive_sync.build")
def test_download_skips_when_file_missing(mock_build, mock_creds, tmp_path):
    service = make_fake_service(existing_file_id=None)
    mock_build.return_value = service

    out_path = tmp_path / "muwon.db"
    gdrive_sync.download("FOLDER123", "muwon.db", str(out_path))

    assert not out_path.exists()
    service.files.return_value.get_media.assert_not_called()


def test_missing_master_key_env_raises_system_exit():
    with patch.dict("os.environ", {}, clear=True):
        try:
            gdrive_sync._build_service()
            raise AssertionError("SystemExit이 발생해야 한다")
        except SystemExit as e:
            assert "GDRIVE_SA_KEY_JSON" in str(e)
