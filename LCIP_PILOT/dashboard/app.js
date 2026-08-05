// LCIP Pilot Dashboard — 클라이언트 사이드 스크립트
// 표(Tracker 등)는 build_dashboard.py가 서버 사이드에서 이미 정적 HTML로 렌더링한다.
// 이 스크립트는 소송금액 추이 SVG 라인 차트만 그린다 (외부 차트 라이브러리 의존 없음).

(function renderTrendChart() {
  var dataEl = document.getElementById("lcip-trend-data");
  var svg = document.getElementById("lcip-trend-svg");
  if (!dataEl || !svg) return;

  var points;
  try {
    points = JSON.parse(dataEl.textContent || "[]");
  } catch (e) {
    points = [];
  }

  if (!points.length) {
    var emptyText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    emptyText.setAttribute("x", "300");
    emptyText.setAttribute("y", "90");
    emptyText.setAttribute("text-anchor", "middle");
    emptyText.setAttribute("fill", "#5f6368");
    emptyText.setAttribute("font-size", "13");
    emptyText.textContent = "표시할 소송금액 데이터가 아직 없음";
    svg.appendChild(emptyText);
    return;
  }

  var width = 600, height = 180, padding = 24;
  var amounts = points.map(function (p) { return p.amount_usd; });
  var maxAmount = Math.max.apply(null, amounts.concat([1]));
  var minAmount = 0;

  function xForIndex(i) {
    if (points.length === 1) return padding;
    return padding + (i * (width - padding * 2)) / (points.length - 1);
  }
  function yForAmount(v) {
    var ratio = (v - minAmount) / (maxAmount - minAmount || 1);
    return height - padding - ratio * (height - padding * 2);
  }

  var pathD = points
    .map(function (p, i) {
      var x = xForIndex(i);
      var y = yForAmount(p.amount_usd);
      return (i === 0 ? "M" : "L") + x.toFixed(1) + " " + y.toFixed(1);
    })
    .join(" ");

  var svgNS = "http://www.w3.org/2000/svg";

  var path = document.createElementNS(svgNS, "path");
  path.setAttribute("d", pathD);
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", "#0b3d91");
  path.setAttribute("stroke-width", "2");
  svg.appendChild(path);

  points.forEach(function (p, i) {
    var circle = document.createElementNS(svgNS, "circle");
    circle.setAttribute("cx", xForIndex(i).toFixed(1));
    circle.setAttribute("cy", yForAmount(p.amount_usd).toFixed(1));
    circle.setAttribute("r", "3");
    circle.setAttribute("fill", "#0b3d91");
    var title = document.createElementNS(svgNS, "title");
    title.textContent = (p.date || "") + " — " + p.amount_usd.toLocaleString() + " USD";
    circle.appendChild(title);
    svg.appendChild(circle);
  });
})();
