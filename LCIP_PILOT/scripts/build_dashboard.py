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
from html import escape

from _common import project_root
from dashboard_data_provider import StaticJSONDataProvider
from dashboard_widgets import DEFAULT_WIDGETS, render_generic_list

DASHBOARD_DIR = project_root() / "dashboard"


def _render_common_tokens(data: dict, widgets: list = DEFAULT_WIDGETS) -> dict[str, str]:
    """Round 4 지시(Widget 기반 대시보드)에 따라, 각 Widget이 자신의 토큰만 책임지고 채운다.
    `widgets` 목록에서 항목을 빼거나 추가하면 해당 섹션만 독립적으로 켜지거나 꺼진다 —
    나머지 Widget/토큰에는 영향을 주지 않는다."""
    tokens = {
        "{{TOPIC_DISPLAY_NAME}}": escape(data.get("topic_display_name") or "엔지니어드스톤·실리코시스"),
        "{{GENERATED_AT_KST}}": escape(data.get("generated_at_kst") or ""),
    }
    for widget in widgets:
        tokens[f"{{{{{widget.token}}}}}"] = widget.render(data)
    return tokens


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
    data = StaticJSONDataProvider(data_path).get_data()
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
