---
information_class: public
document_type: knowledge
company: LX Hausys
source_types: [news, trade_press, official_website]
reference_date: 2026-08-05
last_reviewed: 2026-08-05
source_urls:
  - https://www.stoneworld.com/articles/95354-lx-hausys-unveils-new-quartz-technology-touts-us-manufacturing-amid-tariff-concerns
  - https://www.lxhausys.com/us/blog/who-manufactures-viatera-quartz/
  - https://www.gmdsurfaces.com/the-start-of-a-new-partnership-with-lx-hausys/
confidence: medium
version: 0.3
owner: user (Architect Review Round 6 — TASK-K01)
knowledge_taxonomy_version: 1.0
---

# LX Hausys Value Chain

> Master Pipeline의 AI Analyze 단계(舊 WF-P05 Risk Analysis, ADR-007로 통합)에서
> "계열사·사업·제품·Value Chain 영향경로 분석"에 사용되는 참조 문서.
> `knowledge/KNOWLEDGE_POLICY.md` §4 우선순위 2위 문서. Round 6 TASK-K01로 1차 리서치
> 반영 — `LX_HAUSYS_COMPANY_DNA.md`와 동일 출처를 Value Chain 관점으로 재구성했다.

## 1. 원재료 조달 (Upstream)

VIATERA 쿼츠 표면재는 자사 공식 발표 기준 최대 93% 쿼츠(석영, 결정형 실리카 함유 광물)
함량이다. 구체적 원재료 공급망(원산지·공급사)과 관세/통상 조치 관련 공개 리스크는 이번
라운드에서 확인하지 못했다.

- 주요 원재료: 쿼츠(최대 93%, VIATERA 기준, 자사 공식 발표)
- 공급망 세부사항(원산지·공급사): TODO: source required
- 원재료 수입/조달 관련 공개된 리스크(관세, 통상 조치 등): TODO: source required
- Source: LX Hausys 공식 블로그
- Reference URL: https://www.lxhausys.com/us/blog/who-manufactures-viatera-quartz/
- Confidence: medium
- Last Verified: 2026-08-05

## 2. 생산 (Manufacturing)

미국 조지아주 Adairsville 생산단지(2010년 가동 개시)에 HIMACS 솔리드 서페이스 1개 라인,
VIATERA 쿼츠 3개 라인, 자동차 내장재 1개 라인이 있다. 부지 293,000+ sq ft, 종업원
160명 이상. 산업안전 관련 인증/기준(예: OSHA 대비 자체 기준)은 공개된 것을 확인하지
못했다.

- 생산 거점별 주요 제품군: Adairsville, GA(미국) — HIMACS×1, VIATERA×3, 자동차내장재×1
- 국내(한국) 생산 거점: TODO: source required
- 생산 공정상 공개된 산업안전 관련 인증/기준: TODO: source required
- Source: Stone World
- Reference URL: https://www.stoneworld.com/articles/95354-lx-hausys-unveils-new-quartz-technology-touts-us-manufacturing-amid-tariff-concerns
- Confidence: medium
- Last Verified: 2026-08-05

## 3. 유통·판매 (Distribution)

미국 내 유통은 지역 Fabricator/유통 파트너(예: 일리노이·인디애나 지역의 GMD Surfaces)를
통한 대리점 채널이 확인된다. 판매 지역별 매출 비중은 확인하지 못했다.

- 판매 채널: Fabricator/유통 파트너 대리점 (예: GMD Surfaces, 미국 일리노이·인디애나)
- 주요 판매 지역별 비중: TODO: source required
- Source: GMD Surfaces 보도자료
- Reference URL: https://www.gmdsurfaces.com/the-start-of-a-new-partnership-with-lx-hausys/
- Confidence: medium
- Last Verified: 2026-08-05

## 4. 고객·최종 사용처 (Downstream)

최종 고객은 주방·욕실 표면재 시공업체, 건축·인테리어 시공업체 등 B2B 산업이다. B2C
직접판매 비중은 확인하지 못했다.

- 최종 고객 산업: 건축·인테리어(주방·욕실 표면재 시공업체) 중심
- B2B/B2C 비중: TODO: source required
- Source: GMD Surfaces 보도자료, LX Hausys 공식 블로그
- Reference URL: https://www.gmdsurfaces.com/the-start-of-a-new-partnership-with-lx-hausys/
- Confidence: medium
- Last Verified: 2026-08-05

## 5. Value Chain 상 리스크 전이 경로 (엔지니어드스톤·실리코시스 기준)

> TOP-0001 분석용. 실제 공개 사실이 확인된 범위까지만 기록한다.

- **소송/보험 커버리지 → 판매법인 영향 경로**: Bloomberg Law 보도(2026)에 따르면
  LX Hausys Ltd. 미국 법인이 실리카 관련 소송의 보험 커버리지 분쟁(실리카 면책조항)에
  이름이 언급됐다 — 이는 미국 판매법인의 잠재적 소송 대응 비용/보험료 부담으로 이어질
  수 있는 경로다(구체적 재무 영향은 확인하지 못함, TODO).
- **규제 강화 → 제품 포트폴리오 영향**: 저실리카/무실리카 제품 전환 발표는 확인하지
  못했다(TODO: source required).
- **관세 → 원가·수출 영향**: Stone World 보도(2026)는 LX Hausys가 미국 현지 생산
  (Adairsville)을 관세 대응 및 "Made in USA" 경쟁 우위로 홍보하고 있음을 보여준다 —
  이는 관세 리스크를 현지 생산으로 일부 상쇄하는 경로로 해석할 수 있다.

- Source: Bloomberg Law, Stone World
- Reference URL: https://news.bloomberglaw.com/insurance/artificial-stone-silica-suits-set-up-insurance-coverage-fights ,
  https://www.stoneworld.com/articles/95354-lx-hausys-unveils-new-quartz-technology-touts-us-manufacturing-amid-tariff-concerns
- Confidence: medium
- Last Verified: 2026-08-05

## 6. 원문 링크

- https://www.stoneworld.com/articles/95354-lx-hausys-unveils-new-quartz-technology-touts-us-manufacturing-amid-tariff-concerns
- https://www.lxhausys.com/us/blog/who-manufactures-viatera-quartz/
- https://www.gmdsurfaces.com/the-start-of-a-new-partnership-with-lx-hausys/
- https://news.bloomberglaw.com/insurance/artificial-stone-silica-suits-set-up-insurance-coverage-fights
