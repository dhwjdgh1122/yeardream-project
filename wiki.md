# 공공 웹사이트 불법광고 탐지 도구 — 설계·규격

## 1. 문서 역할과 목표

이 문서는 **현재 구현의 아키텍처·수집/탐지·API·location·결과 데이터 계약과 향후 확장 방향**을 설명합니다. 대상 독자는 구현 구조와 기술적 동작을 확인하는 개발자·검토자입니다. 기술이 구현되어 있다는 설명은 실사이트 전수 검증이나 정확도 보장이 아닙니다.

공식 요구·평가/제출 조건과 기능별 입력/처리/출력/예외는 [요구사항정의서](요구사항정의서.md), 설치·실행·도구 명령은 [README](README.md), 현재 검사 결과·사용자 확인·알려진 문제는 [project.md](project.md), 작업 방식은 [project-guide.md](project-guide.md)를 따릅니다. 화면 배치·상태별 제어는 [화면설계서](docs/SCREEN_DESIGN.md), 물리 테이블·키·ERD는 [DB 설계서](docs/DATABASE_DESIGN.md)가 기준이며 여기서는 요약과 연결만 제공합니다.

공통 목표는 입력 URL에서 하위 페이지·게시글·댓글·iframe을 탐색해 필수4종 특징과 관련 홍보를 구분하고 정확한 위치·원문·결과 파일을 제공하는 것입니다. 현재 제품은 로컬 단일 사용자 도구이며 외부 AI API·생성 모델·RAG는 사용하지 않습니다. PDF의 공식 표/예시와 자체 구현 정책은 구분합니다. 별도 공식 JSON Schema 파일이 제공된 것으로 표현하지 않습니다.

## 2. 역할과 개발 우선순위

사용자1명이 구현·분석·판정 기준·정답 검수를 담당하고 에이전트가 돕습니다. 작업 승인·변경 범위·검증 선택·설명 방식은 project-guide.md를, 현재 남은 일은 project.md를 따릅니다. 아래 기술 규격은 다음 개발을 자동 승인하는 목록이 아닙니다.

## 3. 구조

```text
브라우저 UI → FastAPI /api/jobs → 단일 분석 작업
                                  ↓
                         수집 → 문서별 즉시 분석
                                  ↓
                   특징·홍보 내용·제출 후보 선택
                                  ↓
                  location/원문 → 결과 파일·응답
                                  ↓
                     SQLite 이력 → 후보 검토
```

Python·FastAPI·Uvicorn·httpx·BeautifulSoup4·html5lib·HTML/JavaScript를 사용하고, 선택적인 동적 수집은 Playwright와 설치된 Microsoft Edge를 사용합니다. 수집과 탐지는 HTML5 파서로 같은 DOM 구조를 구성합니다. 재현 환경·의존성 설치는 README, 설치/검사 이력은 project.md에서 관리합니다. 프레임워크와 버전은 공모전 지정 기술이 아닙니다.

| 구성 | 구현 위치·책임 |
|---|---|
| 시작·경로 | run_app.py, paths.py: 로컬 서버·정적 리소스·결과/DB 경로 |
| API·작업 | main.py, models.py, jobs.py: 입력/응답·단일 작업·진행·중단 |
| 수집·범위 | crawler.py, browser.py, limits.py, coverage.py: HTML/DOM·링크/프레임·한도·실제 범위 |
| 특징·내용·정책 | detection.py, jamo.py, content.py, textnorm.py, policy.py, rendered.py: 탐지·정규화·원문 연결·제출 선택 |
| 위치·결과 | location.py, comparison.py, result.py: selector·URL 동등성·출력 계약 검증 |
| 영구 이력 | history.py: 분석·후보 사본·누적 검토 |
| 화면 | frontend/static/index.html, history.html: 분석·이력/검토 UI |
| 오프라인 검수 | evaluation.py, review.py, review_inventory.py, validation_suite.py 및 scripts의 관련 CLI |

Result Builder는 result.py로 분리되어 있습니다. 기존 root result.json은 과거 산출물일 수 있으므로 최신 분석 성공의 증거로 사용하지 않습니다.

### 로컬 이력 저장

SQLite는 분석 요청/응답 사본·SHA-256, feature/content 후보, 사람의 검토 기록을 저장합니다. 분석 ID와 분석 내부 후보 ID의 조합으로 연결하며 재분석 사이 같은 광고를 식별하는 영구 ID는 아닙니다. 스키마·복합키·제약·저장/조회 동작의 상세는 [DB 설계서](docs/DATABASE_DESIGN.md)를 따릅니다.

DB는 실행 폴더가 아닌 LOCALAPPDATA/YearDream/history.sqlite3에 두고, LOCALAPPDATA가 없으면 ~/.local/share/YearDream/history.sqlite3를 사용합니다. 검토는 추가 방식이며 분석 사본·공식 JSON을 바꾸지 않습니다. DB 저장 실패는 현재 분석을 실패로 바꾸지 않고 경고·null analysis_id로 안내합니다. 전체 HTML/DOM 관찰값은 이력DB에 보관하지 않습니다.

### Windows 실행·배포

`run_app.py`는 소스/Windows 실행 파일 공통 진입점입니다. 쓰기 가능한 결과 경로를 확인하고 127.0.0.1 소켓을 먼저 확보한 다음 단일 Uvicorn 서버를 실행합니다. 서버 준비 후 기본 브라우저를 열며 `--no-browser`로 생략할 수 있습니다. 기본 포트 8000, `--port`로 변경하며 0이면 자동 선택합니다. GPU·외부 AI API는 필요하지 않습니다.

