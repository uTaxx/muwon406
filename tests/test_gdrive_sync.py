"""구글 계정 없이도 gdrive_sync 로직(신규 파일이면 create, 있으면 update,
없으면 새 상태로 시작, 다운로드는 원자적 교체)이 맞는지 Drive API를
모킹해서 검증한다."""

from unittest.mock import MagicMock, patch

from muwon.cloud import gdrive_sync


def make_fake_service(existing_file_id: str | None):
    service = MagicMock()
    service.files.return_value.list.return_value.execute.return_value = {
        "files": [{"id": existing_file_id, "name": "muwon.db"}] if existing_file_id else []
    }
    return service


@patch.dict("os.environ", {"GDRIVE_SA_KEY_JSON": '{"type": "service_account"}'})
@patch("muwon.cloud.gdrive_sync.service_account.Credentials.from_service_account_info")
@patch("muwon.cloud.gdrive_sync.build")
@patch("muwon.cloud.gdrive_sync.MediaFileUpload")
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
@patch("muwon.cloud.gdrive_sync.service_account.Credentials.from_service_account_info")
@patch("muwon.cloud.gdrive_sync.build")
@patch("muwon.cloud.gdrive_sync.MediaFileUpload")
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
@patch("muwon.cloud.gdrive_sync.service_account.Credentials.from_service_account_info")
@patch("muwon.cloud.gdrive_sync.build")
def test_download_skips_when_file_missing(mock_build, mock_creds, tmp_path):
    service = make_fake_service(existing_file_id=None)
    mock_build.return_value = service

    out_path = tmp_path / "muwon.db"
    gdrive_sync.download("FOLDER123", "muwon.db", str(out_path))

    assert not out_path.exists()
    service.files.return_value.get_media.assert_not_called()


@patch.dict("os.environ", {"GDRIVE_SA_KEY_JSON": '{"type": "service_account"}'})
@patch("muwon.cloud.gdrive_sync.service_account.Credentials.from_service_account_info")
@patch("muwon.cloud.gdrive_sync.build")
@patch("muwon.cloud.gdrive_sync.MediaIoBaseDownload")
def test_download_writes_via_temp_file_then_atomic_replace(mock_downloader_cls, mock_build, mock_creds, tmp_path):
    """대시보드가 백그라운드에서 주기적으로 다시 내려받는 동안, 그 파일을
    동시에 읽는 쪽이 반쯤 쓰인 파일을 보지 않도록 임시 파일에 쓰고 나서
    교체하는지 확인한다."""
    service = make_fake_service(existing_file_id="EXISTING456")
    mock_build.return_value = service

    def fake_downloader(fileobj, request):
        fileobj.write(b"downloaded-db-bytes")
        instance = MagicMock()
        instance.next_chunk.return_value = (None, True)
        return instance

    mock_downloader_cls.side_effect = fake_downloader

    out_path = tmp_path / "muwon.db"
    gdrive_sync.download("FOLDER123", "muwon.db", str(out_path))

    assert out_path.exists()
    assert out_path.read_bytes() == b"downloaded-db-bytes"
    assert not (tmp_path / "muwon.db.tmp").exists()  # 교체 후 임시 파일이 남지 않아야 함


def test_missing_master_key_env_raises_system_exit():
    with patch.dict("os.environ", {}, clear=True):
        try:
            gdrive_sync._build_service()
            raise AssertionError("SystemExit이 발생해야 한다")
        except SystemExit as e:
            assert "GDRIVE_SA_KEY_JSON" in str(e)
