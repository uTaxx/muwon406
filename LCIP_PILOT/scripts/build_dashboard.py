#!/usr/bin/env python3
"""TASK-012 준비 — 정적 HTML 대시보드 빌더 (로컬 빌드만, Drive 업로드는 하지 않음).

dashboard/template.html의 {{TOKEN}} 플레이스홀더에 데이터를 주입해 정적 HTML을 만든다.
기본 입력은 dashboard/sample_data.json이며, 실제 INTELLIGENCE_DB 연동은 TASK-012 본 구현
(다음 라운드)에서 Master Pipeline의 Dashboard 단계(舊 WF-P06)가 담당한다.

Architect Review Q7(2026-08-05)로 두 가지 출력 모드를 지원한다.
- Mode 1 (single, 기본): CSS/JS를 전부 인라인 삽입한 자기완결형 단일 HTML. Pilot 기본값 —
  Google Drive 저장·이메일 첨부·오프라인 열람에 유리하다.
- Mode 2 (split): dashboard.html + styles.css + app.js로 분리 Export. Enterprise 확장 시
  CSS/JS를 반복 재사용하거나 CDN에 올리는 시나리오를 대비한다.

기본 출력 위치는 output/ (gitignore 대상, 로컬 미리보기용)이다. dashboard/current/에 실제
"현재 버전"을 반영하는 것은 사용자 승인 하의 배포 절차(TASK-018)에서 수행한다.
"""
from __future__ import annotations

import argparse
import json
from html import escape

from _common import project_root

DASHBOARD_DIR = project_root() / "dashboard"

NUM_FIELDS = {"total_amount_usd", "claimant_count", "avg_amount_per_person_usd"}


def _fmt_num(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value:,}"


def render_tracker_rows(rows: list[dict]) -> str:
    if not rows:
        return '        <tr><td colspan="11" class="lcip-empty">등록된 Tracker 항목 없음</td></tr>'
    out = []
    for r in rows:
        out.append(
            "        <tr>"
            f"<td>{escape(r.get('published_at') or '-')}</td>"
            f"<td>{escape(r.get('region') or '-')}</td>"
            f"<td>{escape(r.get('title') or '-')}</td>"
            f"<td>{escape(r.get('defendant') or '-')}</td>"
            f"<td>{escape(r.get('event_type') or '-')}</td>"
            f"<td class=\"lcip-num\">{_fmt_num(r.get('total_amount_usd'))}</td>"
            f"<td class=\"lcip-num\">{_fmt_num(r.get('claimant_count'))}</td>"
            f"<td class=\"lcip-num\">{_fmt_num(r.get('avg_amount_per_person_usd'))}</td>"
            f"<td>{escape(r.get('status') or '-')}</td>"
            f"<td><a href=\"{escape(r.get('source_url') or '#')}\" target=\"_blank\" rel=\"noopener\">원문 보기</a></td>"
            f"<td>{escape(r.get('note') or '')}</td>"
            "</tr>"
        )
    return "\n".join(out)


