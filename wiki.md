# 공공 웹사이트 불법광고 탐지 도구 — 설계·규격

### 저장본 제출 검토 구현

`backend/app/review.py`와 `scripts/review_submission.py`는 자동 API 정책과 독립적인 오프라인 검토·내보내기를 제공합니다. `submission-review.json`은 capture SHA-256과 검출된 각 특징의 URL/location/technique/원문에 연결됩니다. 최초 판단은 모두 pending입니다. include/exclude에는 검토자·이유·시간대 있는 검토 시각이 필수입니다. 저장 HTML 해시·요소 단일 재식별·원문 일치·전체 검출 목록 보존·선택자 별칭 중복을 검증한 뒤 include만 명시적 true로 Result Builder에 전달합니다. pending/exclude를 false로 변환하지 않습니다.

새 출력 폴더의 result.json과 함께 정확한 검토 원본 사본 및 review-audit.json(수집/검토/결과/현재 코드 해시, 자동 평가, 포함·제외·미검토 수)을 보존합니다. 해시는 변조 확인용이며 전자서명이나 쓰기 방지는 아닙니다. 검토 완료는 재현된 검출 목록에만 한정됩니다. 기존 content-labels.json의 내용 정답·법적 판단 메모를 자동 전환하지 않으며 특징/내용 정확도 지표도 변경하지 않습니다. 검토 UI·검출 누락 요소 추가·내용 후보 검토·디스크 오류 시 여러 파일의 트랜잭션 보장은 아직 없습니다. 실행법은 README를 따릅니다.

## 1. 문서 역할과 목표

공통 목표는 URL에서 시작해 하위 페이지·게시글·댓글·iframe·중첩 iframe을 탐색하고 HOMOGLYPH·JAMO·TRANSPARENT·OFFSCREEN을 탐지하여 정확한 위치·근거·result.json·결과 UI를 제공하는 것입니다.

이 문서는 목표 설계이며 현재 구현 완료를 뜻하지 않습니다. 2026-10-25 업로드된 모집요강 PDF 18쪽을 대조했습니다. 평가·제출 조건은 요구사항정의서의 NFR, 결과 규격은 PDF 붙임4(10~14쪽)의 표와 예시를 기준으로 합니다. 별도 JSON Schema 파일을 제공받은 것은 아니며 PDF 기반 계약 검증과 실제 주최 측 채점은 구분합니다.

| 주제 | 기준 문서 |
|---|---|
| 요구 범위·담당·통과 기준 | [요구사항정의서.md](요구사항정의서.md) |
| 구조·탐지 기준·API·데이터 규격 | [wiki.md](wiki.md) |
| 설치·실행·테스트 절차 | [README.md](README.md) |
| 현재 상태·검증·문제·다음 작업 | [project.md](project.md) |
| 작업·설명·보고 방식 | [project-guide.md](project-guide.md) |

규격은 기준 문서에서 관리하고 다른 문서는 참조합니다. 현재 코드는 현황의 근거이며 요구사항을 대체하지 않습니다. 변경 시 관련 문서·코드·테스트 영향을 함께 검토합니다.

## 2. 역할과 개발 우선순위

사용자 1명이 서비스 구현·통합·탐지 기준·데이터 구성·정확도·오탐·미탐·위치 검증을 모두 담당합니다. 개발·분석은 업무 분류이며 별도 인력의 검수를 기다리는 구조가 아닙니다. 코딩 에이전트는 이 작업을 돕습니다.

우선순위는 필수 요구사항 → 탐색 → 필수 4종 탐지 → 정확한 location → result.json → UI → 정확도·안정성 → 선택 기능입니다. 각 단계에서 실행·검증하며 검증을 마지막으로 미루지 않습니다. 현재 다음 작업은 project.md에서 관리합니다.

## 3. 구조

```text
Frontend → FastAPI → Crawler → Detection Engine
                                  ↓
                         Location 생성·검증
                                  ↓
                         Result Builder → result.json
                                  ↓
                            API → 결과 UI
```

현재 기술은 Python·FastAPI·Uvicorn·httpx·BeautifulSoup4·html5lib·HTML/JavaScript입니다. 수집과 탐지는 HTML5 파서로 동일한 DOM을 구성해 암시적 tbody 등 브라우저의 구조 보정을 반영합니다. 선택적인 동적 수집과 브라우저 검증에는 Playwright와 설치된 Edge를 사용합니다. 특정 프레임워크는 팀의 선택이며 공모전 지정 기술이 아닙니다.

