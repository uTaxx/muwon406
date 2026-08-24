/* ─────────────────────────────────────────────────────────────
   sdlab 대시보드

   이 화면은 상태를 들고 있지 않다. 열 때마다 n8n 웹훅에 물어보고 그린다.
   스트림릿이 죽던 병 — 배포가 밀리는 것, DB를 갈아 끼우다 연결이 끊기는
   것 — 은 전부 서버가 상태를 들고 있어서 생겼다. 여기엔 그 병이 없다.

   ## 웹훅 규약

   손익만 기존 웹훅을 그대로 쓴다(이미 돌고 있다).

     POST {바탕}/webhook/muwon-balance   { 열쇠 }

   나머지는 창구 하나로 모은다. 열쇠 검사도, 허용 출처도 한 곳에서만
   보게 하려는 것이다 — 여럿으로 나누면 하나를 빠뜨리고 빠뜨린 줄도 모른다.

     POST {바탕}/webhook/sdlab   { 열쇠, 무엇, ...인자 }

       무엇: "승인목록"  →  { 날짜, 후보: [{종목코드, 종목명, 섹터, 수량, 예상가, 승인}] }
       무엇: "승인"      →  { 종목코드, 값: "Y"|"N"|"" }  →  { 된것: true }
       무엇: "기록"      →  { 승률, 손익비, 최대낙폭, 거래: [...] }
       무엇: "기준"      →  { 매매켜짐, 전략, 전략들: [...], 손절, 비중, 동시보유 }
       무엇: "기준저장"  →  { 바꿀것: {...} }  →  { 된것: true }

   아직 /webhook/sdlab 은 만들어지지 않았다. 그때까지는 예시 자료를 그리고
   **예시라는 것을 화면에 밝힌다.** 조용히 가짜를 보여 주면 그게 제일 나쁘다.
   ───────────────────────────────────────────────────────────── */

