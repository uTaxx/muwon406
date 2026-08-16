"""GitHub Actions에서 muwon.db 상태 파일을 구글드라이브와 주고받는 헬퍼.

GitHub Actions 러너는 매번 새 가상머신이라 로컬 디스크가 실행이 끝나면
사라진다 — 보유 종목·가상현금(positions/engine_state 테이블)이 이어져야
하는 이 프로젝트 구조상, 실행 시작 시 이 스크립트로 muwon.db를 구글드라이브에서
내려받고, 끝나면 다시 올려서 다음 실행이 이어받게 한다.

서비스 계정으로 인증한다 — 사람이 브라우저로 로그인해서 매번 토큰을 새로
받아야 하는 OAuth 사용자 인증 흐름은 GitHub Actions처럼 사람이 개입할 수
없는 환경엔 안 맞는다. 설정 방법(GCP 서비스 계정 만들기, 드라이브 폴더
공유, GitHub Secrets 등록)은 docs/deploy_github_actions.md 참고.

사용 예:
    python scripts/gdrive_sync.py download --folder-id XXX --filename muwon.db --out ./muwon.db
    python scripts/gdrive_sync.py upload --folder-id XXX --filename muwon.db --path ./muwon.db
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _build_service():
    key_json = os.environ.get("GDRIVE_SA_KEY_JSON")
    if not key_json:
        raise SystemExit("GDRIVE_SA_KEY_JSON 환경변수가 없습니다 (서비스 계정 JSON 키 원문).")
    info = json.loads(key_json)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def _find_file_id(service, folder_id: str, filename: str) -> str | None:
    query = f"name = '{filename}' and '{folder_id}' in parents and trashed = false"
    result = (
        service.files()
        .list(
            q=query,
            fields="files(id, name)",
            spaces="drive",
            corpora="allDrives",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    files = result.get("files", [])
    return files[0]["id"] if files else None


def download(folder_id: str, filename: str, out_path: str) -> None:
    service = _build_service()
    file_id = _find_file_id(service, folder_id, filename)
    if file_id is None:
        print(
            f"구글드라이브에 '{filename}'이 아직 없습니다 — 첫 실행이면 정상이며, "
            "새 상태(초기 현금)로 시작합니다.",
            file=sys.stderr,
        )
        return

    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    with open(out_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    print(f"다운로드 완료: {filename} -> {out_path}")


def upload(folder_id: str, filename: str, path: str) -> None:
    service = _build_service()
    file_id = _find_file_id(service, folder_id, filename)
    media = MediaFileUpload(path, resumable=True)

    if file_id is None:
        metadata = {"name": filename, "parents": [folder_id]}
        service.files().create(
            body=metadata, media_body=media, fields="id", supportsAllDrives=True
        ).execute()
        print(f"신규 업로드 완료: {filename}")
    else:
        service.files().update(
            fileId=file_id, media_body=media, supportsAllDrives=True
        ).execute()
        print(f"업데이트 완료: {filename}")


def main() -> None:
    parser = argparse.ArgumentParser(description="구글드라이브 상태 파일(muwon.db) 동기화")
    sub = parser.add_subparsers(dest="command", required=True)

    dl = sub.add_parser("download", help="구글드라이브 -> 로컬")
    dl.add_argument("--folder-id", required=True)
    dl.add_argument("--filename", required=True)
    dl.add_argument("--out", required=True)

    up = sub.add_parser("upload", help="로컬 -> 구글드라이브 (있으면 덮어쓰기)")
    up.add_argument("--folder-id", required=True)
    up.add_argument("--filename", required=True)
    up.add_argument("--path", required=True)

    args = parser.parse_args()
    if args.command == "download":
        download(args.folder_id, args.filename, args.out)
    elif args.command == "upload":
        upload(args.folder_id, args.filename, args.path)


if __name__ == "__main__":
    main()