재현 기준은 Windows 11 x64·CPython 3.14.6·pip 26.1.2입니다. requirements.txt는 기본 실행, requirements-browser.txt는 동적 분석, requirements-dev.txt는 전체 검증 환경입니다. 공통 constraints-windows-py314.txt로 직접·하위 의존성 31개를 고정하며 선택 패키지는 필요한 설치 경로에서만 추가합니다. Edge는 외부 설치 앱으로 별도 검증합니다. 설치·기동·테스트 명령은 README를 따릅니다. Python 버전 선택에는 [Pydantic의 Python 3.14 지원 안내](https://pydantic.dev/articles/pydantic-v2-12-release)를 참고했으며 실제 설치 근거는 project.md 17절에서 관리합니다.

현재 파일 배치는 다음과 같습니다. 파일 존재와 정상 동작은 구분합니다.

```text
backend/app/
  __init__.py
  main.py          # API·저장·화면 연결
  crawler.py       # 정적 HTTP 수집·링크·iframe 탐색
  browser.py       # 선택적 Edge 렌더링·실제 프레임 DOM 수집
  detection.py     # 탐지 로직
  content.py       # 도박·성인물 홍보 내용 후보
  location.py      # 고유 selector 생성
  limits.py        # 수집·탐지 공유 시간 예산
  result.py        # 결과 변환·팀 규격 검증
  models.py        # API 모델
frontend/static/index.html
scripts/demo_detection.py
scripts/smoke_test.py
tests/test_detection.py
tests/test_api.py
tests/test_result.py
tests/test_location.py
tests/test_crawler_frames.py
tests/test_location_integration.py
tests/test_limits.py
scripts/test_frontend.cjs
requirements.txt
result.json        # 기존 산출물, 최신 성공의 증거는 아님
```

Result Builder는 탐지와 논리적으로 분리합니다. 별도 파일·폴더로 옮길지는 구현 단계에서 결정합니다. 화면과 결과 파일 경로는 저장소 루트를 기준으로 일관되게 계산해야 합니다.

## 4. 수집 규격

URL 검증·정규화 → Queue → 페이지 수집 → DOM 분석 → 하위 링크·iframe 등록 → 중복 제거 → 탐지 전달 흐름을 따릅니다.

수집 단계에서 다음 정보를 보존해야 합니다. 이는 논리적 정보이며 현재 객체의 확정 스키마가 아닙니다. 모델 변경은 영향 검토 후 진행합니다.

- 입력·요청·리디렉션 후 URL, HTML, 텍스트
- 페이지 종류(page/post/comment/iframe), 부모 페이지 관계
- iframe 내부 URL, 상위 문서에서 시작하는 프레임 요소 selector 경로
- 성공·실패·시간 초과·한도 중단 사유

일반 링크와 프레임 문서를 구분합니다. 현재 top_url·parent_url·frame_path를 보존하며 같은 iframe URL도 삽입 위치마다 별도 컨텍스트로 처리합니다. 정적 모드는 성공/실패 응답을 실행 중 URL별 캐시로 재사용합니다. 상대 src와 정적 srcdoc을 처리하고 순환·깊이 초과·외부/미지원 src를 기록합니다. srcdoc의 링크 기준은 부모 문서 URL입니다. HTML base 요소는 미지원입니다.

동적 모드는 요청마다 새 Edge 컨텍스트를 열고 일반 페이지를 DOMContentLoaded까지 이동한 뒤 기본 500ms를 추가 대기합니다. 기존 개인 프로필은 사용하지 않으며 팝업은 닫고 Service Worker는 차단합니다. JS가 만든 본문·fetch 댓글·링크·iframe과 실행된 srcdoc/about:blank의 DOM을 읽습니다. iframe은 URL로 다시 열지 않고 원래 부모 안의 실제 Frame을 읽으므로 동일 src라도 부모가 수정한 삽입별 상태를 유지합니다. 프레임을 모두 처리한 뒤 다음 일반 페이지로 이동합니다. 스냅샷은 문서별 순차 수집이며 전체 프레임 트리의 원자적 고정본이 아닙니다.

동적 iframe의 현재 URL이 범위 밖이면 제외하며 src가 있으나 아직 about:blank인 프레임은 frame_not_loaded, 분리·접근 실패는 frame_unavailable로 알립니다. HTTP 400 이상 문서는 실패로 처리하고 페이지 JavaScript 예외는 warnings로 반환합니다. 프레임 깊이와 문서 수는 읽는 DOM 컨텍스트를 제한하며 브라우저가 이미 로딩하는 리소스·외부 요청의 차단 또는 총 요청 수 제한을 뜻하지 않습니다. 종료·오류 시 브라우저와 드라이버를 정리합니다.

사용 API의 기준은 Playwright 공식 문서의 [Page.goto](https://playwright.dev/python/docs/api/class-page#page-goto), [Frame.content](https://playwright.dev/python/docs/api/class-frame#frame-content), [BrowserType.launch](https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch)를 참조합니다.

일반 링크는 동일 호스트 범위를 기본으로 합니다. scheme·port·서브도메인·리디렉션·외부 iframe의 세부 허용 정책은 미확정입니다. 현재 구현은 netloc가 같은 링크와 iframe src만 허용하며 외부 iframe 지원 완료를 뜻하지 않습니다.

상대 URL·fragment·query·중복 요청·리디렉션·비HTTP 링크·실패 재시도를 처리합니다. 현재 기본 한도는 다음과 같습니다. 평가 조건·실제 사이트 검증 전의 구현값이며 공식 수치가 아닙니다.

| 한도 | 기본값·의미 |
|---|---|
| max_pages | API 8, 실패를 포함한 문서 컨텍스트 수. 반복 iframe도 위치별 계산 |
| max_depth | 2, 시작 페이지 0에서 링크 이동마다 1 증가 |
| max_iframe_depth | 3, 프레임 경계 수. 링크 깊이와 별도 |
| total_timeout_sec | 60초, 수집·탐지 공유 시간 예산 |
| HTTP timeout | 최대 10초, 요청 시작 시 남은 공유 시간보다 길지 않게 설정 |

프레임·srcdoc에 들어가도 링크 깊이는 유지하고, 프레임 안의 링크를 따라가면 1 증가합니다. 같은 링크 깊이의 프레임을 먼저 확장해 깊이가 더 큰 경로가 짧은 경로를 가리지 않도록 합니다. 깊이 초과 링크·문서 수·프레임 깊이·시간 중단 사유를 구분합니다.

공유 시간은 monotonic clock으로 측정하고 요청 시작·응답 스트림 청크·수집 반복·탐지 요소 처리 사이에서 확인합니다. 이미 진행 중인 I/O·파싱·selector 탐색을 즉시 중단하는 강제 종료가 아니므로 제한을 일부 초과할 수 있습니다. 최종 결과 변환·직렬화·파일 저장은 중단 결과를 돌려주기 위한 마무리이며 이 예산으로 강제 종료하지 않습니다. 공식 30분 조건의 엄격한 준수를 검증한 기능으로 취급하지 않습니다.

HTML에 존재하는 게시글·댓글과 JS 실행·추가 요청이 필요한 콘텐츠를 구분해 검증합니다. 동적 모드는 제한된 관찰 시점까지 생성된 DOM·계산 스타일을 지원합니다. 자동 스크롤·클릭·로그인·Shadow DOM은 미지원입니다. DOM 수집 후 변동이 있으면 selector 재식별이 실패할 수 있으며 실제 사이트 정확도는 별도 검증합니다. 개별 프레임 실패가 전체 탐색을 중단시키지 않게 하되 전체 수집 실패는 정상 0건과 구분합니다.

## 5. 탐지 기준

4종은 독립적으로 판정하고 결과를 통합합니다. 같은 요소의 복수 기법은 기법별 finding으로, 같은 유형의 서로 다른 요소도 각각 보존합니다.

| 유형 | 분석 대상 | 정상·경계 사례 |
|---|---|---|
| HOMOGLYPH | Unicode·code point·정규화·유사 문자 위장 | 정상 외국어·전각 문자 |
| JAMO | 음절·초중종성·분리 자모·정규화 | 정상 자모·초성 표현 |
| TRANSPARENT | 텍스트·색상·opacity·배경·상속·computed style | 숨김 UI·접근성 텍스트 |
| OFFSCREEN | 위치·크기·font-size·display·layout·표시 상태 | 정상 absolute·overflow·접근성 텍스트 |

PDF 5쪽은 font-size 0~1px, position:absolute; left:-9999px, display:none을 OFFSCREEN 예시로 명시합니다. TRANSPARENT에는 배경색과 같은 색, opacity:0, color:transparent를 제시합니다. 이 예시를 실제 DOM·스타일 검증으로 구현해야 하며 정상 UI나 광고 여부는 별도 확인합니다. 겹치는 속성만으로 두 유형을 모두 확정하지 않습니다.

위장·은닉 특징 발견과 광고 판정은 구분합니다. policy.py의 feature-content-policy-v1은 특징의 실제 원문 구간이 관련 홍보 주제/유도 표현 구간과 겹치는 경우만 자동 제출 후보로 선택합니다. 이것은 구현 정책이며 PDF가 키워드·임계값을 지정한 것은 아닙니다. 규칙상 true와 법적 위반 확정을 동일시하지 않으며 고정 feature confidence도 측정 정확도가 아닙니다. 실제 판정 정확도는 별도 검수가 필요합니다.

2026-10-25 사용자 설명에 따라 도박·성인물 후보 판별을 구현했고 이후 PDF 1·5쪽에서도 범위를 확인했습니다. 실제 gen.go.kr 일반 표시 글의 공백에 대응한 v1·문장 문맥 v2를 거쳐 현재 content-rules-v3입니다. 표현/은닉 4종과 내용 범주는 독립적입니다. content_candidates는 검수용이고 result_extra.json은 PDF 13쪽의 ETC+extra_finding 형식입니다. 일반 표시 후보를 필수 4종으로 임의 분류하지 않으며 후보 부재도 광고 부재를 보장하지 않습니다.

v3는 텍스트를 가장 가까운 블록에 귀속해 inline 조각만 합치고 문단은 섞지 않습니다. 문장 경계와 주제 앞 45/뒤 100자의 규칙은 유지하며 도메인 내부 마침표를 경계로 만들지 않습니다. textnorm.py는 NFKC·현대 한글/호환 자모 재조합·제한된 키릴 닮은꼴→Latin 매핑·casefold·공백/일부 zero-width 제거를 판별용으로 적용합니다. 정규화 문자마다 원문 범위를 추적해 원문 자체는 바꾸지 않습니다. 카지노·성인물 등의 주제와 가입/보너스/시청/바로가기 등의 단서가 함께 필요합니다. PDF 예시의 mega-BET·슬롯 체험·먹튀검증/텔레그램 유도도 검증합니다. 예방교육·단속 보도·광고 신고/삭제 요청·피해상담 등 명시적 보호 문맥은 제외합니다. 전체 Unicode 위장·모든 자모 조합·은어·의미 이해를 지원하는 것은 아닙니다.

후보 단위는 URL+location+category이며 GAMBLING/ADULT_CONTENT로 분류합니다. selector·원문·근거 문맥·matched_terms·policy_version·needs_review 상태와 feature_links(location+technique)를 보존합니다. HOMOGLYPH/JAMO는 실제 의심 문자 구간, CSS 기법은 해당 요소의 직접 텍스트 중 공백/제거 대상 zero-width를 제외한 구간이 홍보 주제/유도 표현과 겹쳐야 연결합니다. URL·프레임·블록·문장을 넘겨 무관한 특징을 연결하지 않으며 techniques는 이 링크에서 계산합니다. 문단 안 별도 숨김 메뉴, 같은 요소의 전각 인사말/외국어 접두사, 숨김 zero-width만으로 홍보를 위장했다고 간주하지 않습니다. 후보 자체는 confidence나 is_violation 없이 검토 상태를 유지합니다.

정책은 모든 특징을 included 또는 needs_review로 평가하고 이유·관련 범주를 API에 남깁니다. included만 result.json에 explicit is_violation=true로 전달하며 근거 부족은 false로 확정하거나 제출하지 않습니다. 미탐·인용 문맥 오탐·어휘 밖 광고의 검토 잔류 위험이 있으며 이 규칙은 실제 정확도 검증을 대체하지 않습니다. 정상 숨김 UI·외국어·초성도 특징 자체는 화면과 feature 평가에 남습니다.

화면용 evidence에는 의심 문자·스타일·판정 이유를 설명합니다. 제출 evidence_text에는 별도 source_text의 정규화 전 DOM 텍스트를 설명 접두사나 길이 제한 없이 저장합니다(PDF 11쪽). HTML 마크업 문자열이 아니라 HTML 엔티티가 해석된 텍스트이며 공백·줄바꿈·전각·자모·zero-width 문자를 보존합니다. 필수 4종은 탐지 요소의 직접 텍스트 노드, 내용 후보는 같은 블록에 귀속된 텍스트 노드의 원래 순서로 수집합니다. 동적 모드는 관찰 시점의 DOM 원문입니다.

현재 정적 탐지에서는 직접 텍스트를 가진 요소를 대상으로 하고 script·style·head·template·noscript·주석·속성 문자열은 텍스트 판정에서 제외합니다. 유형별 첫 일치에서 멈추지 않고 모든 일치를 반환합니다. 근거에 해당 요소의 원문을 포함합니다.

단순 inline 선언의 중복·!important 우선순위를 처리하며 opacity는 정확히 0인 경우와 조상 opacity:0을 확인합니다. 클래스 이름만으로 투명 여부를 판정하지 않습니다. OFFSCREEN 후보는 display:none, 0~1px 글꼴, absolute/fixed와 음수 left/top(px) 조합입니다. 단독 absolute·overflow:hidden은 제외합니다. 음수 좌표의 실제 화면 이탈 여부와 유형 분류는 추가 검증이 필요합니다.

위 inline 규칙은 정적 모드 및 스타일 관찰값 없는 과거 저장본의 기준입니다. 새 동적 모드는 rendered_snapshot.js의 단일 동기 호출에서 HTML과 직접 텍스트를 가진 HTML 요소별 관찰값을 함께 수집합니다. 문서 안 요소는 순차 관찰하며 프레임 트리 전체의 동일 시점 고정이나 애니메이션·이후 DOM 변경을 보장하지 않습니다. DOM을 수정하지 않고 구조 선택자·원문·계산 스타일·좌표를 저장합니다. 처리 반복에 공유 시간 예산을 적용하되 브라우저 내부 연산의 즉시 강제 종료는 아닙니다. API 사용 기준은 [getComputedStyle](https://developer.mozilla.org/en-US/docs/Web/API/Window/getComputedStyle)과 [getBoundingClientRect](https://developer.mozilla.org/en-US/docs/Web/API/Element/getBoundingClientRect) 문서를 참조합니다.

rendered.py의 rendered-style-rules-v1은 zero opacity·계산된 visibility·투명 글자·동일 불투명 RGB 단색 배경을 TRANSPARENT로, 조상 포함 display:none·상속된 0~1px 글꼴·양의 크기를 가진 요소의 전체가 문서 왼쪽/위쪽 음수 영역에 있는 배치를 OFFSCREEN으로 판단합니다. 좌표에 스크롤을 더해 문서 기준으로 비교하며 일반적인 스크롤 아래 콘텐츠와 일부 보이는 음수 배치는 제외합니다. 그림자/윤곽선이 있으면 글자색만으로 투명 판정하지 않습니다. 관찰값이 있으면 CSS 기법에서 inline 후보보다 우선하여 !important·실제 레이아웃을 반영합니다. 관찰 대상이 아닌 요소에는 CSS 후보를 임의 보충하지 않습니다.

배경 이미지·그라데이션·반투명 합성·표준 RGB 이외 색상 계산은 추측하지 않습니다. 가림·clip·양의 방향 화면 밖·SVG·가상 요소·Shadow DOM·프레임 경계 밖 iframe 요소의 은닉 전파는 미지원입니다. HOMOGLYPH/JAMO와 노드 간 문자 조합 범위는 이번 작업에서 바꾸지 않았습니다. 합성 특징 검증은 광고 여부를 확정한 정답이 아닙니다.

관찰값은 capture.json의 문서별 rendered_style(schema_version=1)에 보존합니다. 현재 parser가 선택자를 정확히 한 요소로 해석하고 원문이 일치하는지 검증하며 중복·잘못된 경로·원문 불일치는 평가를 거부합니다. 저장 HTML과 관찰값이 함께 labels의 capture 해시에 연결됩니다. 보고서는 렌더링 판정 코드 해시·정책 버전 및 observation_basis를 기록합니다. 과거 browser 캡처라도 관찰값이 없으면 정적 문서 수로 집계해 현재 computed style 평가로 오해하지 않게 합니다. 정적 사례의 한계는 [사례 설명](tests/fixtures/detection/README.md)을 따릅니다.

## 6. URL·location 규격

PDF 11~12쪽의 위치·채점 원칙을 적용합니다.

- url: 일반 요소는 분석 페이지 URL. iframe 결과는 프레임 경로를 다시 따라갈 수 있는 최상위 페이지 URL을 기준으로 합니다. 내부 프레임 URL은 별도 내부 정보로 보존합니다.
- location: 해당 url에서 시작하는 CSS selector 경로. URL 접두사를 붙이지 않습니다.
- iframe 경계는 `>>>`로 구분합니다. 이는 경로 표기이며 표준 CSS selector 하나가 아닙니다. 각 문서에서 selector를 따로 평가합니다.

```text
일반: div.notice-board > span.visually-hidden
반복 요소: table > tbody > tr:nth-of-type(7) > td:nth-of-type(2)
iframe: iframe#widget >>> div.wrap > span.hidden-link
중첩: iframe#outer >>> iframe#inner >>> span.ad
```

각 selector는 해당 문서에서 대상 하나를 식별해야 합니다. PDF는 태그/클래스·순서·큰따옴표 속성·iframe 절대 src 표기를 안내하지만 다른 형식도 같은 요소를 정확히 가리키면 정답으로 인정합니다. 현재는 원본 DOM에 맞는 ID/클래스/순서 선택자로 프레임을 식별합니다. 상대 src를 절대 주소로 바꿔 원본 DOM과 맞지 않는 선택자를 만들지 않습니다. 두 요소 이상을 가리키는 선택자는 오답이므로 고유성을 검증합니다.

기존 `URL::selector`는 폐기한 과거 형식입니다. 일반 요소는 selector, 프레임 요소는 frame_path와 내부 selector를 ` >>> `로 연결합니다. PDF 13쪽 예시처럼 프레임을 포함한 웹페이지 URL에서 위치 경로를 따라갑니다.

Detection Unit은 `(url + location + technique)`입니다. 같은 조합은 중복 제거하고 서로 다른 요소·프레임 삽입 위치·기법은 유지합니다.

PDF 12쪽에 따라 평가·제출 중복 비교에서는 http/https·URL 끝 슬래시·fragment 차이를 무시하고 쿼리 항목 순서를 정렬합니다. 쿼리 값과 중복 항목은 보존합니다. 이 규칙은 comparison.py에서 공유하며 HTTP 수집 주소나 표시 URL을 강제 변경하지 않습니다. 정답 검수는 동등 URL과 같은 요소를 가리키는 선택자를 함께 처리합니다. 동등 URL로 저장된 문서 내용이 서로 다르면 모호성을 피하기 위해 평가를 거부합니다.

## 7. 결과 규격

PDF 10~14쪽의 표와 예시에 따른 출력입니다. 표준 문서는 PDF이며 아래 모델을 별도의 공식 JSON Schema 파일이라고 부르지 않습니다.

```json
{
  "meta": {
    "topic": "TOPIC",
    "entry_url": "https://example.com",
    "started_at": "2026-10-23T00:00:00+00:00",
    "finished_at": "2026-10-23T00:00:01+00:00",
    "elapsed_sec": 1.0,
    "tool_version": "YearDream-0.1.0"
  },
  "findings": [
    {
      "id": "finding-1",
      "url": "https://example.com",
      "is_violation": true,
      "location": "div#promo",
      "evidence_text": "무료 슬롯 체험 바로가기",
      "technique": "OFFSCREEN"
    }
  ]
}
```

| 필드 | 자료형·의미 |
|---|---|
| meta.topic | PDF 표·예시의 TOPIC 문자열 |
| meta.entry_url | 문자열, 시작 URL |
| meta.started_at / finished_at | 시간대 포함 ISO 8601 문자열 |
| meta.elapsed_sec | 0 이상 숫자, 실행 경과 시간 |
| meta.tool_version | 선택 문자열 |
| findings | 배열, 정상 분석 후 0건이면 빈 배열 |
| finding.id | 결과 안에서 고유한 문자열 |
| finding.url / location | 문자열, 6절의 페이지·요소 경로 |
| finding.is_violation | Boolean, 정의한 기준에 따른 위반 여부 |
| finding.evidence_text | 정규화 전 원문 텍스트, 설명 접두사·자르기 없음 |
| finding.technique | HOMOGLYPH / JAMO / TRANSPARENT / OFFSCREEN |

PDF는 is_violation Boolean을 필수로 두고 true 예시를 제시하지만 상세 키워드·정상/의심 포함 정책은 명시하지 않습니다. 현재 자동 제출 후보 선택은 5절의 구현 정책을 적용하며 자체 검증과 주최 측 정답 판정을 구분합니다.

Result Builder의 판정값 누락 시 true로 바꾸던 호환 동작은 제거했습니다. 내부 직접 호출도 source_text와 명시적 Boolean is_violation이 필요하며 누락/잘못된 자료형은 거부합니다. API는 선택된 후보만 true로 전달하고 미판정 특징은 제외합니다. 별도 내부 호출에서 명시한 false는 보존하지만 자동 정책이 근거 부족을 정상으로 변환하지는 않습니다. location은 6절을 따릅니다.

필수 필드·자료형·허용 기법·ID·중복·시간·빈 배열을 검증합니다. 두 결과 모두 UTF-8 BOM 없이 meta+findings 두 키와 단일 findings 배열로 저장합니다. 기본 위치는 프로젝트 루트의 result.json 및 result_extra.json입니다. PDF는 구동 파일 폴더를 원칙으로 하며 다른 경로면 사용설명서 첫 장에 파일별 경로를 안내합니다. 배포용 구동 파일·동시 요청 및 두 파일 저장 중 디스크 오류의 트랜잭션 보장은 아직 미구현입니다.

result_extra.json은 같은 실행 meta를 사용하며 id/url/location/evidence_text/technique/extra_finding을 갖습니다. technique은 ETC이고 extra_finding은 GAMBLING_PROMOTION_CANDIDATE 또는 ADULT_CONTENT_PROMOTION_CANDIDATE입니다. PDF 13쪽 추가 결과 예시처럼 is_violation을 자동 추가하지 않습니다. 이 파일은 본심사 참고용 추가 제안이며 필수 4종 성능을 대체하지 않습니다. 성공한 0건 분석에서도 빈 findings로 저장하며 수집 실패/분석 전 시간 초과 시 기존 파일을 보존합니다.

PDF 12쪽에 따라 정답 핵심은 URL+실제 위치+기법이고 evidence_text는 필수 본심사 참고자료입니다. 필드 누락·스키마 미준수 항목은 오답/채점 제외 대상이며 파일 파싱 불가는 해당 회차 성능 점수 0점입니다. 제출 파일 미생성 등은 평가 제외 가능성이 있습니다. 자체 테스트 통과를 주최 측 채점 통과로 표현하지 않습니다.

## 8. API와 UI

현재 복구 대상으로 유지할 경로입니다. 정상 실행 여부는 project.md에서 관리합니다.

| 경로 | 역할 |
|---|---|
| GET / | UI 제공 |
| GET /api/health | 서버 생존 확인 |
| POST /api/analyze | URL 분석·결과 반환 |

요청의 필수값은 `{"url": "https://example.com"}`입니다. 선택값 max_depth는 0~20 정수(기본 2), total_timeout_sec는 0 초과~1800 이하 유한 숫자(기본 60), collection_mode는 static(기본)/browser, render_wait_ms는 0~5000 정수(기본 500)입니다. 이 상한은 API 개발 기준이며 공모전 요구값이 아닙니다. 잘못된 값은 HTTP 422로 거부합니다. 응답 모델은 url, collection_mode, page_title, crawled_pages, findings, content_candidates, content_policy_version, result_json, result_extra_json, warnings입니다. API finding의 technique/selector/location/url/evidence/confidence와 제출용 finding은 구분합니다. Result Builder는 내부 source_text를 제출 evidence_text로 변환하며 화면 설명 evidence를 제출 원문에 섞지 않습니다.

응답은 submission_policy_version과 각 finding의 submission_status/submission_reason/submission_categories를 포함합니다. 화면은 위장·은닉 특징, 내용 후보, 선택된 4종 제출 후보와 검토 대상을 구분합니다. result_json은 선택된 후보만 포함하므로 API finding 수와 다를 수 있습니다.

한 페이지는 4종 특징·내용 후보·제출 후보 평가 세 단계가 모두 끝나야 완료입니다. 공유 Deadline이 중간 만료되면 해당 페이지의 결과를 함께 버립니다. 앞서 완료한 페이지가 없으면 504와 기존 두 파일 보존, 있으면 그 결과와 부분 경고를 반환합니다.

browser 모드는 Playwright·Edge가 필요하며 시작 실패는 HTTP 503입니다. 정적으로 자동 전환하지 않습니다. 브라우저 시작·이동·추가 대기·수집·탐지는 동일 Deadline을 사용합니다. 이동 timeout은 남은 시간과 10초 중 작은 값이며 대기도 남은 시간으로 제한합니다. 드라이버 시작·DOM 직렬화·종료 등 모든 작업을 즉시 강제 종료하는 기능은 아닙니다. 오류 응답은 기존 결과 파일을 보존합니다. collection_mode는 API·UI 안내이며 제출 JSON에는 추가하지 않습니다.

crawled_pages는 수집 성공한 문서 URL의 중복 없는 목록입니다. srcdoc과 동일 URL의 여러 프레임은 위치별 finding으로 구분됩니다. 전체 수집 실패는 HTTP 502로 반환하고 기존 결과 파일을 덮어쓰지 않습니다. 일부 실패·프레임 제외·컨텍스트 한도 도달은 warnings로 반환하며 UI에도 표시합니다. warnings는 API 안내 필드이고 제출 JSON에 추가하지 않습니다. 따라서 파일만으로 분석 범위 완전성을 확인하는 정책은 추후 검토합니다.

링크 깊이·시간 제한도 warnings로 안내합니다. 수집·탐지 중 시간 초과로 분석을 끝낸 페이지가 하나도 없으면 HTTP 504이고 기존 파일을 보존합니다. 완료한 페이지가 있으면 그 결과를 반환하되 나머지 미분석을 명시합니다. 분석 도중 중단된 페이지의 중간 finding은 포함하지 않습니다. crawled_pages는 수집 성공 목록이며 모든 문서의 탐지 완료를 뜻하지 않습니다.

포트와 실행 명령은 README를 따릅니다. UI는 같은 서버의 `/api/analyze`를 상대 경로로 호출합니다.

UI 목표는 URL 입력·실행·상태 안내·전체/유형별 건수·URL·location·근거·필터·JSON 다운로드입니다. 응답 원본을 보존해 필터링합니다. Frontend에 수집·탐지 로직을 넣지 않습니다.

JSON 다운로드는 현재 화면의 마지막 성공 응답에 담긴 result_json 전체를 사용합니다. 유형 필터는 다운로드 내용에 영향을 주지 않습니다. Blob(application/json;charset=utf-8)과 임시 링크로 result.json을 저장하고 링크·object URL을 정리합니다. UTF-8 BOM 없이 직렬화하며 API·서버 파일과의 동등성은 파싱한 JSON 값 기준입니다. 기본/동적·부분 분석·0건 모두 저장할 수 있습니다. 부분 분석의 warnings는 기존 제출 규격에 추가하지 않으며 화면 안내를 유지합니다.

UI는 4종 특징 수와 내용 후보 수를 따로 표시합니다. 범주 필터는 내용 후보를, 기법 필터는 해당 특징과 그 특징이 연결된 후보를 표시합니다. 별도 ‘광고 후보 다운로드’는 content-candidates.json으로 purpose=content_candidate_review·규칙 버전·meta·수집 방식·warnings·전체 candidates를 저장합니다. ‘추가 탐지 결과 다운로드’는 마지막 응답의 result_extra_json을 result_extra.json으로 저장합니다. 세 다운로드 모두 필터에 독립적이며 새 분석·실패·빈 URL 제출 때 비활성화합니다. 내용 후보를 법적 위반 확정으로 취급하지 않습니다.

분석 전과 새 분석 시작 시 다운로드를 비활성화하고 성공 응답 이후에만 활성화합니다. 실패·빈 URL 제출 후에는 과거 응답으로 내려받지 못하게 합니다. 공유 서버 파일을 다시 가져오는 경로는 추가하지 않으며 다른 요청이 파일을 덮어써도 현재 화면의 응답을 유지합니다.

Job 기반 `/api/detection`, `/api/detection/{id}`, `/api/detection/{id}/status`, `/api/detection/{id}/result`, `/api/detection/{id}/download`는 이전 문서의 향후 제안이며 도입 미확정입니다. 현재 API가 아닙니다. queued/running/completed/failed/timeout은 목표 상태 의미이며 기본 안내가 반드시 상태 API를 요구하지는 않습니다.

## 9. 검증·변경 원칙

요구사항 ID에 대응하는 정답 사례로 검증합니다.

- 수집: URL·중복·실패·시간·한도·프레임 관계·동적 콘텐츠.
- 탐지: 유형별 정상·탐지·경계 사례, 복수 요소·기법, 오탐·미탐.
- 위치: 실제 원본 요소 재식별, selector 고유성, 중첩 iframe, 동일 src 복수 삽입.
- 결과: 필드·자료형·중복·빈 결과·실패 구분·UTF-8 BOM 없음.
- 통합/UI: URL부터 파일·화면·필터 전체 복귀·다운로드 일치.
- 평가: 대조한 PDF 조건에 따른 요구사항정의서 NFR의 실제 대상 환경·배포 검증.

작은 기능 → 실행 → 예상 결과·회귀 확인 → 진행 기록 갱신 순으로 개발합니다. 기존 코드를 검토 없이 삭제하거나 프로젝트 전체를 재생성하지 않습니다. Git 기록 여부와 기능 검증은 구분합니다.

사이트 검증 도구는 수집(capture)과 정답 비교(evaluate)를 분리합니다. capture는 원본/렌더링 HTML과 컨텍스트·시각·설정·해시·코드/패키지 버전·탐지 후보·수집 경고를 기록하고 후보 정답은 미검토로 생성합니다. evaluate는 저장된 HTML을 현재 탐지기로 다시 분석합니다. HTML 및 capture 해시로 입력을 확인하고, 정답 selector를 해당 문서·프레임의 실제 요소로 재식별합니다. 같은 요소를 가리키는 다른 selector는 같은 정답으로 처리합니다.

capture/evaluate는 내용 후보·규칙 버전·후보 수도 별도 기록합니다. labels와 metrics는 기존 4종 특징만 평가하며 metrics_purpose=four_technique_features_only로 명시합니다. 내용 후보의 정확도를 이 지표로 대체하지 않습니다.

정답 기준 초안은 문자 위장과 정상 외국어, 분리형 한글 위장과 정상 초성, 텍스트의 실제 은닉과 정상 표시, 화면 이탈과 정상 배치를 구분하는 것입니다. 접근성 텍스트·외국어·초성·작은 글꼴·display:none 등의 예외와 유형 경계는 사용자 기준으로 확정하고 labels.json의 policy에 버전을 기록합니다. 이 초안은 공식 위반 판정 기준이 아닙니다. 확정 전에는 expected=null·reviewed=false를 유지합니다.

평가 단위는 최상위 URL+실제 요소 위치+기법입니다. 검토된 양성의 탐지/누락을 TP/FN, 정상의 탐지/미탐지를 FP/TN으로 기록합니다. 부분 검수는 미검토 탐지를 unknown으로 남기고 지표를 계산하지 않습니다. complete=true는 저장된 문서의 모든 양성 특징 검수 선언이며 정답 밖 탐지는 FP입니다. 명시한 policy·전 항목의 reviewed/Boolean 정답/근거가 필요합니다. feature/content 지표는 제출 선택 정확도나 전체 사이트 정확도가 아닙니다. capture/evaluate는 submission_assessments·정책 버전과 코드/정규화 해시도 기록하며 submission_candidate_count는 단순 선택 건수입니다. 고정 confidence나 자동 true를 정답으로 사용하지 않습니다.

## 10. 미확정 사항·선택 기능

PDF 원문·출력 표/예시는 대조했습니다. 판정 정책·자체 정확도 목표, 실제 사이트 동적 수집 범위, 호스트/iframe 정책·탐색 한도, 다른 Python/OS 호환성, 배포 구동 파일과 설치 방식은 추가 검증이 필요합니다. PDF는 Python/FastAPI/브라우저 종류를 지정하지 않습니다.

추가 탐지·RAG·LLM·LangChain·LangGraph·DB·이력·고급 UI는 핵심 안정화 이후 검토합니다. 필요성이 확인되지 않은 기술을 먼저 도입하지 않습니다.
## 내용 후보 평가 도구 추가 (2026-10-25)

`scripts/validate_site.py evaluate RUN --kind content`는 `content-labels.json`을 사용하고 `content-report.json`으로 저장합니다. 기본 evaluate는 기존 4종 기법 평가입니다. 새 capture는 두 정답 초안을 모두 생성하며, 이전 저장본에는 `init-content-labels RUN`으로 내용 정답을 추가합니다. 기존 파일 덮어쓰기는 거부합니다.

내용 검수 단위는 최상위 URL + 프레임을 포함한 텍스트 블록 위치 + GAMBLING/ADULT_CONTENT 범주입니다. 후보만 확인하지 말고 미탐 블록과 정상 사례도 정답에 추가해야 합니다. `complete: false`에서는 검수된 TP/FP/FN/TN만 집계하고 지표는 null입니다. 저장 문서 전체의 양성 정답을 검수하고 기준 policy를 기록했을 때만 complete를 true로 설정합니다. 전체 검수에서는 양성 정답 밖 후보를 FP로 계산합니다.

원본 HTML·capture 해시와 정답 연결, 선택자 유일성, 동등한 선택자의 중복을 검사합니다. 보고서는 정답 및 평가 코드 해시도 기록합니다. 법적 판단 메모는 선택적 violation_verdict/reviewer/verdict_reason으로 보존하며 내용 존재 평가와 분리합니다. 기본은 미판정이고 API나 제출 스키마에 자동 반영하지 않습니다.

실제 저장본 본문 일부 검수: 107 GAMBLING TP 1, 151 ADULT_CONTENT TP 1, 454470 예방교육 본문 두 범주 TN 2. 세 저장본 모두 부분 검수여서 전체 지표는 null입니다. 원본 및 검수 파일은 Git에서 제외된 .validation/에 보관합니다. 사용 예시와 상세 필드는 README의 내용 후보 평가 절을 참고합니다.
