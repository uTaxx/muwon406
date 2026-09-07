const test = require('node:test');
const assert = require('node:assert/strict');
const { 불러오기, 값 } = require('./gas');

const 파일들 = ['설정.js', '조회_원본.js'];

test('지표 갈래는 정해진 탭 이름만 받는다', () => {
  const g = 불러오기('lxgroup', 파일들);
  const 좋은것 = g.원본찾을것({ 갈래: '지표', 이름: '하우시스' }, []);
  assert.deepEqual(값(좋은것), {
    좋나: true, 파일이름: '하우시스 지표 마스터', 폴더: g.시장지표폴더ID, 예비이름: 'LX-index-master'
  });
  const 나쁜것 = g.원본찾을것({ 갈래: '지표', 이름: '엉뚱' }, []);
  assert.equal(나쁜것.좋나, false);
});

test('경쟁사 갈래는 시트에 사용중으로 등록된 회사만 받는다', () => {
  const g = 불러오기('lxgroup', 파일들);
  const 회사줄 = [
    { 회사명: 'A사', 사용: 'Y', 드라이브폴더: 'folder-a' },
    { 회사명: 'B사', 사용: '', 드라이브폴더: 'folder-b' }
  ];
  assert.deepEqual(값(g.원본찾을것({ 갈래: '경쟁사', 이름: 'A사' }, 회사줄)), {
    좋나: true, 파일이름: 'A사 실적 마스터', 폴더: 'folder-a', 예비이름: 'LX-competitor-master'
  });
  assert.equal(g.원본찾을것({ 갈래: '경쟁사', 이름: 'B사' }, 회사줄).좋나, false);
  assert.equal(g.원본찾을것({ 갈래: '경쟁사', 이름: '없는회사' }, 회사줄).좋나, false);
});

test('드라이브 폴더가 시트에 안 적혀 있으면 거절한다', () => {
  const g = 불러오기('lxgroup', 파일들);
  const 회사줄 = [{ 회사명: 'C사', 사용: 'Y', 드라이브폴더: '' }];
  const 답 = g.원본찾을것({ 갈래: '경쟁사', 이름: 'C사' }, 회사줄);
  assert.equal(답.좋나, false);
  assert.match(답.왜, /드라이브 폴더/);
});

test('갈래가 경쟁사나 지표가 아니면 거절한다', () => {
  const g = 불러오기('lxgroup', 파일들);
  assert.equal(g.원본찾을것({ 갈래: '딜', 이름: 'x' }, []).좋나, false);
  assert.equal(g.원본찾을것({}, []).좋나, false);
});

test('붙임값은 우리말 이름과 아스키 예비 이름을 같이 담는다', () => {
  const g = 불러오기('lxgroup', 파일들);
  const 값값 = g.원본붙임값('하우시스 지표 마스터', 'LX-index-master');
  assert.match(값값, /^attachment; filename="LX-index-master\.xlsx"; filename\*=UTF-8''/);
  assert.ok(값값.indexOf(encodeURIComponent('하우시스 지표 마스터.xlsx')) > 0);
});
