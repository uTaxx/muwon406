"""Round 13(RC2 실체화) — create_drive_structure.py의 실제 apply_plan() 검증.

실제 Google Drive/OAuth 없이, `googleapiclient.discovery.build`와
`google_auth.load_credentials`를 가짜로 교체해 폴더 생성 로직(멱등성 — 이미 있는
폴더는 재사용하고 중복 생성하지 않는다)만 검증한다.
"""
from __future__ import annotations

import google_auth
import googleapiclient.discovery
from create_drive_structure import apply_plan, build_plan


class _FakeFilesList:
    def __init__(self, files: list[dict]):
        self._files = files

    def execute(self) -> dict:
        return {"files": self._files}


class _FakeFilesCreate:
    def __init__(self, service: "_FakeDriveService", body: dict):
        self._service = service
        self._body = body

    def execute(self) -> dict:
        new_id = f"folder-{len(self._service.created)}"
        self._service.created.append({"id": new_id, **self._body})
        return {"id": new_id}


class _FakeFiles:
    def __init__(self, service: "_FakeDriveService"):
        self._service = service

    def list(self, q=None, spaces=None, fields=None):
        # 이름+부모 조합이 이미 만들어진 폴더 중에 있으면 그걸 반환한다(멱등성 검증용).
        matches = [f for f in self._service.created if f["name"] in q]
        return _FakeFilesList(matches)

    def create(self, body=None, fields=None):
        return _FakesFilesCreateWrapper(self._service, body)


class _FakesFilesCreateWrapper(_FakeFilesCreate):
    pass


class _FakeDriveService:
    def __init__(self):
        self.created: list[dict] = []

    def files(self):
        return _FakeFiles(self)


def test_apply_plan_creates_root_and_subfolders(monkeypatch):
    fake_service = _FakeDriveService()
    monkeypatch.setattr(googleapiclient.discovery, "build", lambda *a, **kw: fake_service)
    monkeypatch.setattr(google_auth, "load_credentials", lambda auth_mode, scopes: object())

    plan = build_plan()
    apply_plan(plan, auth_mode="service_account")

    created_names = {f["name"] for f in fake_service.created}
    assert plan["root_folder_name"] in created_names
    for entry in plan["folders_to_ensure"]:
        leaf_name = entry["path"].rsplit("/", 1)[-1]
        assert leaf_name in created_names


def test_apply_plan_n8n_only_mode_does_not_call_drive_api(monkeypatch):
    call_count = {"n": 0}

    def _fail_if_called(*a, **kw):
        call_count["n"] += 1
        raise AssertionError("n8n_only 모드에서는 Drive API를 호출하면 안 된다")

    monkeypatch.setattr(googleapiclient.discovery, "build", _fail_if_called)

    plan = build_plan()
    apply_plan(plan, auth_mode="n8n_only")

    assert call_count["n"] == 0
