"""Round 13(RC2 실체화) — n8n_deploy.py의 실제 배포 로직(apply_deploy) 검증.

실제 n8n Cloud 없이, GoogleRSSAdapter의 http_get 주입과 동일한 패턴으로 가짜 HTTP
클라이언트를 주입해 "기존 Workflow 이름이 있으면 갱신, 없으면 생성, 삭제 API는 절대
호출하지 않는다"는 안전장치를 검증한다.
"""
from __future__ import annotations

from n8n_deploy import apply_deploy


class _FakeResponse:
    def __init__(self, json_data: dict):
        self._json_data = json_data

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._json_data


class _FakeHttp:
    def __init__(self, existing_workflows: list[dict]):
        self.existing_workflows = existing_workflows
        self.calls: list[tuple[str, str, dict | None]] = []

    def get(self, url: str, headers=None, timeout=None):
        self.calls.append(("GET", url, None))
        return _FakeResponse({"data": self.existing_workflows})

    def post(self, url: str, headers=None, json=None, timeout=None):
        self.calls.append(("POST", url, json))
        return _FakeResponse({"id": "new-id-123"})

    def put(self, url: str, headers=None, json=None, timeout=None):
        self.calls.append(("PUT", url, json))
        return _FakeResponse({"id": url.rsplit("/", 1)[-1]})


def test_apply_deploy_creates_new_workflows_when_none_exist():
    http = _FakeHttp(existing_workflows=[])
    results = apply_deploy("https://fake-n8n.example.com", "fake-api-key", http=http)

    post_calls = [c for c in http.calls if c[0] == "POST"]
    delete_calls = [c for c in http.calls if c[0] == "DELETE"]
    assert len(delete_calls) == 0  # 삭제 API는 절대 호출하지 않는다
    assert len(post_calls) == len(results)
    assert all(r["action"] == "created" for r in results)
    # 안전장치: payload에 active 필드를 절대 보내지 않는다("항상 active:false"를
    # API 계약에 기대지 않고 payload 자체에서 보장)
    for _, _, payload in post_calls:
        assert "active" not in payload
        assert set(payload.keys()) == {"name", "nodes", "connections", "settings"}


def test_apply_deploy_updates_existing_workflows_instead_of_duplicating():
    from n8n_deploy import load_local_workflows

    local = load_local_workflows()
    existing = [{"id": f"existing-{i}", "name": wf["name"]} for i, wf in enumerate(local)]
    http = _FakeHttp(existing_workflows=existing)

    results = apply_deploy("https://fake-n8n.example.com", "fake-api-key", http=http)

    post_calls = [c for c in http.calls if c[0] == "POST"]
    put_calls = [c for c in http.calls if c[0] == "PUT"]
    assert len(post_calls) == 0  # 전부 이미 존재 -> 생성 없음
    assert len(put_calls) == len(local)
    assert all(r["action"] == "updated" for r in results)


def test_apply_deploy_never_calls_delete():
    http = _FakeHttp(existing_workflows=[])
    apply_deploy("https://fake-n8n.example.com", "fake-api-key", http=http)
    assert not hasattr(http, "delete_called")
    assert all(call[0] != "DELETE" for call in http.calls)