def render_generic_list(items: list[dict], empty_label: str) -> str:
    if not items:
        return f'<p class="lcip-empty">{escape(empty_label)}</p>'
    rows = []
    for item in items:
        cols = "".join(f"<td>{escape(str(v))}</td>" for v in item.values())
        rows.append(f"<tr>{cols}</tr>")
    headers = "".join(f"<th>{escape(k)}</th>" for k in items[0].keys())
    return (
        '<table class="lcip-table"><thead><tr>'
        + headers
        + "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render_today_changes(data: dict) -> str:
    changes = data.get("today_changes") or []
    if not changes:
        return escape(data.get("today_changes_summary") or "신규 주요 변화 없음")
    return "<ul>" + "".join(f"<li>{escape(str(c))}</li>" for c in changes) + "</ul>"


def _render_common_tokens(data: dict) -> dict[str, str]:
    trend = data.get("litigation_amount_trend") or []
    return {
        "{{TOPIC_DISPLAY_NAME}}": escape(data.get("topic_display_name") or "엔지니어드스톤·실리코시스"),
        "{{GENERATED_AT_KST}}": escape(data.get("generated_at_kst") or ""),
        "{{TODAY_CHANGES_HTML}}": render_today_changes(data),
        "{{TRACKER_ROWS_HTML}}": render_tracker_rows(data.get("tracker_rows") or []),
        "{{NON_US_ISSUES_HTML}}": render_generic_list(data.get("non_us_issues") or [], "등록된 미국 외 이슈 없음"),
        "{{US_STATE_REGULATIONS_HTML}}": render_generic_list(
            data.get("us_state_regulations") or [], "등록된 미국 주별 규제 동향 없음"
        ),
        "{{GLOBAL_REGULATIONS_HTML}}": render_generic_list(
            data.get("global_regulations") or [], "등록된 글로벌 규제 동향 없음"
        ),
        "{{SAFEGUARD_NEWS_HTML}}": render_generic_list(data.get("safeguard_news") or [], "등록된 세이프가드 소식 없음"),
        "{{TREND_DATA_JSON}}": json.dumps(trend, ensure_ascii=False),
    }


def build_html(data: dict, mode: str = "single") -> str | dict[str, str]:
    """대시보드를 빌드한다.

    mode="single" (기본): 완전 자기완결형 단일 HTML 문자열을 반환한다 (하위 호환 — 기존
    호출부는 문자열을 그대로 사용할 수 있다).
    mode="split": {"dashboard.html": ..., "styles.css": ..., "app.js": ...} 딕셔너리를
    반환한다. HTML은 `<link>`/`<script src>`로 CSS/JS를 외부 참조한다.
    """
    if mode not in ("single", "split"):
        raise ValueError(f"알 수 없는 mode: {mode} (single 또는 split만 지원)")

    template = (DASHBOARD_DIR / "template.html").read_text(encoding="utf-8")
    styles = (DASHBOARD_DIR / "styles.css").read_text(encoding="utf-8")
    app_js = (DASHBOARD_DIR / "app.js").read_text(encoding="utf-8")

    html = template
    for token, value in _render_common_tokens(data).items():
        html = html.replace(token, value)

    if mode == "single":
        html = html.replace("{{INLINE_STYLES}}", styles)
        html = html.replace("{{INLINE_APP_JS}}", app_js)
        return html

    # mode == "split"
    html = html.replace(
        "<style>\n{{INLINE_STYLES}}\n</style>", '<link rel="stylesheet" href="styles.css">'
    )
    html = html.replace(
        "<script>\n{{INLINE_APP_JS}}\n</script>", '<script src="app.js"></script>'
    )
    return {"dashboard.html": html, "styles.css": styles, "app.js": app_js}


def main() -> int:
    parser = argparse.ArgumentParser(description="LCIP Pilot 대시보드 로컬 빌드")
    parser.add_argument("--data", default="dashboard/sample_data.json", help="입력 데이터 JSON 경로")
    parser.add_argument(
        "--mode", choices=["single", "split"], default="single",
        help="single(기본, 자기완결형 단일 HTML) 또는 split(HTML+CSS+JS 분리)",
    )
    parser.add_argument(
        "--out", default=None,
        help="출력 경로. single 모드는 파일 경로(기본 output/dashboard_preview.html), "
             "split 모드는 디렉터리 경로(기본 output/dashboard_preview/)",
    )
    args = parser.parse_args()

    data_path = project_root() / args.data
    data = json.loads(data_path.read_text(encoding="utf-8"))
    result = build_html(data, mode=args.mode)

    if args.mode == "single":
        out_path = project_root() / (args.out or "output/dashboard_preview.html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result, encoding="utf-8")
        print(f"대시보드 미리보기 생성 (single): {out_path}")
    else:
        out_dir = project_root() / (args.out or "output/dashboard_preview")
        out_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in result.items():
            (out_dir / filename).write_text(content, encoding="utf-8")
        print(f"대시보드 미리보기 생성 (split): {out_dir}/")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