(() => {
  "use strict";

  const 저장키 = "sdlab.연결";
  const 기본바탕 = "https://sondullab.app.n8n.cloud";
  const 자동간격 = 60000;   // 증권사가 토큰 발급을 자주 하면 막는다. 1분이면 넉넉하다.

  const $ = (id) => document.getElementById(id);
  const 보이기 = (id, 켤까) => $(id).classList.toggle("숨김", !켤까);

  let 자동 = null;
  let 이번창 = null;        // localStorage가 막혀도 이번 방문은 굴러가야 한다
  let 기준값 = null;        // 되돌리기용 원본

  /* ── 연결 정보 ─────────────────────────────────────── */

  const 읽기 = () => {
    try {
      const ㄱ = JSON.parse(localStorage.getItem(저장키) || "null");
      if (ㄱ && ㄱ.열쇠) return ㄱ;
    } catch { /* 막힌 브라우저 — 이번창으로 간다 */ }
    return 이번창;
  };
  const 쓰기 = (값) => {
    이번창 = 값;
    try { localStorage.setItem(저장키, JSON.stringify(값)); return true; }
    catch { return false; }
  };
  const 지우기 = () => {
    이번창 = null;
    try { localStorage.removeItem(저장키); } catch { /* 무시 */ }
  };

  /* ── 그리기 도구 ───────────────────────────────────── */

  const 안전 = (글) => String(글 ?? "").replace(/[&<>"']/g,
    (ㄱ) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ㄱ]);

  const 돈 = (n) => (n === null || n === undefined || Number.isNaN(Number(n)))
    ? "—" : Math.round(Number(n)).toLocaleString("ko-KR") + "원";
  const 부호돈 = (n) => (Number(n) > 0 ? "+" : "") + 돈(n);
  const 퍼센트 = (n, 자리 = 2) => (Number(n) > 0 ? "+" : "") + Number(n).toFixed(자리) + "%";
  // 한국 증시 관례 — 오르면 빨강, 내리면 파랑
  const 색 = (n) => (Number(n) > 0 ? "오름" : Number(n) < 0 ? "내림" : "중립");
  const 지금 = () => new Date().toLocaleTimeString("ko-KR");

  function 알림(자리, 종류, 제목, 설명) {
    $(자리).innerHTML = 종류
      ? `<div class="알림 ${종류 === "순한" ? "순한" : ""}">
           <strong>${제목}</strong>${설명 ? "<br>" + 설명 : ""}
         </div>`
      : "";
  }

  function 탈났다(제목, 설명) {
    $("탈남").innerHTML = `<strong>${제목}</strong><br>${설명}`;
    보이기("탈남", true);
  }

  /* ── 웹훅 ──────────────────────────────────────────── */

  const 바탕주소 = () => (읽기()?.주소 || 기본바탕).replace(/\/+$/, "");

  async function 부르기(길, 몸 = {}) {
    const 연결 = 읽기();
    if (!연결 || !연결.열쇠) throw Object.assign(new Error("열쇠 없음"), { 열쇠없음: true });

    const 답 = await fetch(`${바탕주소()}${길}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 열쇠: 연결.열쇠, ...몸 }),
    });

    if (답.status === 401 || 답.status === 403) {
      throw Object.assign(new Error("열쇠가 맞지 않습니다"), { 열쇠틀림: true });
    }
    if (답.status === 404) {
      throw Object.assign(new Error("아직 안 만들어진 창구"), { 없는창구: true });
    }
    if (!답.ok) throw new Error(`HTTP ${답.status}`);

    const 자료 = await 답.json();
    if (자료 && 자료.오류) throw new Error(자료.오류);
    return 자료;
  }

  const 창구 = (무엇, 인자 = {}) => 부르기("/webhook/sdlab", { 무엇, ...인자 });

  /* 창구가 아직 없으면 예시로 대신하고, 예시라는 것을 밝힌다. */
  async function 창구또는예시(무엇, 예시, 알림자리) {
    try {
      const 자료 = await 창구(무엇);
      알림(알림자리, null);
      return { 자료, 진짜: true };
    } catch (e) {
      if (e.열쇠틀림) throw e;
      알림(알림자리, "경고",
        "예시 자료입니다 — 아직 연결 전입니다.",
        `n8n에 <code>/webhook/sdlab</code> 창구를 아직 안 만들었습니다. ` +
        `아래 숫자는 <b>화면 모양을 보여 주는 가짜</b>이고, 누른 것은 저장되지 않습니다. ` +
        `만드는 법은 <code>docs/대시보드_통합.md</code>에 적어 뒀습니다.`);
      return { 자료: 예시, 진짜: false };
    }
  }

  /* ── 탭 ────────────────────────────────────────────── */

  const 탭들 = ["손익", "승인", "기록", "기준"];
  const 불러온적 = new Set();

  function 탭보이기(이름) {
    탭들.forEach((ㄱ) => {
      보이기(`쪽-${ㄱ}`, ㄱ === 이름);
      const 단추 = document.querySelector(`.탭[data-탭="${ㄱ}"]`);
      단추.setAttribute("aria-selected", String(ㄱ === 이름));
    });
    if (!불러온적.has(이름)) {
      불러온적.add(이름);
      ({ 손익: 손익불러오기, 승인: 승인불러오기, 기록: 기록불러오기, 기준: 기준불러오기 })[이름]();
    }
  }

  document.querySelectorAll(".탭").forEach((단추) => {
    단추.addEventListener("click", () => 탭보이기(단추.dataset.탭));
  });

  /* ── 탭 1 · 지금 손익 ──────────────────────────────── */

  async function 손익불러오기() {
    $("다시").disabled = true;
    $("다시").textContent = "조회 중…";
    try {
      const 자료 = await 부르기("/webhook/muwon-balance");
      알림("손익알림", null);
      보이기("탈남", false);
      손익그리기(자료);
    } catch (e) {
      if (e.열쇠없음) { 첫화면(); return; }
      if (e.열쇠틀림) {
        알림("손익알림", "경고", "열쇠가 맞지 않습니다.",
          "<b>연결 지우기</b>를 누르고 다시 넣어 주세요. 기다린다고 해결되지 않습니다.");
        return;
      }
      알림("손익알림", "경고", "계좌를 조회하지 못했습니다.",
        `${안전(e.message)}<br>증권사가 잠깐 막았을 수 있습니다 — ` +
        `토큰 발급을 자주 하면 막습니다. 1분쯤 뒤 다시 눌러 보세요.`);
    } finally {
      $("다시").disabled = false;
      $("다시").textContent = "🔄 지금 다시 조회";
    }
  }

  function 손익그리기(자료) {
    const 손익 = Number(자료.평가손익 ?? 0);
    const 원가 = Number(자료.원가 ?? 0);
    $("손익").textContent = 부호돈(손익);
    $("손익").className = "값 " + 색(손익);
    $("수익률").textContent = 원가
      ? `원가 ${돈(원가)} 대비 ${퍼센트(손익 / 원가 * 100)}`
      : "보유 종목이 없습니다";
    $("순자산").textContent = 돈(자료.순자산);
    $("현금").textContent = 돈(자료.현금);

    const 줄들 = Array.isArray(자료.종목) ? 자료.종목 : [];
    $("보유몸").innerHTML = 줄들.length === 0
      ? `<tr><td colspan="7" class="빔">보유 종목이 없습니다</td></tr>`
      : 줄들.map((s) => {
          const ㅅ = Number(s.평가손익 ?? 0);
          const ㅇ = Number(s.평균매입가 ?? 0);
          const ㅈ = Number(s.현재가 ?? 0);
          const 률 = ㅇ ? (ㅈ / ㅇ - 1) * 100 : 0;
          const c = 색(ㅅ);
          return `<tr>
            <td>${안전(s.종목 ?? s.symbol ?? "")}</td>
            <td class="${c}">${부호돈(ㅅ)}</td>
            <td class="${c}">${퍼센트(률)}</td>
            <td>${Number(s.수량 ?? 0).toLocaleString("ko-KR")}</td>
            <td>${돈(ㅇ)}</td><td>${돈(ㅈ)}</td>
            <td>${돈(s.평가금액)}</td>
          </tr>`;
        }).join("");

    $("때").textContent = `${지금()} 조회` +
      (자료.조회시각 ? ` · 증권사 기준 ${안전(자료.조회시각)}` : "");
  }

  function 자동맞추기(켤까) {
    if (자동) { clearInterval(자동); 자동 = null; }
    if (켤까) 자동 = setInterval(손익불러오기, 자동간격);
    $("자동전환").textContent = 켤까 ? "자동 갱신 끄기 (1분)" : "자동 갱신 켜기";
  }

  /* ── 탭 2 · 오늘 승인 ──────────────────────────────── */

  const 승인예시 = {
    날짜: new Date().toISOString().slice(0, 10),
    후보: [
      { 종목코드: "042700", 종목명: "한미반도체", 섹터: "반도체", 수량: 3, 예상가: 98500, 승인: "" },
      { 종목코드: "064350", 종목명: "현대로템",   섹터: "방산",   수량: 2, 예상가: 121000, 승인: "Y" },
      { 종목코드: "196170", 종목명: "알테오젠",   섹터: "바이오", 수량: 1, 예상가: 342000, 승인: "N" },
    ],
  };

  async function 승인불러오기() {
    $("승인다시").disabled = true;
    try {
      const { 자료, 진짜 } = await 창구또는예시("승인목록", 승인예시, "승인알림");
      승인그리기(자료, 진짜);
      $("승인때").textContent = `${지금()} 조회` +
        (자료.날짜 ? ` · ${안전(자료.날짜)} 후보` : "");
    } catch (e) {
      알림("승인알림", "경고", "승인 목록을 불러오지 못했습니다.", 안전(e.message));
    } finally {
      $("승인다시").disabled = false;
    }
  }

  function 승인그리기(자료, 진짜) {
    const 후보 = Array.isArray(자료.후보) ? 자료.후보 : [];
    $("승인몸").innerHTML = 후보.length === 0
      ? `<div class="빔">오늘 고른 종목이 없습니다 — 살 만한 신호가 없었다는 뜻입니다</div>`
      : 후보.map((ㅎ) => {
          const 수량 = Number(ㅎ.수량 ?? 0);
          const 정해짐 = ㅎ.승인 === "Y" || ㅎ.승인 === "N";
          return `
          <div class="후보${정해짐 ? " 정해짐" : ""}" data-코드="${안전(ㅎ.종목코드)}">
            <div class="누구">
              <div class="이름">${안전(ㅎ.종목명)}</div>
              <div class="잔글">
                ${안전(ㅎ.종목코드)}${ㅎ.섹터 ? " · " + 안전(ㅎ.섹터) : ""}
                &nbsp;|&nbsp; ${수량.toLocaleString("ko-KR")}주 × ${돈(ㅎ.예상가)}
              </div>
            </div>
            <div class="고르기">
              <button class="작게 고름" data-값="Y" aria-pressed="${ㅎ.승인 === "Y"}"
                ${진짜 ? "" : "disabled"}>산다</button>
              <button class="작게 거름" data-값="N" aria-pressed="${ㅎ.승인 === "N"}"
                ${진짜 ? "" : "disabled"}>안 산다</button>
            </div>
          </div>`;
        }).join("");

    if (!진짜) return;
    $("승인몸").querySelectorAll("button[data-값]").forEach((단추) => {
      단추.addEventListener("click", () => 승인누름(단추));
    });
  }

  async function 승인누름(단추) {
    const 줄 = 단추.closest(".후보");
    const 코드 = 줄.dataset.코드;
    const 켜짐 = 단추.getAttribute("aria-pressed") === "true";
    const 값 = 켜짐 ? "" : 단추.dataset.값;    // 같은 것을 다시 누르면 되돌린다

    const 이전 = [...줄.querySelectorAll("button[data-값]")]
      .map((ㄴ) => [ㄴ, ㄴ.getAttribute("aria-pressed")]);

    // 먼저 화면을 바꾼다 — 누른 게 먹었는지 몰라서 또 누르는 일을 막는다
    줄.querySelectorAll("button[data-값]").forEach((ㄴ) => {
      ㄴ.setAttribute("aria-pressed", String(ㄴ.dataset.값 === 값));
      ㄴ.disabled = true;
    });

    try {
      await 창구("승인", { 종목코드: 코드, 값 });
      줄.classList.toggle("정해짐", 값 !== "");
      $("승인때").textContent = `${지금()} 저장됨`;
    } catch (e) {
      이전.forEach(([ㄴ, ㅅ]) => ㄴ.setAttribute("aria-pressed", ㅅ));
      알림("승인알림", "경고", "저장하지 못했습니다 — 되돌렸습니다.",
        `${안전(e.message)}<br>화면에 보이는 것이 실제와 다르면 안 되므로 원래대로 돌려놨습니다.`);
    } finally {
      줄.querySelectorAll("button[data-값]").forEach((ㄴ) => { ㄴ.disabled = false; });
    }
  }

  /* ── 탭 3 · 기록 ───────────────────────────────────── */

  const 기록예시 = {
    승률: 41.7, 손익비: 1.9, 최대낙폭: -12.4,
    거래: [
      { 종목: "HPSP(403870)", 손익: -2200, 수익률: -2.44, 수량: 2, 산값: 45050, 판값: 43950, 기간: "3일" },
      { 종목: "리노공업(058470)", 손익: 41500, 수익률: 6.10, 수량: 5, 산값: 136000, 판값: 144300, 기간: "11일" },
    ],
  };

  async function 기록불러오기() {
    $("기록다시").disabled = true;
    try {
      const { 자료 } = await 창구또는예시("기록", 기록예시, "기록알림");
      const ㅅ = Number(자료.승률 ?? 0), ㅂ = Number(자료.손익비 ?? 0), ㄴ = Number(자료.최대낙폭 ?? 0);
      $("승률").textContent = ㅅ.toFixed(1) + "%";
      $("손익비").textContent = ㅂ.toFixed(2);
      $("최대낙폭").textContent = ㄴ.toFixed(1) + "%";
      $("최대낙폭").className = "값 " + (ㄴ < 0 ? "내림" : "중립");

      const 거래 = Array.isArray(자료.거래) ? 자료.거래 : [];
      $("기록몸").innerHTML = 거래.length === 0
        ? `<tr><td colspan="7" class="빔">아직 청산까지 끝난 거래가 없습니다</td></tr>`
        : 거래.map((ㄱ) => {
            const c = 색(ㄱ.손익);
            return `<tr>
              <td>${안전(ㄱ.종목)}</td>
              <td class="${c}">${부호돈(ㄱ.손익)}</td>
              <td class="${c}">${퍼센트(ㄱ.수익률)}</td>
              <td>${Number(ㄱ.수량 ?? 0).toLocaleString("ko-KR")}</td>
              <td>${돈(ㄱ.산값)}</td><td>${돈(ㄱ.판값)}</td>
              <td>${안전(ㄱ.기간 || "—")}</td>
            </tr>`;
          }).join("");
      $("기록때").textContent = `${지금()} 조회`;
    } catch (e) {
      알림("기록알림", "경고", "기록을 불러오지 못했습니다.", 안전(e.message));
    } finally {
      $("기록다시").disabled = false;
    }
  }

  /* ── 탭 4 · 전략과 기준 ────────────────────────────── */

  const 기준예시 = {
    매매켜짐: false,
    전략: "volume_surge_5d",
    전략들: [
      { 키: "volume_surge_5d", 이름: "거래량 급증 5일", 설명: "평소보다 거래가 확 늘어난 종목을 산다. 지금 이 저장소에서 5년 내내 플러스인 셋 중 하나." },
      { 키: "golden_cross_20_60", 이름: "골든크로스 20/60", 설명: "단기선이 장기선을 위로 뚫으면 산다. 가장 고전적." },
      { 키: "macd_cross", 이름: "MACD 교차", 설명: "MACD선이 신호선을 뚫으면 산다. 가장 널리 쓰이는 추세 지표." },
      { 키: "ma_rsi_v1", 이름: "이동평균 + RSI", 설명: "추세와 과열도를 같이 본다." },
    ],
    손절: 7, 비중: 20, 동시보유: 5,
  };

  async function 기준불러오기() {
    try {
      const { 자료, 진짜 } = await 창구또는예시("기준", 기준예시, "기준알림");
      기준값 = 자료;
      기준그리기(자료, 진짜);
    } catch (e) {
      알림("기준알림", "경고", "기준을 불러오지 못했습니다.", 안전(e.message));
    }
  }

  function 기준그리기(자료, 진짜) {
    const 켜짐 = Boolean(자료.매매켜짐);
    $("킬값").textContent = 켜짐 ? "매매 켜짐" : "매매 꺼짐";
    $("킬값").className = "값 " + (켜짐 ? "오름" : "중립");
    $("킬곁말").textContent = 켜짐
      ? "새로 사는 것이 돕니다"
      : "새로 사는 것이 전부 멈춰 있습니다. 손절은 그대로 돕니다";
    $("킬전환").textContent = 켜짐 ? "끄기" : "켜기";
    $("킬딱지").textContent = 켜짐 ? "매매 켜짐" : "매매 꺼짐";
    $("킬딱지").className = "딱지 " + (켜짐 ? "켜짐" : "꺼짐");
    보이기("킬딱지", true);

    const 전략들 = Array.isArray(자료.전략들) ? 자료.전략들 : [];
    $("전략").innerHTML = 전략들.map((ㅈ) =>
      `<option value="${안전(ㅈ.키)}" ${ㅈ.키 === 자료.전략 ? "selected" : ""}>${안전(ㅈ.이름)}</option>`
    ).join("");
    전략설명갱신();

    $("손절").value = 자료.손절 ?? "";
    $("비중").value = 자료.비중 ?? "";
    $("동시보유").value = 자료.동시보유 ?? "";

    ["킬전환", "전략", "손절", "비중", "동시보유", "기준저장"].forEach((id) => {
      $(id).disabled = !진짜;
    });
  }

  function 전략설명갱신() {
    const 고른것 = $("전략").value;
    const ㅈ = (기준값?.전략들 || []).find((ㄱ) => ㄱ.키 === 고른것);
    $("전략설명").textContent = ㅈ ? ㅈ.설명 : "";
  }
  $("전략").addEventListener("change", 전략설명갱신);

  $("킬전환").addEventListener("click", async () => {
    const 켤까 = !기준값.매매켜짐;
    const 물음 = 켤까
      ? "매매를 켭니다. 다음 실행부터 승인된 종목을 실제로 삽니다. 계속할까요?"
      : "매매를 끕니다. 새로 사는 것이 전부 멈춥니다(손절은 계속 돕니다). 계속할까요?";
    if (!confirm(물음)) return;

    $("킬전환").disabled = true;
    try {
      await 창구("기준저장", { 바꿀것: { 매매켜짐: 켤까 } });
      기준값.매매켜짐 = 켤까;
      기준그리기(기준값, true);
      $("기준때").textContent = `${지금()} 저장됨`;
    } catch (e) {
      알림("기준알림", "경고", "바꾸지 못했습니다.", 안전(e.message));
    } finally {
      $("킬전환").disabled = false;
    }
  });

  $("기준저장").addEventListener("click", async () => {
    const 바꿀것 = {
      전략: $("전략").value,
      손절: Number($("손절").value),
      비중: Number($("비중").value),
      동시보유: Number($("동시보유").value),
    };
    for (const [이름, 값] of Object.entries(바꿀것)) {
      if (이름 !== "전략" && (!Number.isFinite(값) || 값 <= 0)) {
        알림("기준알림", "경고", `${이름} 값이 이상합니다.`, "0보다 큰 숫자를 넣어 주세요.");
        return;
      }
    }
    $("기준저장").disabled = true;
    try {
      await 창구("기준저장", { 바꿀것 });
      Object.assign(기준값, 바꿀것);
      알림("기준알림", null);
      $("기준때").textContent = `${지금()} 저장됨 · 다음 실행부터 적용됩니다`;
    } catch (e) {
      알림("기준알림", "경고", "저장하지 못했습니다.", 안전(e.message));
    } finally {
      $("기준저장").disabled = false;
    }
  });

  $("기준다시").addEventListener("click", 기준불러오기);
  $("승인다시").addEventListener("click", 승인불러오기);
  $("기록다시").addEventListener("click", 기록불러오기);
  $("다시").addEventListener("click", 손익불러오기);
  $("자동전환").addEventListener("click", () => 자동맞추기(!자동));

  /* ── 첫 화면 ───────────────────────────────────────── */

  function 첫화면() {
    보이기("설정", true);
    보이기("본문", false);
    보이기("킬딱지", false);
  }

  $("저장").addEventListener("click", () => {
    const 열쇠 = $("열쇠").value.trim();
    if (!열쇠) { alert("열쇠를 넣어 주세요."); return; }
    const 외웠나 = 쓰기({ 주소: $("주소").value.trim(), 열쇠 });
    보이기("기억못함", !외웠나);   // 못 외웠어도 길을 막지는 않는다
    보이기("설정", false);
    보이기("본문", true);
    불러온적.clear();
    탭보이기("손익");
  });

  $("연결풀기").addEventListener("click", () => {
    지우기();
    자동맞추기(false);
    불러온적.clear();
    보이기("기억못함", false);
    보이기("탈남", false);
    첫화면();
  });

  자동맞추기(false);
  if (읽기()?.열쇠) {
    보이기("본문", true);
    탭보이기("손익");
  } else {
    첫화면();
  }
})();