`backend/app/paths.py`는 frontend/static 리소스의 번들 경로와 출력 경로를 구분합니다. 소스 실행은 프로젝트 루트, PyInstaller frozen 실행은 sys.executable의 부모 폴더에 결과 두 파일을 저장합니다. rendered_snapshot.js는 기존 browser.py 옆에 포함합니다. PyInstaller 6.22.3의 onedir 방식으로 Playwright 드라이버와 Python 런타임을 포함하고 설치된 Edge를 사용합니다. 빌드 스크립트는 새 출력 폴더·ZIP·소스/배포 해시 매니페스트·설명서 사본을 만듭니다. 기존 결과·실제 캡처·가상환경은 배포하지 않습니다. 코드 서명·설치 프로그램·자동 업데이트는 미구현입니다. 다른 PC 정상 작동 사용자 보고와 버전별 상세 검증은 project.md에서 구분합니다. 실행/빌드 방법과 결과 경로는 docs의 두 설명서를 따릅니다.

## 4. 수집 규격

URL 검증·정규화 → Queue → 페이지 수집 → DOM 분석 → 하위 링크·iframe 등록 → 중복 제거 → 탐지 전달 흐름을 따릅니다.

수집 단계에서 요청/최종 URL·HTML·부모/프레임 관계·실패/한도 사유를 보존합니다. 다음은 논리적 정보이며 외부 제출 JSON의 필드를 추가하라는 뜻은 아닙니다.

- 입력·요청·리디렉션 후 URL, HTML, 텍스트
- 페이지 종류(page/post/comment/iframe), 부모 페이지 관계
- iframe 내부 URL, 상위 문서에서 시작하는 프레임 요소 selector 경로
- 성공·실패·시간 초과·한도 중단 사유

일반 링크와 프레임 문서를 구분합니다. 현재 top_url·parent_url·frame_path를 보존하며 같은 iframe URL도 삽입 위치마다 별도 컨텍스트로 처리합니다. 정적 모드는 성공/실패 응답을 실행 중 URL별 캐시로 재사용합니다. 상대 src와 정적 srcdoc을 처리하고 순환·깊이 초과·외부/미지원 src를 기록합니다. srcdoc의 링크 기준은 부모 문서 URL입니다. HTML base 요소는 미지원입니다.

동적 모드는 요청마다 새 Edge 컨텍스트를 열고 일반 페이지를 DOMContentLoaded까지 이동한 뒤 기본 500ms를 추가 대기합니다. 기존 개인 프로필은 사용하지 않으며 팝업은 닫고 Service Worker는 차단합니다. JS가 만든 본문·fetch 댓글·링크·iframe과 실행된 srcdoc/about:blank의 DOM을 읽습니다. iframe은 URL로 다시 열지 않고 원래 부모 안의 실제 Frame을 읽으므로 동일 src라도 부모가 수정한 삽입별 상태를 유지합니다. 프레임을 모두 처리한 뒤 다음 일반 페이지로 이동합니다. 스냅샷은 문서별 순차 수집이며 전체 프레임 트리의 원자적 고정본이 아닙니다.

동적 iframe의 현재 URL이 범위 밖이면 제외하며 src가 있으나 아직 about:blank인 프레임은 frame_not_loaded, 분리·접근 실패는 frame_unavailable로 알립니다. HTTP 400 이상 문서는 실패로 처리하고 페이지 JavaScript 예외는 warnings로 반환합니다. 프레임 깊이와 문서 수는 읽는 DOM 컨텍스트를 제한하며 브라우저가 이미 로딩하는 리소스·외부 요청의 차단 또는 총 요청 수 제한을 뜻하지 않습니다. 종료·오류 시 브라우저와 드라이버를 정리합니다.

