/* 엑셀 내려받기. n8n `LXGroup_원본내려받기`(l1YMWL5bmAZUciMZ)가 하던 일이다.

   화면의 「엑셀 내려받기」가 갈래(경쟁사|지표)와 이름을 보내면, 드라이브의
   마스터 스프레드시트를 찾아 xlsx로 바꿔 돌려준다. 화면 표를 만드는 것이
   아니라 정리 워크플로가 이미 쌓아 둔 원본 파일을 그대로 준다.

   Apps Script 웹 앱은 파일을 그대로 돌려주지 못한다. base64로 담아 JSON
   으로 준다. 마스터 파일이 수십 KB라 문제없다(설계 §4-4). 브라우저 쪽은
   `dashboard/app.js` 대신 hub.html의 `원본받기()`가 이 값을 Blob으로 저장
   하도록 최종 연결 때 고친다. */

//: 지표 갈래에서 받을 수 있는 탭 이름. n8n 코드에 그대로 있던 목록이다.
const 지표탭들 = ['공통', '인터', '판토스', '하우시스', '글라스', '세미콘', 'MMA'];

/** 받은 물음(갈래, 이름)으로 찾을 파일 이름과 폴더를 정한다. 순수 함수.

    받은 이름을 그대로 드라이브에 물으면 아무 파일이나 꺼내 갈 수 있다.
    시트에 적힌 회사와 화면에 있는 탭만 답한다. 목록에 없는 이름은 찾지도
    않는다. n8n의 `찾을 것 정하기` 노드와 같은 규칙이다. */
function 원본찾을것(물음, 회사줄) {
  const 갈래 = String((물음 && 물음.갈래) || '').trim();
  const 이름 = String((물음 && 물음.이름) || '').trim();

  if (갈래 === '지표') {
    if (지표탭들.indexOf(이름) < 0) return { 좋나: false, 왜: '그런 지표 탭이 없습니다.' };
    return { 좋나: true, 파일이름: 이름 + ' 지표 마스터', 폴더: 시장지표폴더ID, 예비이름: 'LX-index-master' };
  }

  if (갈래 === '경쟁사') {
    const 참 = function (v) { return /^(TRUE|true|Y|y|예|1|O|o)$/.test(String(v == null ? '' : v).trim()); };
    const 그 = (회사줄 || []).filter(function (r) {
      return 참(r['사용']) && String(r['회사명'] || '').trim() === 이름;
    })[0];
    if (!그) return { 좋나: false, 왜: '경쟁사 시트에 없는 회사입니다.' };
    const 폴더 = String(그['드라이브폴더'] || '').trim();
    if (!폴더) return { 좋나: false, 왜: '그 회사의 드라이브 폴더가 시트에 적혀 있지 않습니다.' };
    return { 좋나: true, 파일이름: 이름 + ' 실적 마스터', 폴더: 폴더, 예비이름: 'LX-competitor-master' };
  }

  return { 좋나: false, 왜: '갈래는 경쟁사 또는 지표여야 합니다.' };
}

/** 파일 이름에 실을 Content-Disposition 값. RFC 5987 꼴로 우리말 이름을
    싸고, 그것을 못 읽는 브라우저를 위해 아스키 예비 이름을 같이 둔다.
    순수 함수. */
function 원본붙임값(파일이름, 예비이름) {
  return 'attachment; filename="' + 예비이름 + '.xlsx"; filename*=UTF-8\'\'' +
    encodeURIComponent(파일이름 + '.xlsx');
}

/** 실제 드라이브 조회와 내보내기. Apps Script 안에서만 돈다. */
function 원본조회(코드, 인자) {
  const 회사줄 = 탭읽기(주시트ID, 탭이름.경쟁사);
  const 찾을것 = 원본찾을것(인자, 회사줄);
  if (!찾을것.좋나) return { ok: false, error: 찾을것.왜, 상태: 404 };

  const 파일들 = DriveApp.getFolderById(찾을것.폴더).getFilesByName(찾을것.파일이름);
  if (!파일들.hasNext()) {
    return {
      ok: false,
      error: '「' + 찾을것.파일이름 + '」가 드라이브에 아직 없습니다. 정리 워크플로가 한 번 돌고 나면 생깁니다.',
      상태: 404
    };
  }
  const 파일 = 파일들.next();
  const 내보내기url = 'https://www.googleapis.com/drive/v3/files/' + 파일.getId() + '/export?mimeType=' +
    encodeURIComponent('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
  const 응답 = UrlFetchApp.fetch(내보내기url, {
    method: 'get',
    headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() },
    muteHttpExceptions: true
  });
  if (응답.getResponseCode() !== 200) {
    return { ok: false, error: '드라이브에서 xlsx로 내보내지 못했습니다 (' + 응답.getResponseCode() + ')', 상태: 502 };
  }
  return {
    ok: true,
    파일이름: 찾을것.파일이름 + '.xlsx',
    붙임: 원본붙임값(찾을것.파일이름, 찾을것.예비이름),
    갱신: Utilities.formatDate(파일.getLastUpdated(), 'Asia/Seoul', 'yyyy-MM-dd HH:mm:ss'),
    base64: Utilities.base64Encode(응답.getBlob().getBytes())
  };
}
