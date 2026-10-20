"""석탄 가격 예측 범위 모델 v1 (2026-10-20).

방향(오를지 내릴지)은 예측하지 않는다. 검증 결과 방향은 현재 변수로 예측되지 않았다(문서 1~6차).
이 모델은 「다음 몇 개월의 월평균 가격이 어느 범위에 들 가능성이 높은가」만 낸다.

입력은 두 가지 모드다.
  현물 모드  : 최신 현물(주·일 단위 지수, 예: ICI4·ICI5 주간)을 알 때. 중심을 월말 현물에 둔다.
  월평균 모드: 월평균만 알 때(예: IMF 뉴캐슬 월별). 중심을 마지막 월평균에 둔다.
두 모드 모두 중심은 변화 없음(0)으로 두고 폭만 변동성으로 정한다.
  폭 = 최근 변동성(EWMA) x 과거 표준화 변화의 경험 분위수(10·50·90%).
과거 표준화 변화는 예측 시점에 이미 확정된 값만 쓴다.

사용:  python3 -I 예측모델_v1.py 월평균모드 뉴캐슬_월별가격.json
       python3 -I 예측모델_v1.py 현물모드 현물가격.csv   (열: 날짜,값  YYYY-MM-DD)
"""
import json, math, sys, csv
import numpy as np
from collections import defaultdict

분위 = [0.1, 0.5, 0.9]
람다 = 0.9           # 변동성 EWMA 감쇠. 직전 12개월 정도를 주로 반영한다.
최소학습 = 36         # 경험 분위수를 쓰려면 최소 이 개월 수의 과거가 필요하다.

def 다음달(m, k=1):
    y, mo = map(int, m.split("-")); mo += k
    while mo > 12: y += 1; mo -= 12
    while mo < 1: y -= 1; mo += 12
    return "%d-%02d" % (y, mo)

def 월집계(점들):
    """[(YYYY-MM-DD, 값)] -> {월: {평균, 말일}}"""
    g = defaultdict(list)
    for d, v in sorted(점들): g[d[:7]].append(v)
    return {m: {"평균": float(np.mean(v)), "말일": float(v[-1])} for m, v in g.items()}

def 월간수익률(기준):
    """기준: {월: 값}. 연속한 월의 로그 수익률."""
    ms = sorted(기준)
    return {ms[i]: math.log(기준[ms[i]] / 기준[ms[i - 1]]) for i in range(1, len(ms)) if 다음달(ms[i - 1]) == ms[i]}

def 변동성(수익률, m):
    ks = [k for k in sorted(수익률) if k <= m]
    if len(ks) < 12: return None
    v = float(np.var([수익률[k] for k in ks[:12]]))
    for k in ks[12:]: v = 람다 * v + (1 - 람다) * 수익률[k] ** 2
    return math.sqrt(v)

def 표본(모드, 자료):
    """(기준월 m, 중심값 c, 월평균맵, 수익률맵) 를 만든다. 중심값은 현물 모드에서 월말 현물, 월평균 모드에서 월평균."""
    agg = 월집계(자료) if 모드 == "현물모드" else {m: {"평균": v, "말일": v} for m, v in 자료.items()}
    중심 = {m: a["말일"] if 모드 == "현물모드" else a["평균"] for m, a in agg.items()}
    return agg, 중심, 월간수익률(중심)

def 백테스트(모드, 자료, 시작="2015-01", 기간들=(1, 2, 3)):
    agg, 중심, 수익률 = 표본(모드, 자료)
    ms = sorted(agg); 결과 = []
    for h in 기간들:
        행 = []
        for m in ms:
            n = 다음달(m, h)
            if n in agg and m in 중심:
                s = 변동성(수익률, m)
                if s: 행.append((m, math.log(agg[n]["평균"] / 중심[m]), s))
        적중 = []; 폭 = []; 핀볼 = 0.0; 건수 = 0
        for t, (m, y, s) in enumerate(행):
            if m < 시작: continue
            과거 = [yy / ss for (mm, yy, ss) in 행[:t] if mm <= 다음달(m, -h)]
            if len(과거) < 최소학습: continue
            a, b, c = [s * x for x in np.quantile(과거, 분위)]
            적중.append(a <= y <= c); 폭.append(c - a)
            핀볼 += sum(max(q * (y - v), (q - 1) * (y - v)) for q, v in zip(분위, (a, b, c))); 건수 += 1
        if 건수: 결과.append({"기간": h, "평가월수": 건수, "80%구간적중": round(float(np.mean(적중)), 3),
                             "평균폭_로그": round(float(np.mean(폭)), 3), "핀볼손실": round(핀볼 / 건수, 4)})
    return 결과

def 예측(모드, 자료, 기간들=(1, 2, 3)):
    agg, 중심, 수익률 = 표본(모드, 자료)
    ms = sorted(agg); m0 = ms[-1]; s = 변동성(수익률, m0); 나옴 = []
    for h in 기간들:
        행 = []
        for m in ms:
            n = 다음달(m, h)
            if n in agg and m in 중심:
                sm = 변동성(수익률, m)
                if sm: 행.append((m, math.log(agg[n]["평균"] / 중심[m]) / sm))
        z = [x for (m, x) in 행 if m <= 다음달(m0, -h)]
        if len(z) < 최소학습: continue
        a, b, c = [s * x for x in np.quantile(z, 분위)]
        기준값 = 중심[m0]
        나옴.append({"대상월": 다음달(m0, h), "하단10": round(기준값 * math.exp(a), 1), "중심": round(기준값 * math.exp(b), 1),
                    "상단90": round(기준값 * math.exp(c), 1)})
    return {"기준월": m0, "기준값": round(중심[m0], 1), "월변동성": round(s, 4), "예측": 나옴}

if __name__ == "__main__":
    모드, 파일 = sys.argv[1], sys.argv[2]
    if 모드 == "월평균모드": 자료 = {m: v for m, v in json.load(open(파일))}
    else: 자료 = [(r[0], float(r[1])) for r in csv.reader(open(파일)) if r and r[0][:2] == "20"]
    print(json.dumps({"백테스트": 백테스트(모드, 자료), "최신 예측": 예측(모드, 자료)}, ensure_ascii=False, indent=1))