사용 API의 기준은 Playwright 공식 문서의 [Page.goto](https://playwright.dev/python/docs/api/class-page#page-goto), [Frame.content](https://playwright.dev/python/docs/api/class-frame#frame-content), [BrowserType.launch](https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch)를 참조합니다.

현재 수집 범위는 netloc가 같은 HTTP(S) 링크·프레임이며 서브도메인·포트가 다르면 별도 범위로 처리합니다. 이 범위 정책은 구현 선택이며 다른 호스트/외부 iframe 분석 지원으로 확대 해석하지 않습니다.

상대 URL·fragment·query·중복·리디렉션·비HTTP 링크와 실패를 처리합니다. 현재 API별 기본 한도는 아래와 같으며 공식 지정 수치가 아닙니다.

| 한도 | 기본값·의미 |
|---|---|
| max_pages | UI/작업 API 100(1~1000), 동기 API 8. 실패를 포함한 문서 컨텍스트 수. 반복 iframe도 위치별 계산 |
| max_depth | UI/작업 API 4, 동기 API 2. 시작 페이지 0에서 링크 이동마다 1 증가 |
| max_iframe_depth | 3, 프레임 경계 수. 링크 깊이와 별도 |
| total_timeout_sec | UI/작업 API 1500초, 동기 API 60초. 수집·탐지 공유 시간 예산 |
| HTTP timeout | 최대 10초, 요청 시작 시 남은 공유 시간보다 길지 않게 설정 |

프레임·srcdoc에 들어가도 링크 깊이는 유지하고, 프레임 안의 링크를 따라가면 1 증가합니다. 같은 링크 깊이의 프레임을 먼저 확장해 깊이가 더 큰 경로가 짧은 경로를 가리지 않도록 합니다. 깊이 초과 링크·문서 수·프레임 깊이·시간 중단 사유를 구분합니다.

화면은100문서·깊이4·25분을 변경 가능한 기본값으로 제공하며 문서1~1000·깊이0~20·시간1~30분을 입력할 수 있습니다. 한도 값과 실제 분석 완료 수는 다를 수 있습니다.

공유 시간은 monotonic clock으로 측정하고 요청 시작·응답 스트림 청크·수집 반복·탐지 요소 처리 사이에서 확인합니다. 이미 진행 중인 I/O·파싱·selector 탐색을 즉시 중단하는 강제 종료가 아니므로 제한을 일부 초과할 수 있습니다. 최종 결과 변환·직렬화·파일 저장은 중단 결과를 돌려주기 위한 마무리이며 이 예산으로 강제 종료하지 않습니다. 공식 30분 조건의 엄격한 준수를 검증한 기능으로 취급하지 않습니다.

HTML에 존재하는 게시글·댓글과 JS 실행·추가 요청이 필요한 콘텐츠를 구분해 검증합니다. 동적 모드는 제한된 관찰 시점까지 생성된 DOM·계산 스타일을 지원합니다. 자동 스크롤·클릭·로그인·Shadow DOM은 미지원입니다. DOM 수집 후 변동이 있으면 selector 재식별이 실패할 수 있으며 실제 사이트 정확도는 별도 검증합니다. 개별 프레임 실패가 전체 탐색을 중단시키지 않게 하되 전체 수집 실패는 정상 0건과 구분합니다.

### 우선순위·읽기 링크·첨부 제외

순차 수집에서 게시판 목록·게시글을 일반 안내보다 우선하고, 내용 후보가 관찰된 문서의 자식 작업을 추가 우선합니다. iframe은 실제 부모 Frame이 유효할 때 먼저 처리합니다. 페이지 넘김은 발견된 HTTP(S) 링크만 따르며 자동 클릭은 하지 않습니다. query 순서 정규화와 xboard/board.php의 mode=view+number+tbnum 조합에서 page/sCat/keyset/searchword 차이를 수집 중복 판정에서 제외하되 실제 요청 URL·근거 URL은 유지합니다. 다른 게시판/게시글 ID와 일반 query 값은 합치지 않습니다.

xboard의 mode1=go는 추적용 파라미터가 아니라 바로 이동 동작을 바꾸므로 중복 키에서 제거하지 않습니다. 우선 탐색 모드에서는 해당 링크로 외부 이동하는 대신 mode1을 제거한 같은 호스트의 공개 본문 보기 경로를 명시적으로 수집합니다. 원래 링크는 redirect_link 사유로 남기고 수집 문서의 source_link에 보존해 발견 링크와 실제 읽은 경로를 구분합니다. 이 어댑터는 xboard 경로·mode=view·mode1=go·number·tbnum이 모두 맞을 때만 적용합니다.

알려진 첨부 링크는 attachment 사유로 대기열에 넣지 않습니다. 정적 HTTP는 MIME·Content-Disposition·Content-Length를 확인하고 압축 해제 후 누적 바이트도 5 MiB로 제한합니다. 알려진 PDF/ZIP/이미지 시그니처도 제외합니다. 웹 페이지·브라우저 DOM 이외의 첨부파일 탐지는 지원 범위가 아닙니다. 이 방어는 동적 DOM의 크기나 사이트 전체 요청 수의 한도를 뜻하지 않습니다.

작성·수정·삭제·답글 작성·로그아웃 등의 mode/action/act/cmd/do 또는 경로 작업 이름은 non_readonly 사유로 자동 방문에서 제외하며 해당 진입 URL도 거부합니다. 폼을 제출하거나 사이트 데이터를 변경하는 기능은 없습니다. 우선순위가 깊이순과 다를 수 있으므로 URL별 최단 발견 깊이를 보관하고, 더 짧은 경로가 나중에 발견되면 확장할 수 있게 합니다. 오래된 깊은 대기 작업은 요청 전에 건너뜁니다.

### 실제 탐색 범위 응답

분석 API의 `coverage`는 기존 `crawled_pages`(성공 수집 URL의 중복 제거 목록)와 별개로 문서 컨텍스트별 수집/탐지 상태를 보관합니다. `documents`는 requested_url·최종 url·parent_url·depth·frame_path·상태(analyzed/not_analyzed/collection_failed)·이유를 담습니다. 요청 후 시간 예산으로 수집/전처리를 끝내지 못한 문서는 interrupted_context로 보존하고 coverage에 실패로 집계합니다. 따라서 이미 요청한 URL을 미방문으로 잘못 세지 않습니다. 같은 URL의 반복 iframe은 각각 셉니다.

`unvisited_links`는 알려진 링크/잔여 수집 대기열 중 방문 기록이 없는 URL과 발견 문서·한도 이유를, `excluded_frames`는 제외되거나 대기열에서 수집되지 못한 iframe 위치·이유를 담습니다. `limits`에는 적용한 문서 수/깊이/시간/iframe 깊이를 기록합니다. `website_complete=false`는 사이트 전수 검사를 확정하지 않는다는 뜻이며 알려진 미방문이 0이어도 전체 미분석이 0이라는 뜻이 아닙니다. 퍼센트 검사율은 산출하지 않습니다.

탐지 화면은 집계를 기본 표시하고 상세 URL/위치/사유를 펼쳐 볼 수 있습니다. 수집 성공·탐지 미완료를 탐지 완료와 구분하고, 0건은 분석한 범위의 결과로 안내합니다. 결과 필터를 바꿔도 이 범위는 바뀌지 않습니다. 범위는 DB 분석 사본과 검수용 후보 다운로드에도 보관하지만 공식 result.json/result_extra.json 규격에는 넣지 않습니다. 이전 DB 기록에 없는 범위는 소급 추정하지 않습니다.

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

현재 내용 판별 규칙은 content-rules-v5입니다. 변경·실사이트 검사 이력은 project.md에서 관리합니다. 표현/은닉 4종과 내용 범주는 독립적입니다. content_candidates는 검수용이고 result_extra.json은 PDF 13쪽의 ETC+extra_finding 형식입니다. 일반 표시 후보를 필수 4종으로 임의 분류하지 않으며 후보 부재도 광고 부재를 보장하지 않습니다.

내용 판별은 텍스트를 가장 가까운 블록에 귀속해 inline 조각만 합치고 문단은 섞지 않습니다. 문장 경계와 주제 앞 45/뒤 100자의 규칙은 유지하며 도메인 내부 마침표를 경계로 만들지 않습니다. textnorm.py는 NFKC·현대 한글/호환 자모 재조합·제한된 키릴 닮은꼴→Latin 매핑·casefold·공백/일부 zero-width 제거를 판별용으로 적용합니다. 정규화 문자마다 원문 범위를 추적해 원문 자체는 바꾸지 않습니다. 카지노·성인물 등의 주제와 가입/보너스/시청/바로가기 등의 단서가 함께 필요합니다. PDF 예시의 mega-BET·슬롯 체험·먹튀검증/텔레그램 유도도 검증합니다. 예방교육·단속 보도·광고 신고/삭제 요청·피해상담 등 명시적 보호 문맥은 제외합니다. 전체 Unicode 위장·모든 자모 조합·은어·의미 이해를 지원하는 것은 아닙니다.

후보 단위는 URL+location+category이며 GAMBLING/ADULT_CONTENT로 분류합니다. selector·원문·근거 문맥·matched_terms·policy_version·needs_review 상태와 feature_links(location+technique)를 보존합니다. HOMOGLYPH/JAMO는 실제 의심 문자 구간, CSS 기법은 해당 요소의 직접 텍스트 중 공백/제거 대상 zero-width를 제외한 구간이 홍보 주제/유도 표현과 겹쳐야 연결합니다. URL·프레임·블록·문장을 넘겨 무관한 특징을 연결하지 않으며 techniques는 이 링크에서 계산합니다. 문단 안 별도 숨김 메뉴, 같은 요소의 전각 인사말/외국어 접두사, 숨김 zero-width만으로 홍보를 위장했다고 간주하지 않습니다. 후보 자체는 confidence나 is_violation 없이 검토 상태를 유지합니다.

정책은 모든 특징을 included 또는 needs_review로 평가하고 이유·관련 범주를 API에 남깁니다. included만 result.json에 explicit is_violation=true로 전달하며 근거 부족은 false로 확정하거나 제출하지 않습니다. 미탐·인용 문맥 오탐·어휘 밖 광고의 검토 잔류 위험이 있으며 이 규칙은 실제 정확도 검증을 대체하지 않습니다. 정상 숨김 UI·외국어·초성도 특징 자체는 화면과 feature 평가에 남습니다.

화면용 evidence에는 의심 문자·스타일·판정 이유를 설명합니다. 제출 evidence_text에는 별도 source_text의 정규화 전 DOM 텍스트를 설명 접두사나 길이 제한 없이 저장합니다(PDF 11쪽). HTML 마크업 문자열이 아니라 HTML 엔티티가 해석된 텍스트이며 공백·줄바꿈·전각·자모·zero-width 문자를 보존합니다. 필수 4종은 탐지 요소의 직접 텍스트 노드, 내용 후보는 같은 블록에 귀속된 텍스트 노드의 원래 순서로 수집합니다. 동적 모드는 관찰 시점의 DOM 원문입니다.

현재 정적 탐지에서는 직접 텍스트를 가진 요소를 대상으로 하고 script·style·head·template·noscript·주석·속성 문자열은 텍스트 판정에서 제외합니다. 유형별 첫 일치에서 멈추지 않고 모든 일치를 반환합니다. 근거에 해당 요소의 원문을 포함합니다.

단순 inline 선언의 중복·!important 우선순위를 처리하며 opacity는 정확히 0인 경우와 조상 opacity:0을 확인합니다. 클래스 이름만으로 투명 여부를 판정하지 않습니다. OFFSCREEN 후보는 display:none, 0~1px 글꼴, absolute/fixed와 음수 left/top(px) 조합입니다. 단독 absolute·overflow:hidden은 제외합니다. 음수 좌표의 실제 화면 이탈 여부와 유형 분류는 추가 검증이 필요합니다.

위 inline 규칙은 정적 모드 및 스타일 관찰값 없는 과거 저장본의 기준입니다. 새 동적 모드는 rendered_snapshot.js의 단일 동기 호출에서 HTML과 직접 텍스트를 가진 HTML 요소별 관찰값을 함께 수집합니다. 문서 안 요소는 순차 관찰하며 프레임 트리 전체의 동일 시점 고정이나 애니메이션·이후 DOM 변경을 보장하지 않습니다. DOM을 수정하지 않고 구조 선택자·원문·계산 스타일·좌표를 저장합니다. 처리 반복에 공유 시간 예산을 적용하되 브라우저 내부 연산의 즉시 강제 종료는 아닙니다. API 사용 기준은 [getComputedStyle](https://developer.mozilla.org/en-US/docs/Web/API/Window/getComputedStyle)과 [getBoundingClientRect](https://developer.mozilla.org/en-US/docs/Web/API/Element/getBoundingClientRect) 문서를 참조합니다.

rendered.py의 rendered-style-rules-v1은 zero opacity·계산된 visibility·투명 글자·동일 불투명 RGB 단색 배경을 TRANSPARENT로, 조상 포함 display:none·상속된 0~1px 글꼴·양의 크기를 가진 요소의 전체가 문서 왼쪽/위쪽 음수 영역에 있는 배치를 OFFSCREEN으로 판단합니다. 좌표에 스크롤을 더해 문서 기준으로 비교하며 일반적인 스크롤 아래 콘텐츠와 일부 보이는 음수 배치는 제외합니다. 그림자/윤곽선이 있으면 글자색만으로 투명 판정하지 않습니다. 관찰값이 있으면 CSS 기법에서 inline 후보보다 우선하여 !important·실제 레이아웃을 반영합니다. 관찰 대상이 아닌 요소에는 CSS 후보를 임의 보충하지 않습니다.

배경 이미지·그라데이션·반투명 합성·표준 RGB 이외 색상 계산은 추측하지 않습니다. 가림·clip·양의 방향 화면 밖·SVG·가상 요소·Shadow DOM·프레임 경계 밖 iframe 요소의 은닉 전파는 미지원입니다. HOMOGLYPH/JAMO와 노드 간 문자 조합은 별도 문자 판별 규칙을 적용합니다. 합성 특징 검증은 광고 여부를 확정한 정답이 아닙니다.

관찰값은 capture.json의 문서별 rendered_style(schema_version=1)에 보존합니다. 현재 parser가 선택자를 정확히 한 요소로 해석하고 원문이 일치하는지 검증하며 중복·잘못된 경로·원문 불일치는 평가를 거부합니다. 저장 HTML과 관찰값이 함께 labels의 capture 해시에 연결됩니다. 보고서는 렌더링 판정 코드 해시·정책 버전 및 observation_basis를 기록합니다. 과거 browser 캡처라도 관찰값이 없으면 정적 문서 수로 집계해 현재 computed style 평가로 오해하지 않게 합니다. 정적 사례의 한계는 [사례 설명](tests/fixtures/detection/README.md)을 따릅니다.

### JAMO의 웃음 표현 예외와 알려진 한계

`jamo.py`의 연속 자모 구간 중 전체가 ㅋ/ㅎ 두 글자 이상인 경우만 JAMO에서 제외합니다. 단독 자음·다른 자모·모음/현대 자모는 유지하고 CSS 특징도 별도로 탐지합니다. textnorm.py도 같은 구간을 호환 자모로 보존해 앞 단어의 받침으로 합치지 않습니다(content-rules-v4). 원문/위치 범위는 유지합니다. capture·평가·검토 내보내기와 벤치마크는 공유 jamo 규칙 파일의 해시도 기록합니다.

현재 범위에는 호환 자모인 아래아(ㆍ)도 포함됩니다. 사용자 이력 검토에서 정상 행정 문구15개가 이 문자 때문에 JAMO 검토 대상으로 잡힌 사실을 확인했습니다. 제출 후보 선택과는 구분되며 이 알려진 한계는 아직 수정하지 않았습니다. 근거와 후보 중복 관찰은 project.md의 현재 요약을 따릅니다.

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

필수 필드·자료형·허용 기법·ID·중복·시간·빈 배열을 검증합니다. 두 결과 모두 UTF-8 BOM 없이 meta+findings 두 키와 단일 findings 배열로 저장합니다. 소스 실행은 프로젝트 루트, 패키지 실행은 실행 파일 옆에 result.json 및 result_extra.json을 저장합니다. PDF는 구동 파일 폴더를 원칙으로 하며 다른 경로면 사용설명서 첫 장에 파일별 경로를 안내합니다. Windows 구동 파일과 단일 분석 동시 실행 제한은 구현되어 있습니다. 두 파일 저장 중 디스크 오류에 대한 원자적 트랜잭션 보장은 없습니다.

result_extra.json은 같은 실행 meta를 사용하며 id/url/location/evidence_text/technique/extra_finding을 갖습니다. technique은 ETC이고 extra_finding은 GAMBLING_PROMOTION_CANDIDATE 또는 ADULT_CONTENT_PROMOTION_CANDIDATE입니다. PDF 13쪽 추가 결과 예시처럼 is_violation을 자동 추가하지 않습니다. 이 파일은 본심사 참고용 추가 제안이며 필수 4종 성능을 대체하지 않습니다. 성공한 0건 분석에서도 빈 findings로 저장하며 수집 실패/분석 전 시간 초과 시 기존 파일을 보존합니다.

PDF 12쪽에 따라 정답 핵심은 URL+실제 위치+기법이고 evidence_text는 필수 본심사 참고자료입니다. 필드 누락·스키마 미준수 항목은 오답/채점 제외 대상이며 파일 파싱 불가는 해당 회차 성능 점수 0점입니다. 제출 파일 미생성 등은 평가 제외 가능성이 있습니다. 자체 테스트 통과를 주최 측 채점 통과로 표현하지 않습니다.

## 8. API와 UI

### 경로와 입력

| 경로 | 역할 |
|---|---|
| GET /, GET /history | 분석 화면, 이력/후보 검토 화면 |
| GET /api/health | 서버 생존 확인 |
| POST /api/jobs | 화면용 비동기 분석 생성,202와 작업ID 반환 |
| GET /api/jobs/{job_id} | 작업 요청·상태·진행·경과·결과/error 조회 |
| POST /api/jobs/{job_id}/cancel | 협력적 중단 요청 |
| POST /api/analyze | 기존 동기 호환 분석·결과 반환 |
| GET /api/history | 이력 목록, limit기본20(1~100), offset기본0(0이상) |
| GET /api/history/{analysis_id} | 요청·응답 사본·후보별 검토 전체 |
| POST /api/history/{analysis_id}/candidates/{candidate_id}/reviews | 내용 분류 검토 추가 |

분석 필수 입력은url입니다. 공통 선택값은collection_mode=static/browser(기본static), render_wait_ms=500(0~5000정수), max_pages(1~1000정수), max_depth(0~20정수), total_timeout_sec(0초과~1800이하 유한숫자), prioritize_boards입니다. 작업API의 기본값은100/4/1500초/우선탐색true, 동기API는8/2/60초/false입니다. UI는 시간 분을 초로 변환합니다. 이 값들은 공식 지정 한도가 아닙니다.

응답 AnalysisResponse는url·collection_mode·page_title·crawled_pages·findings·content_candidates·content_policy_version·submission_policy_version·result_json·result_extra_json·warnings·coverage·nullable analysis_id를 제공합니다. 내부 finding의selector/location/evidence/source_text와 제출용 finding은 구분합니다. 제출 후보 선택 상태/이유/범주를 제공하고 result_json은 선택 후보만 포함하므로 전체 특징 수와 다를 수 있습니다.

### 작업 상태·중단·재연결

UI는 `POST /api/jobs`로 JobRequest를 만들고 `GET /api/jobs/{id}`를 약 500ms마다 조회합니다. 기본값은 max_pages=100, max_depth=4, total_timeout_sec=1500, prioritize_boards=true입니다. 문서 수 1~1000·깊이 0~20·시간 예산 최대 1800초를 검증합니다. `POST /api/jobs/{id}/cancel`은 협력적 중단을 요청합니다. 별도 작업 스레드에서 수집한 문서를 즉시 분석하므로 수집만으로 예산을 다 써 완료 결과가 전혀 없는 경로를 줄입니다.

작업 상태는 running/completed/cancelled/failed, 진행 단계는 starting/collecting/analyzing/saving/cancelling와 종료 상태입니다. 실제 완료 건수·대기 건수·현재 URL·경과 시간을 전달하며 전체 분모가 확정되지 않아 사이트 검사율은 계산하지 않습니다. 중단 시 완료한 문서만 결과 파일·DB에 보관하고 완료 문서가 없으면 기존 결과를 덮어쓰지 않습니다. I/O/파싱 중 즉시 종료는 보장하지 않습니다.

한 번에 분석 하나만 허용하며 중복 실행은 409입니다. 최근 작업 20개는 메모리에서만 보관하고 오래된 완료 작업을 제거합니다. 완료 분석의 SQLite 이력과 별개이며 앱 재시작 시 작업은 사라집니다. 같은 탭의 sessionStorage 작업 ID로 새로고침/일시 조회 실패 후 재연결할 수 있고 만료 ID는 404입니다. 기존 POST /api/analyze는 동기 호환 경로로 기본 8문서·깊이2·60초·발견순을 유지하되 max_pages/prioritize_boards를 명시하면 같은 점진 분석 로직에 적용합니다. 기존 오프라인 capture 도구도 별도의 기존 기본값을 유지합니다.

### 오류·부분 결과

모델 입력 오류는422, 중복 분석은409, 없는 작업/이력/후보는404입니다. 이력 조회/검토의 DB 오류는503입니다. 검토 입력은decision=promotion/normal/uncertain, reviewer1~100자·reason1~2000자이며 서버에서 앞뒤 공백을 제거한 뒤 빈 값을 거부합니다. 서버UTC시각과 함께 기록을 추가합니다.

브라우저 시작 불가는503, 전체 수집 실패는502, 완료 문서 없는 시간 예산 소진은504로 구분합니다. 한 문서는 특징·내용·제출 선택까지 마쳐야 완료입니다. 중단된 문서의 중간 후보는 포함하지 않고, 완료 문서가 있으면 부분 결과/안내를 반환합니다. 완료 문서 없는 중단/실패는 이전 파일을 유지합니다. 브라우저 실패 시 정적 모드로 자동 전환하지 않습니다.

위 분석 오류는 동기API에서는 해당 HTTP상태로 반환합니다. 비동기 작업은 생성의202와 실행 결과를 구분하며 이후 status/error 안에서 실패 원인과 status_code를 확인합니다. 작업 조회 자체의HTTP200만으로 분석 성공을 판단하지 않습니다.

### UI·다운로드

UI는 같은 서버의 /api/jobs를 상대경로로 호출하고 약500ms 간격으로 조회합니다. 상세 배치·상태별 잠금·현재 범위 안내는 [화면설계서](docs/SCREEN_DESIGN.md)를 따릅니다. 수집/탐지 로직은 서버에 두며 원문·URL·안내를textContent로 표시합니다. 유형 필터는 표시만 바꾸며 분석 범위를 확대하지 않습니다.

분석 안내는 사유별 건수·접힌 상세로 묶고 중단·실패를 먼저 표시합니다. 동일 원문은 반복 건수를 표시하지만 API/DB/다운로드의 원문 배열은 유지합니다. 이력 상세의 개별 안내 문단은 분석 화면과 별도입니다.

세 다운로드는 현재 화면이 보관한 마지막 응답의result_json·result_extra_json·전체content_candidates를 각각 사용합니다. 검수용content-candidates.json의purpose는content_candidate_review이며 규칙 버전·메타·범위·안내를 포함합니다. 필터에 독립적이고 서버 파일을 다시 가져오지 않습니다. Blob으로UTF-8 BOM 없이 저장하며 파일과의 동등성은 파싱한JSON값 기준입니다. 새 분석·실패·빈URL·완료 결과 없는 중단에서는 다운로드를 비활성화합니다.

이전 문서의 /api/detection 계열이나queued/timeout을 별도 작업status로 두는 구상은 현재 계약이 아닙니다. 현재 작업status와 progress.phase는 위 규격을 기준으로 합니다.

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

### 내용 정답 검수

`scripts/validate_site.py evaluate RUN --kind content`는 `content-labels.json`을 사용하고 `content-report.json`으로 저장합니다. 기본 evaluate는 기존 4종 기법 평가입니다. 새 capture는 두 정답 초안을 모두 생성하며, 이전 저장본에는 `init-content-labels RUN`으로 내용 정답을 추가합니다. 기존 파일 덮어쓰기는 거부합니다.

내용 검수 단위는 최상위 URL + 프레임을 포함한 텍스트 블록 위치 + GAMBLING/ADULT_CONTENT 범주입니다. 후보만 확인하지 말고 미탐 블록과 정상 사례도 정답에 추가해야 합니다. `complete: false`에서는 검수된 TP/FP/FN/TN만 집계하고 지표는 null입니다. 저장 문서 전체의 양성 정답을 검수하고 기준 policy를 기록했을 때만 complete를 true로 설정합니다. 전체 검수에서는 양성 정답 밖 후보를 FP로 계산합니다.

원본 HTML·capture 해시와 정답 연결, 선택자 유일성, 동등한 선택자의 중복을 검사합니다. 보고서는 정답 및 평가 코드 해시도 기록합니다. 법적 판단 메모는 선택적 violation_verdict/reviewer/verdict_reason으로 보존하며 내용 존재 평가와 분리합니다. 기본은 미판정이고 API나 제출 스키마에 자동 반영하지 않습니다.

### 전체 텍스트 검수 인벤토리

`review_inventory.py`는 저장본의 비어 있지 않은 `_text_units` 블록 전체를 열거해 원문/해시·URL/location·현재 검출 범주·두 범주의 ContentLabel을 내보냅니다. 새 label은 expected=null·reviewed=false이며 기존 label/이유를 복사합니다. 현재 예측을 정답으로 사용하지 않습니다. capture/HTML/정답/선택자 검증은 기존 오프라인 평가와 공유하고 입력 변경 감지도 수행합니다. 블록 단위 밖의 정답은 별도 배열로 보존합니다. 프레임/동일 문구는 위치별 단위를 유지합니다.

### 반복 후보 집계

content suite의 `prediction_repetition`은 예측의 범주+정확한 source_text UTF-8 해시로만 그룹을 만듭니다. 공백·Unicode 차이를 정규화하지 않고 같은 원문이 다른 범주에 있으면 분리합니다. 예측 수·고유 그룹·반복 그룹·반복 그룹의 전체 건수·그룹 첫 건 이후 반복 수 및 URL/location/case_id 참조를 기록합니다. 위치별 평가/제출 단위는 그대로이며 의미상 고유 광고나 독립 데이터의 개수를 추정하지 않습니다. feature suite에는 null입니다.

### 여러 저장본 일괄 평가

`validation_suite.py`와 `scripts/evaluate_suite.py`는 manifest의 capture/정답 해시를 검증하고 네트워크 없이 여러 저장본을 재평가합니다. 중복 ID/경로와 다른 케이스 간 겹치는 동등 페이지 URL을 거부합니다. feature/content 평가 목적을 구분하고, 부분 검수 케이스가 하나라도 있으면 집계 지표는 null입니다. 미검토 예측과 수집 경고를 별도 집계하며 기존 보고서를 덮어쓰지 않습니다. 같은 도메인의 반복 목록은 다른 요소로 계산되므로 표본 다양성으로 해석하지 않습니다.

### CLI 제출 후보 수동 검토

`backend/app/review.py`와 `scripts/review_submission.py`는 자동 API 정책과 독립적인 오프라인 검토·내보내기를 제공합니다. `submission-review.json`은 capture SHA-256과 검출된 각 특징의 URL/location/technique/원문에 연결됩니다. 최초 판단은 모두 pending입니다. include/exclude에는 검토자·이유·시간대 있는 검토 시각이 필수입니다. 저장 HTML 해시·요소 단일 재식별·원문 일치·전체 검출 목록 보존·선택자 별칭 중복을 검증한 뒤 include만 명시적 true로 Result Builder에 전달합니다. pending/exclude를 false로 변환하지 않습니다.

새 출력 폴더의 result.json과 함께 정확한 검토 원본 사본 및 review-audit.json(수집/검토/결과/현재 코드 해시, 자동 평가, 포함·제외·미검토 수)을 보존합니다. 해시는 변조 확인용이며 전자서명이나 쓰기 방지는 아닙니다. 검토 완료는 재현된 검출 목록에만 한정됩니다. 기존 content-labels.json의 내용 정답·법적 판단 메모를 자동 전환하지 않으며 특징/내용 정확도 지표도 변경하지 않습니다. 이 CLI에는 검토UI·누락 요소 추가·내용 분류 검토·여러 파일의 원자적 저장이 없습니다. /history의 DB 내용 분류 검토와 별개입니다. 실행법은 README를 따릅니다.

실행 명령은README, 날짜별 입력·검수 수치·원본/보고서 근거는project.md와docs/VALIDATION.md에 기록합니다. 같은 실행 수치를 여러 문서의 현재 현황으로 복사하지 않습니다.

## 10. 미확정 사항·선택 기능

현재 정한 구현 정책과 아직 검증하지 않은 범위를 구분합니다. 동일netloc 수집·한도·필수/추가 결과·후보 선택은 위 현재 규격이며, 전체 광고 정확도·독립된4종 실사이트 양성·동적 대규모 처리·다른Python/OS·엄격한 공식 시간 준수는 검증 완료가 아닙니다. 현재 이슈·제출 준비 상태는project.md가 기준입니다.

로컬SQLite 이력·검토는 구현되어 있습니다. 사례 검색·RAG·공동 이용 서비스 등 확장은 아래 보류 로드맵으로 관리하며 문서 점검을 새 기능 개발 승인으로 해석하지 않습니다.

### 제출 후보 패키지 구조

`scripts/package_submission.py`는 깨끗한 Git 작업 트리의 추적 소스/문서와 검사된 Windows 폴더를 새 제출 후보로 묶습니다. 빌드 매니페스트·파일 해시·passed 검사 보고서·exe 해시를 검증하고 기록된 분석 빌드 입력 및 새 backend/frontend 런타임 파일이 현재 소스와 일치하는지 확인합니다. 명시된 오프라인 평가/검수 모듈의 변경은 별도 기록합니다. 검증된 파일만 실행 폴더에 복사하고, 전체 소스 ZIP·현재 설명서/점검표·서류 안내/확인된 원문 PDF·검증 근거·해시 매니페스트·ZIP 체크섬을 만듭니다. 기존 출력·실제 수집 자료·가상환경·이전 결과는 전달하지 않습니다.

`ready_to_submit=false`와 미완료 서류·서명·별도 PC·접수/독립 검증 항목을 기록합니다. 제출 후보 생성과 실제 제출은 구분합니다. 자동 접수나 임의 개인정보/서명 작성은 하지 않습니다. 소스와 생성법은 BUILD_MANUAL, 남은 최종 확인은 SUBMISSION_CHECKLIST/OTHER_PC_CHECKLIST를 따릅니다.

현재 파일의 보관/삭제 상태와 실제 접수 여부는project.md를 따릅니다. 패키지 생성법 설명이 새 제출 묶음의 존재나 접수를 의미하지 않습니다.

<a id="future-roadmap"></a>

## 향후 발전 방향 및 기대효과

2026-10-25 사용자 결정으로 아래 확장은 보류합니다. 현재 로컬 프로그램의 완료 요건이나 즉시 실행할 개발 목록이 아니며, 재개 일정은 정하지 않았습니다. 이미 구현한 SQLite 이력·후보 검토 기능은 유지합니다.

서비스 확장의 목표는 여러 담당자가 공공 웹사이트 점검 결과와 처리 이력을 함께 관리하는 것입니다. 브라우저 UI·DB·RAG의 존재만으로 서비스 플랫폼이 되지는 않습니다. 중앙 서버에서 분석할지, 각 PC에서 분석하고 관리 정보만 공유할지도 향후 이용 환경에 맞춰 결정합니다.

| 발전 방향 | 해결할 문제·제안 기능 | 기대효과 | 재개 전 확인할 조건 |
|---|---|---|---|
| 공동 이용 서비스 | 중앙 접속, 사용자별 권한, 담당자 배정·처리 상태 공유 | 개별 PC에 흩어진 업무를 연결하고 중복 처리 감소 | 사용자/기관 수요, 인증·권한, 데이터 보관·백업, 안전한 URL 수집과 운영 자원 설계 |
| DB 활용 확대 | 점검 대상 목록, 정기 점검, 분석 간 변경 추적 | 점검 누락 감소와 신규·변경 후보의 빠른 확인 | 수집 범위·실패를 고려한 비교 기준. 이번에 관찰되지 않은 후보를 삭제로 단정하지 않기 |
| 검수 사례 등록·검색 | 출처·규칙 버전·검수 상태를 가진 홍보/정상 사례 검색 | 유사 사례를 찾는 시간 감소와 검토 근거 재사용 | 독립된 다양한 사례, 검색 결과의 관련성 평가. 자동 예측을 검수 정답으로 취급하지 않기 |
| 로컬 RAG 검토 보조 | 관련 기준·검수 사례를 검색한 뒤 로컬 모델로 비교 설명 생성 | 근거 이해를 돕고 검토 시간 단축 | PC 메모리·CPU/GPU·모델 배포 조건 확인, 출처 부합성·잘못된 설명·응답 시간 검증 |

RAG를 재개하더라도 외부 AI API는 사용하지 않는 방향입니다. 검색과 생성 모델을 로컬에서 구동하는 구상을 두되, 모델·검색 방식·벡터 저장소는 선정하지 않았습니다. 자료 검색만 구현한 단계는 RAG 생성 기능과 구분합니다. 모델 준비 이후 AI 처리에 외부 API를 호출하지 않아도 웹사이트 수집에는 네트워크가 필요합니다.

검수 사례에는 원문·URL/위치·출처/버전·검수 이유와 보류 상태를 보존하고, 공식 요구사항과 자체 구현 정책을 구분합니다. 내용 분류를 법적 확정으로 취급하지 않습니다. RAG 설명에는 참조 근거를 표시하고 근거가 부족하면 보류하며, 설명만으로 제출 후보를 자동 확정하지 않는 방향입니다.

기대효과는 아직 측정하지 않은 가설입니다. 재개 시 DB 기능은 조회/처리 시간과 기록 추적 가능성, 사례 검색은 관련 자료를 찾는 품질, RAG는 근거에 맞는 설명·검토 시간·오류·응답 시간으로 비교합니다. 현재 단일 도메인의 반복 사례만으로 일반 효과를 주장하지 않습니다.
