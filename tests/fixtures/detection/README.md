# 정적 HTML 탐지 특징 검증 사례

개발자가 만든 회귀 검증용 합성 데이터입니다. 사용자가 광고 여부를 확정한 정답 데이터셋이나 실제 사이트 정확도 측정 결과가 아닙니다. `cases.json`의 요소 ID와 유형 조합이 정답이며, 테스트는 실제 selector로 그 요소를 다시 찾아 비교합니다.

## 양성: positive.html

| 요소 ID | 기대 특징 | 선정 근거 |
|---|---|---|
| homoglyph | HOMOGLYPH | 전각 라틴 문자 포함 |
| jamo | JAMO | 분리 자모 포함 |
| transparent | TRANSPARENT | 텍스트 색상 transparent |
| opacity-zero | TRANSPARENT | opacity가 정확히 0.00 |
| offscreen / second-offscreen | OFFSCREEN | absolute/fixed와 -9999px 좌표 조합 |
| tiny | OFFSCREEN | font-size 1px, 기존 팀 문서의 예시 |
| display-none | OFFSCREEN | display:none, 기존 팀 문서의 예시 |
| combined | JAMO + TRANSPARENT | 같은 요소의 두 기법 보존 |
| inherited-opacity | TRANSPARENT | 부모 opacity:0 아래의 텍스트 요소 |
| important | TRANSPARENT | !important가 뒤의 일반 opacity 선언보다 우선 |

11개 요소·12개 finding을 기대합니다. 동일 유형 복수 요소가 누락되지 않는지 확인합니다.

## 음성·경계: negative.html

일반 한글/영문, opacity 0.5·0.05, 뒤에서 취소한 opacity:0, 화면 안 absolute, overflow:hidden, position 없는 left 좌표, 일반 font-size, 클래스 이름만 transparent/null인 요소, 자모가 속성에만 있는 요소, 빈 숨김 요소, 스크립트·스타일·주석·template 안의 문자열은 결과 0건을 기대합니다.

## 검증 범위와 남은 기준

현재 정적 판정은 단순 inline 선언만 처리합니다. opacity는 조상 값 0도 확인하지만 color·visibility·font-size 상속과 조상 display:none 전파 전반은 아직 처리하지 않습니다. 외부/내부 스타일시트·레이아웃·뷰포트·동적 DOM의 계산은 하지 않습니다. 복잡한 CSS 구문·변수·미디어 쿼리는 별도 검증 대상입니다.

OFFSCREEN의 음수 좌표는 absolute/fixed 조합의 후보 규칙입니다. 음수라는 사실만으로 실제 전체 요소가 화면 밖임을 보장하지 않습니다. threshold나 viewport 기반 기준은 미확정입니다.

정상 외국어·전각 표현·초성 대화·접근성 은닉 텍스트와 실제 광고를 구분하는 정책은 미확정입니다. 이 사례를 통과해도 is_violation 판정 정확도가 확보됐다고 표현하지 않습니다. 분리된 DOM 노드 사이의 문자 조합, 반복 ID/class·특수문자 selector·iframe 경로는 별도의 위치·통합 테스트로 검증합니다. scripts/test_browser.py의 별도 로컬 사례에서는 실제 Edge의 표·특수문자 ID·반복/중첩 iframe·srcdoc 재식별을 확인했습니다. 이 디렉터리의 모든 사례를 브라우저로 검증한 것은 아닙니다.

실행 절차는 프로젝트 루트 README.md를 따릅니다.
