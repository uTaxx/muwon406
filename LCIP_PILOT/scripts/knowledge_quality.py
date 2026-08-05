#!/usr/bin/env python3
"""TASK-004C — Knowledge Quality Score 계산기.

knowledge/KNOWLEDGE_GOVERNANCE.md §10 공식을 구현한다:

    Quality Score(%) = (신뢰 가능한 계층 수 / 12) × 100

    "신뢰 가능한 계층" = Confidence != draft AND Reference URL이 채워짐
                        AND Last Verified가 신선도 임계값 이내
                        (단, N/A 계층은 무조건 신뢰 가능으로 카운트)
"""
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import date, datetime

from _common import project_root

KNOWLEDGE_DIR = project_root() / "knowledge"

COMPANY_PROFILE_DOCS = ["LX_HAUSYS_COMPANY_DNA.md", "LX_HOLDINGS_CONTEXT.md"]

# knowledge/KNOWLEDGE_GOVERNANCE.md §8 신선도 임계값 (일 단위)
FRESHNESS_DAYS_COMPANY_PROFILE = 183  # 6개월
UNSET_MARKERS = {"", "(미확인)", "todo", "todo: source required", "n/a", "not applicable"}

SECTION_HEADER_RE = re.compile(r"^## (\d+)\. ([^\n]+)$", re.MULTILINE)
METADATA_LINE_RE = re.compile(
    r"-\s*Source:\s*(?P<source>.*?)\s*/\s*Reference URL:\s*(?P<url>.*?)\s*/\s*"
    r"Confidence:\s*(?P<confidence>.*?)\s*/\s*Last Verified:\s*(?P<last_verified>.*?)\s*$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class LayerStatus:
    number: int
    name: str
    is_na: bool
    confidence: str
    reference_url: str
    last_verified: str
    reliable: bool


def _is_unset(value: str) -> bool:
    return value.strip().lower() in UNSET_MARKERS


def _is_na(confidence: str, reference_url: str) -> bool:
    return confidence.strip().upper() == "N/A" or reference_url.strip().upper() == "N/A"


def _is_fresh(last_verified: str, today: date, threshold_days: int) -> bool:
    try:
        verified_date = datetime.strptime(last_verified.strip(), "%Y-%m-%d").date()
    except ValueError:
        return False
    return (today - verified_date).days <= threshold_days


def parse_layers(text: str, today: date | None = None) -> list[LayerStatus]:
    today = today or date.today()
    headers = list(SECTION_HEADER_RE.finditer(text))
    layers = []
    for i, match in enumerate(headers):
        number = int(match.group(1))
        if number > 12:
            continue
        name = match.group(2).split("—")[0].strip()
        section_start = match.end()
        section_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section_text = text[section_start:section_end]

        meta_match = None
        for meta_match in METADATA_LINE_RE.finditer(section_text):
            pass  # 마지막 매치(섹션 끝의 메타데이터 줄)를 사용

        if meta_match is None:
            layers.append(LayerStatus(number, name, False, "draft", "", "", reliable=False))
            continue

        confidence = meta_match.group("confidence")
        ref_url = meta_match.group("url")
        last_verified = meta_match.group("last_verified")
        is_na = _is_na(confidence, ref_url)

        if is_na:
            reliable = True
        else:
            reliable = (
                not _is_unset(confidence)
                and confidence.strip().lower() != "draft"
                and not _is_unset(ref_url)
                and _is_fresh(last_verified, today, FRESHNESS_DAYS_COMPANY_PROFILE)
            )
        layers.append(LayerStatus(number, name, is_na, confidence, ref_url, last_verified, reliable))
    return layers


def score_document(filename: str) -> tuple[float, list[LayerStatus]]:
    text = (KNOWLEDGE_DIR / filename).read_text(encoding="utf-8")
    layers = parse_layers(text)
    if not layers:
        return 0.0, layers
    reliable_count = sum(1 for l in layers if l.reliable)
    return (reliable_count / 12) * 100, layers


def main() -> int:
    parser = argparse.ArgumentParser(description="LCIP Pilot Knowledge Quality Score")
    parser.add_argument("--verbose", action="store_true", help="계층별 상세 출력")
    args = parser.parse_args()

    print("=== Knowledge Quality Score (knowledge/KNOWLEDGE_GOVERNANCE.md §10) ===")
    scores = []
    for filename in COMPANY_PROFILE_DOCS:
        score, layers = score_document(filename)
        scores.append(score)
        print(f"\n{filename}: {score:.1f}%")
        if args.verbose:
            for layer in layers:
                status = "N/A(신뢰가능)" if layer.is_na else ("OK" if layer.reliable else "미확정")
                print(f"  {layer.number:2d}. {layer.name:<16s} [{status}]")

    overall = sum(scores) / len(scores) if scores else 0.0
    print(f"\n전체 평균: {overall:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
