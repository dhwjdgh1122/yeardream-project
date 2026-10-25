# YearDream — 공공 웹사이트 불법광고 탐지 도구

URL을 시작으로 하위 페이지·게시글·댓글·iframe·중첩 iframe을 탐색하고 HOMOGLYPH·JAMO·TRANSPARENT·OFFSCREEN을 탐지합니다. 정확한 요소 위치와 근거를 `result.json` 및 결과 화면으로 제공합니다.

사용자 1명이 구현·탐지 기준·데이터 구성·정확도 검증을 모두 담당하며 코딩 에이전트가 이를 돕습니다.

### 저장본의 제출 후보 수동 검토

자동 규칙이 놓친 특징을 검토한 뒤 포함하거나, 자동 선택된 특징을 제외할 수 있습니다. 먼저 아래 capture 명령으로 저장본을 만들고, 해당 RUN 폴더에서 검토를 시작합니다. 실제 UI에는 아직 검토 버튼이 없습니다.

```powershell
.venv\Scripts\python.exe -B scripts/review_submission.py init .validation/RUN
```

생성된 `submission-review.json`의 `items`를 편집합니다. 모든 항목의 최초 `decision`은 `pending`이며 자동 선택을 사람의 승인으로 취급하지 않습니다. 실제로 검토한 항목만 `include`(제출 포함) 또는 `exclude`(제출 제외)로 바꾸고, `reviewer`·`reason`·시간대가 있는 ISO 8601 `reviewed_at`을 기록합니다. 예: `2026-10-25T15:00:00+09:00`. `source_text`와 `capture_sha256`는 변경하지 않습니다.

```powershell
.venv\Scripts\python.exe -B scripts/review_submission.py export .validation/RUN --output .validation/RUN-reviewed-01
```

새 폴더에 포함 결정만 담은 `result.json`, 검토 파일의 원본 사본, 해시·건수·자동 평가·코드 해시를 담은 `review-audit.json`이 생성됩니다. `pending`과 `exclude`는 결과에서 빠지며 정상(false)으로 단정하지 않습니다. 부분 검토도 내보낼 수 있지만 감사 기록의 `review_complete`는 false입니다. 이 완료 값은 **검출된 특징 목록**에 대한 검토만 뜻하며 전체 사이트 검수·정확도·법적 확정을 뜻하지 않습니다. 일반 홍보 내용에 임의의 4종 기법을 붙이거나 탐지되지 않은 요소를 추가하는 기능은 없습니다.

기존 검토·출력 폴더를 덮어쓰지 않습니다. `Review failed`가 나오면 원문/요소·항목 누락·검토 근거·시간대·기존 출력 경로를 확인합니다. 코드 변경으로 검출 목록이 달라지면 이전 검토를 자동 이식하지 말고 새 capture에서 다시 검토합니다. 원본 수집·정답·자동 API 결과·루트 결과 파일은 유지됩니다. 내보내기는 추가 유형 파일을 재생성하지 않습니다. 저장 중 디스크 오류가 나면 불완전한 출력 폴더가 남을 수 있으므로 오류를 해결하고 새 경로로 다시 실행합니다.

출력 위치 안내: **소스 실행은 이 README가 있는 프로젝트 루트, Windows 배포본은 YearDream.exe 옆**에 `result.json`(필수 4종)과 `result_extra.json`(추가 홍보 후보)을 생성합니다. 터미널 작업 폴더와 무관합니다. 화면 다운로드는 사용자 다운로드 폴더에 사본을 저장합니다. [사용자 설명서](docs/USER_MANUAL.md) 첫 부분에도 생성 경로를 명시했습니다(PDF 5·9쪽).

## Windows 실행 파일

현재 로컬 최신 배포본은 `dist/release-20261025-02/YearDream/YearDream.exe`입니다. 이전 버전의 콘솔을 Ctrl+C로 종료한 뒤 새 exe를 실행합니다. 기존 release-20261025-01은 보존했습니다. 아래 release-01은 새 빌드를 위한 예시 경로이며 이미 존재하면 다른 이름을 사용합니다.

Python 없이 실행할 수 있는 폴더형 패키지를 빌드합니다. 빌드 결과는 Git에 포함하지 않으며 로컬 dist 폴더에 생성합니다. 배포 ZIP 전체를 압축 해제한 후 YearDream.exe를 실행하면 로컬 서버와 브라우저 화면이 열립니다. 동적 분석에는 대상 PC의 Microsoft Edge가 필요합니다.

```powershell
.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements-build.txt
.venv\Scripts\python.exe -B scripts/build_windows.py --output dist/release-01
.venv\Scripts\python.exe -B scripts/test_packaged.py dist/release-01/YearDream
```

이전 빌드를 덮어쓰지 않도록 새 출력 경로를 지정합니다. ZIP 경로는 `dist/release-01/YearDream-windows-x64.zip`입니다. [빌드 설명서](docs/BUILD_MANUAL.md)와 [사용자 설명서](docs/USER_MANUAL.md)를 참조합니다. 소스에서 같은 시작 프로그램을 사용하려면 `.venv\Scripts\python.exe -B run_app.py`로 실행합니다. 별도 Windows PC의 독립 실행 검증과 실제 사이트 정확도 측정은 남아 있습니다.

## 문서 안내

| 문서 | 관리하는 기준 |
|---|---|
| [요구사항정의서.md](요구사항정의서.md) | 요구사항 ID, 필수 범위, 담당 역할, 통과 기준 |
| [wiki.md](wiki.md) | 구조, 탐지 기준, API, location, 결과 데이터 규격 |
| [README.md](README.md) | 설치·실행·테스트 절차와 문서 진입점 |
| [project.md](project.md) | 확인 날짜, 현재 상태, 검증 근거, 문제, 다음 작업 |
| [project-guide.md](project-guide.md) | 작은 단위 개발, 설명·검증·보고 방식 |

요구사항과 설계는 목표 기준이며 구현 완료를 뜻하지 않습니다. 실제 상태는 `project.md`를 확인합니다. 2026-10-25 업로드된 [공식 모집요강 PDF](<공공 웹사이트 불법광고 탐지 도구 개발 공모전 모집요강.pdf>) 18쪽을 대조했습니다. 필수 4종·평가 배점·제출 서류는 요구사항정의서, 출력 표/예시는 wiki를 따릅니다. 별도 공식 JSON Schema 파일을 받은 것은 아닙니다.

## 구성과 현재 상태

Python, FastAPI, Uvicorn, httpx, BeautifulSoup4, html5lib 및 HTML/JavaScript를 사용합니다. HTML5 파싱으로 브라우저의 tbody 삽입 등을 반영합니다. 선택 가능한 동적 분석은 Playwright와 Microsoft Edge를 사용합니다. 설치·검증 기준은 **Windows 11 x64 / CPython 3.14.6**이며 다른 Python·OS 조합은 미검증입니다. 상세 구조는 [wiki.md](wiki.md)를 참조합니다.

최신 검증 결과는 [project.md](project.md)에서 관리합니다. 4종 위장/은닉 특징과 별도로 도박·성인물 홍보의 내용 후보를 판별합니다. 실제 누락 게시물 2건에서 제목·본문 후보를 확인했고, 교육청 예방자료에서는 내용 후보가 없었습니다. 고정 환경·정적/동적 수집·위치·화면·다운로드를 검증했으며 전체 광고 판정 정확도 측정은 남아 있습니다.

## 설치 및 실행

CPython 3.14.6(64비트)을 설치하고 프로젝트 루트에서 PowerShell로 실행합니다. `python --version`으로 사용할 버전을 먼저 확인합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

브라우저 주소: http://127.0.0.1:8000

문서의 기본 포트는 8000입니다. UI가 같은 서버의 상대 API 경로를 사용하므로 다른 포트에서도 해당 서버 주소로 화면을 열면 됩니다.

`python` 명령이 실행되지 않으면 설치된 Python 실행 파일의 전체 경로로 가상환경을 생성합니다. 개인 PC의 절대 경로는 공통 절차에 고정하지 않습니다. 위 명령은 가상환경 활성화 없이 사용할 수 있습니다.

서버 종료는 해당 터미널에서 `Ctrl+C`를 누릅니다. `.venv`는 로컬 실행 환경이며 Git에 포함하지 않습니다.

| 설치 파일 | 포함 범위 |
|---|---|
| requirements.txt | 기본 분석·API 실행 |
| requirements-browser.txt | 기본 실행 + 동적 분석용 Playwright |
| requirements-dev.txt | 동적 분석 환경 + pytest·전체 검증 |

모든 설치 경로는 `constraints-windows-py314.txt`의 하위 의존성 고정 버전을 공유합니다. constraints는 버전만 제한하므로 기본 설치 시 pytest·Playwright를 추가하지 않습니다. 기준 pip는 26.1.2입니다. 기존의 Pydantic 2.9.2 조합은 Python 3.14용 pydantic-core 휠 설치에서 실패해 검증된 버전으로 갱신했습니다.

기동 절차만 자동 확인하려면 다음 명령을 실행합니다. 임시 포트에서 서버를 열어 health·화면·OpenAPI·잘못된 입력 거부를 확인하고 종료합니다. 외부 사이트 분석이나 기존 result.json 변경은 하지 않습니다.

```powershell
.\.venv\Scripts\python.exe -B scripts/smoke_test.py
```

## 동적 페이지 분석

기본 분석은 HTTP 응답 HTML을 사용합니다. JavaScript가 본문·댓글·iframe을 생성하는 페이지는 화면의 **동적 페이지 분석**을 선택합니다. 이 모드는 서버 PC에 Microsoft Edge와 다음 선택 의존성이 필요합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements-browser.txt
```

별도의 Playwright Chromium 다운로드는 필요하지 않습니다. 설치된 Edge를 headless로 실행하며 개인 브라우저의 로그인·프로필을 사용하지 않습니다. 설치·실행이 불가능하면 HTTP 503으로 안내하고 기존 결과 파일을 보존합니다. 기본 분석에는 Playwright가 필요하지 않습니다.

API 예시:

```json
{"url": "https://example.com", "collection_mode": "browser", "render_wait_ms": 500}
```

`collection_mode`는 `static`(기본) 또는 `browser`입니다. 동적 모드는 DOMContentLoaded 후 `render_wait_ms`만큼 추가 대기합니다(기본 500ms, 0~5000). 브라우저 시작·이동·대기·수집·탐지는 같은 시간 예산을 사용합니다. 실제 프레임을 읽어 부모 JS가 바꾼 내용과 반복 삽입 위치를 보존합니다. 분석 방식은 API 응답·화면 요약에 표시하며 제출용 JSON 규격은 유지합니다.

동적 모드는 대기 시점의 DOM과 계산된 스타일·문서 좌표를 함께 수집합니다. 내부/외부 CSS 클래스, 상위 요소 opacity:0·display:none, 상속된 visibility·작은 글꼴, 투명 글자·같은 불투명 단색 배경, 요소 전체가 문서의 음수 영역에 있는 배치를 확인합니다. 화면에 일부 보이는 음수 배치나 스크롤 아래의 정상 콘텐츠를 은닉으로 간주하지 않으며 글자 그림자·윤곽선이 있으면 색상만으로 투명 판정하지 않습니다. 기본 정적 모드는 기존 inline 후보 규칙이므로 CSS의 실제 표시 상태가 필요하면 동적 모드를 사용합니다.

자동 스크롤·클릭·로그인·Shadow DOM·SVG 스타일·가상 요소·이미지/OCR, iframe 요소 자체의 숨김이 자식 프레임에 미치는 영향은 아직 지원하지 않습니다. 이미지/그라데이션/반투명 배경의 색상 합성이나 일반적인 가림·clip·양의 방향 화면 밖 판정도 범위 밖입니다. 대기 이후 콘텐츠·변경된 DOM 위치와 실제 광고 판정 정확도를 보장하지 않습니다. 외부 프레임은 분석에서 제외하지만 하위 리소스·외부 요청을 차단하지는 않습니다. 문서 수·깊이 제한은 분석 컨텍스트에 적용하며 브라우저 총 요청 수 제한이 아닙니다.

## 분석 한도

현재 UI는 기본값(링크 깊이 2, 수집·탐지 공유 시간 예산 60초)을 사용합니다. API에서는 다음과 같이 지정할 수 있습니다.

```json
{"url": "https://example.com", "max_depth": 2, "total_timeout_sec": 60}
```

시작 페이지의 깊이는 0이며 iframe은 같은 링크 깊이를 유지합니다. iframe 깊이와 문서 수 제한은 별도로 적용합니다. 분석 완료 전 시간 초과는 HTTP 504이고, 완료한 페이지가 있으면 해당 결과와 warnings를 반환합니다. 시간 제한은 처리 구간 사이에서 확인하는 방식으로 네트워크 대기·파싱을 즉시 강제 종료하지 않습니다. 세부 기준과 기본값은 [wiki.md](wiki.md)의 4·8절을 참조합니다.

## JSON 다운로드

분석 완료 후 **JSON 다운로드**는 필수 4종의 `result.json`, **추가 탐지 결과 다운로드**는 `result_extra.json`, **광고 후보 다운로드**는 검수용 `content-candidates.json`을 저장합니다. 모두 화면 필터와 관계없이 마지막 분석의 전체 해당 결과를 포함하며 기본·동적·부분·0건을 지원합니다. 분석 전·새 분석 진행 중·요청 실패·빈 URL 제출 후에는 버튼을 비활성화합니다.

현재 화면이 보관한 API 응답의 `result_json`을 UTF-8(BOM 없음)으로 저장합니다. 서버 파일과의 일치는 파싱한 JSON 값 기준으로 검증합니다. 다른 화면의 분석이 서버 파일을 바꾸더라도 현재 화면의 결과를 내려받습니다. 부분 분석의 warnings는 화면에서 확인해야 하며 제출 JSON에는 포함하지 않습니다.

내용 후보는 API의 `content_candidates`에 GAMBLING/ADULT_CONTENT로 반환합니다. 위치·문맥·일치 표현·연결된 4종 기법·규칙 버전과 `review_status: needs_review`를 포함합니다. 후보 파일에는 수집 방식·분석 메타데이터·경고·규칙 버전도 저장합니다. 일반 표시 광고는 임의의 technique을 붙여 기존 제출 JSON에 넣지 않습니다.

추가 결과는 PDF 13쪽 예시처럼 `technique: ETC`와 `extra_finding`에 `GAMBLING_PROMOTION_CANDIDATE` 또는 `ADULT_CONTENT_PROMOTION_CANDIDATE`를 기록합니다. API의 `result_extra_json`, 서버 파일과 해당 다운로드가 같은 값을 사용합니다. 후보를 확정된 법적 위반으로 변환하지 않으며 추가 결과에는 is_violation을 자동 기재하지 않습니다. 두 제출 파일의 meta.topic은 PDF 표/예시의 `TOPIC`입니다. 제출 evidence_text는 설명·정규화·길이 제한 없이 DOM 원문 텍스트를 보존하고 화면 evidence는 설명용으로 유지합니다.

현재 content-rules-v4는 같은 텍스트 블록·문장 안의 도박/성인물 표현과 가입·이용·시청 유도 표현을 검사합니다. 자모 재조합·전각·제한된 닮은꼴 문자·대소문자·공백·일부 zero-width 변형은 판별용으로만 정리하며 제출 근거는 원문으로 유지합니다. 예방교육·단속 보도·광고 신고/삭제 요청 등 명시적인 정상 문맥은 제외합니다. 별도 문장의 예방 안내는 홍보 후보를 지우지 않으며 도메인 내부 마침표는 유지합니다. 여러 문장에 걸친 홍보·인용 보도, 구두점 없는 문장, 사전 밖 은어·변형·이미지에는 미탐·오탐이 남습니다.

## 제출 후보와 검토 대상

결과 화면에는 발견 원문·유형·제출 후보/검토 필요 상태·이유·페이지/위치를 카드로 표시합니다. 홍보 내용 후보와 수집 경고도 별도로 보이며, 상세 JSON은 접힌 영역에 보관합니다. 전체 집계와 현재 필터의 표시 건수를 구분하고 다운로드는 계속 전체 결과를 저장합니다. 이전 고정 confidence 값은 검증된 확률이 아니므로 API/화면에서 제거했고 finding.source_text를 API에 추가했습니다. 필수 제출 파일 형식은 유지합니다.

JAMO의 완전한 연속 자모 구간이 ㅋ/ㅎ 두 글자 이상으로만 구성되면 일상 웃음 표현으로 제외합니다. 단독 자음·다른 자모·모음이 있는 분리 표현은 계속 탐지하고 CSS 특징은 별도입니다. content-rules-v4는 이 웃음 구간을 앞 단어의 받침으로 잘못 합치지 않아 광고 뒤 ㅋㅋ/ㅎㅎ가 붙어도 관련 어휘를 유지합니다. 모든 정상 자모·우회 표현을 해결한 것은 아닙니다.

feature-content-policy-v1은 위장·은닉 구간이 관련 홍보 주제나 이용 유도 표현의 원문 구간과 겹칠 때만 4종 제출 후보로 포함합니다. 같은 문단의 무관한 숨김 메뉴나 외국어·전각 인사말을 광고 기법으로 연결하지 않습니다. 화면에는 모든 특징과 submission_status/reason을 남기고 제출 후보와 검토 대상 수를 따로 표시합니다.

| 관찰 결과 | 저장·표시 |
|---|---|
| 특징과 관련 홍보 구간이 겹침 | included, result.json에 규칙상 is_violation=true |
| 특징만 있거나 홍보와 무관한 구간 | needs_review, 화면에 보존하고 result.json에서는 제외 |
| 일반 표시 홍보 후보만 있음 | content_candidates 및 result_extra.json, 필수 기법을 임의로 붙이지 않음 |

기존의 is_violation 기본 true 변환을 제거했습니다. 근거 부족을 false(정상)로 바꾸지도 않습니다. 이 정책은 자동 제출 후보 선택 규칙이며 법적 위반 확정이나 실측 정확도가 아닙니다. 어휘·정규화·문맥을 놓치면 실제 광고도 검토 대상으로 남을 수 있으므로 파일 0건만으로 광고 부재를 판단하지 않습니다. 다운로드는 화면 필터와 관계없이 전체 **선택된 제출 후보**를 저장합니다.

## 내용 후보 정답 검수와 평가

합성 문장 문맥 사례 22개를 다음 명령으로 비교할 수 있습니다. 출력은 합성 회귀 데이터의 점수이며 실제 사이트 정확도가 아닙니다. 사례와 선정 기준은 `tests/fixtures/content/`에 있습니다. `--output`으로 지정한 파일이 이미 있으면 보존을 위해 오류로 종료합니다.

```powershell
.\.venv\Scripts\python.exe -B scripts/benchmark_content.py
.\.venv\Scripts\python.exe -B scripts/benchmark_content.py --output .validation/content-benchmark-new.json
```

새 capture는 4종 기법용 `labels.json`과 독립된 `content-labels.json`을 생성합니다. 이전 capture에는 다음 명령으로 내용 정답 초안을 추가할 수 있습니다. 기존 정답 파일은 덮어쓰지 않습니다.

capture와 evaluate는 submission_assessments·submission_policy_version도 별도로 기록합니다. 보고서의 submission_candidate_count는 제출 선택 건수이며 기존 feature/content 지표를 광고 판정 정확도로 바꾸지는 않습니다. 각 특징의 선택·검토 이유와 정책/정규화 코드 해시를 확인할 수 있습니다.

```powershell
.\.venv\Scripts\python.exe -B scripts/validate_site.py init-content-labels .validation/run-001
.\.venv\Scripts\python.exe -B scripts/validate_site.py evaluate .validation/run-001 --kind content
```

`content-labels.json`은 `url`, `location`, `category`(GAMBLING/ADULT_CONTENT)를 기준으로 내용 존재 여부를 검수합니다. `location`은 후보를 소유하는 텍스트 블록의 선택자이며 iframe 경로는 ` >>> `로 연결합니다. 같은 블록의 두 범주는 각각 독립된 정답입니다. 후보뿐 아니라 놓친 홍보 블록과 정상 블록도 직접 추가하고 `expected`, `reviewed`, `reason`을 기록합니다. 선택자는 저장된 문서에서 정확히 한 요소를 가리켜야 합니다.

`complete: false`에서는 검수한 항목의 TP/FP/FN/TN만 집계하며 미검수 후보를 오탐으로 간주하지 않습니다. 저장된 모든 문서의 양성 블록·범주를 빠짐없이 검수한 뒤에만 `complete: true`와 판정 기준 `policy`를 기록합니다. 이때만 precision/recall/F1을 계산하며, 양성 정답 목록 밖 후보는 FP입니다. 분모가 0인 지표는 `null`입니다. 수집 제외·실패 범위는 점수에 포함되지 않습니다.

결과는 `content-report.json`에 저장하고 기존 4종 기법 `report.json`과 분리합니다. `metrics_purpose: content_presence_only`, 범주별 집계, 원본·정답·평가 코드 해시, 규칙 버전과 수집 경고를 포함합니다. 검수된 내용 존재와 법적 위반 판단은 별개입니다. 선택적 `violation_verdict`는 기본 `unreviewed`이며, `uncertain`/`violation`/`non_violation`을 기록하려면 해당 내용 항목 검수와 `reviewer`, `verdict_reason`이 필요합니다. 이 기록은 내용 점수나 API·제출 JSON을 변경하지 않습니다.

실제 gen.go.kr 저장본은 본문에 한정해 홍보 글 107·151 각각 TP 1, 예방교육 글 454470에서 두 범주 TN 2를 검수했습니다. 제목 등 미검수 범위가 남아 지표는 모두 `null`입니다. 전체 사이트 정확도나 법적 판정 결과가 아닙니다.

## 테스트

전체 개발·검증 패키지를 설치합니다. 실제 브라우저 검사는 설치된 Microsoft Edge가 필요합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest tests -q
```

프론트엔드의 필터 전환·전체 복귀·오류 후 초기화는 Node.js가 설치된 환경에서 다음과 같이 검증합니다. DOM·API 대역을 사용하는 스크립트 검사이며 실제 브라우저 검증은 별도입니다.

```powershell
node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
```

통과 여부는 실제 실행 결과로 판단하며 최신 검증 범위와 실패 원인은 [project.md](project.md)에 기록합니다.

실제 브라우저 검사는 Windows의 설치된 Microsoft Edge와 Playwright를 사용합니다. 기본 분석 검증과 동적 분석 검증을 함께 실행합니다.

```powershell
.\.venv\Scripts\python.exe -B scripts/test_browser.py
```

로컬 임시 서버를 열어 표·특수문자 ID·반복/중첩 iframe·srcdoc 위치, UI 필터·부분 결과·실패 복구·정상 0건을 검사합니다. JS 생성 본문·fetch 댓글·링크·프레임의 기본 분석 0건과 동적 분석 11건, 위치·파일 일치·502/504 파일 보존도 확인합니다. 실제 다운로드의 파일명·UTF-8·API 결과 일치·필터 독립성·부분/빈 결과·화면별 결과 보존을 확인합니다. 결과는 임시 디렉터리로 격리하고 서버와 브라우저를 종료합니다. 외부 사이트 정확도 검사와는 별도입니다.

2026-10-25 재현 환경은 Python 3.14.6·pip 26.1.2·Edge 156.0.4314.42·Node 20.12.2입니다. Edge는 별도 설치 앱이므로 버전이 바뀌면 브라우저 검사를 다시 확인합니다. 버전 변경 시 격리 환경의 설치·pip check·Python·Node·브라우저·기동 검증을 마친 뒤 requirements와 constraints를 함께 갱신합니다.

## 사이트 수집·정답 비교

검증할 실제 URL과 판정 기준을 정한 뒤 실행합니다. 다음 도구는 **4종 특징 탐지**를 평가하며 불법광고 여부의 정확도를 확정하지 않습니다.

```powershell
$targetUrl = Read-Host "검증할 공개 페이지 URL"
.\.venv\Scripts\python.exe -B scripts/validate_site.py capture $targetUrl --output .validation/run-001 --mode static --max-depth 0
.\.venv\Scripts\python.exe -B scripts/validate_site.py evaluate .validation/run-001
```

동적 페이지에는 `--mode browser`를 사용합니다. 기본 한도는 링크 깊이 0·문서 컨텍스트 8·프레임 깊이 3·공유 시간 60초입니다. `--max-depth`, `--total-timeout-sec`, `--render-wait-ms`로 범위를 조정할 수 있습니다. 기존 폴더는 덮어쓰지 않으므로 새 수집에는 다른 run 이름을 사용합니다. 전체 수집 실패는 종료 코드 2이며 정상 0건으로 취급하지 않습니다.

수집 폴더에는 HTML, 입력·수집 시각·프레임 경로·해시·4종 탐지·내용 후보·제외/실패 사유를 담은 capture.json, 검수용 labels.json이 생깁니다. 새 동적 수집은 rendered_style 관찰값도 보존하므로 브라우저·네트워크 없이 계산 스타일을 다시 판별할 수 있습니다. 예전 저장본에 관찰값이 없으면 정적 규칙으로 평가합니다. 보고서의 observation_basis에서 rendered_documents/static_documents 수를 확인합니다. `.validation/`은 Git에서 제외되며 앱 결과 파일은 변경하지 않습니다. labels.json 지표는 4종 특징 검수용이고 내용 후보는 별도 정답 검수가 필요합니다.

labels.json은 초기에는 `complete: false`, 각 후보는 `expected: null`, `reviewed: false`입니다. 후보뿐 아니라 놓친 요소와 정상 사례도 저장된 문서에서 찾아 수동으로 추가합니다.

| 필드 | 검수 방법 |
|---|---|
| policy | 적용한 특징·정상 예외 기준과 버전을 기록 |
| url / location / technique | 저장된 문서의 최상위 URL·요소/프레임 경로·4종 유형 지정 |
| expected | 해당 기준의 특징이면 true, 정상이면 false, 판단 전은 null |
| reviewed / reason | 실제 검수 후 true와 판단 근거 기록 |
| complete | 저장된 문서 전체의 4종 양성 요소를 빠짐없이 검수한 경우에만 true |

capture_sha256는 해당 수집과 정답의 연결 값이므로 유지합니다. 검수 중에는 metrics가 null이며 미검토 탐지를 오탐으로 세지 않습니다. 모든 항목 검수와 policy 기록 후 complete를 true로 바꾸고 evaluate를 다시 실행하면 report.json에 TP·FP·FN·명시적 정상 TN과 유형별 precision·recall·F1을 기록합니다. 전체 검수에서는 정답 양성 목록 밖의 탐지가 FP입니다. 분모가 없는 지표는 null입니다.

평가는 **저장에 성공한 문서 범위**에 한정합니다. report.json의 수집 경고와 미검토 수를 함께 확인합니다. 수집에서 빠진 페이지·화면 밖 리소스·광고 위반 판정 전체를 이 점수로 평가하지 않습니다. HTML 해시 불일치·다른 수집의 정답·중복/잘못된 요소 경로는 거부합니다. evaluate는 저장된 HTML만 읽으며 재접속하지 않습니다.

PDF 12쪽 URL 동등성(http/https·끝 슬래시·fragment 무시, 쿼리 순서 무시/값 구분)과 같은 요소를 가리키는 선택자 별칭을 평가에 반영합니다. 수집 URL 자체를 이 규칙으로 바꾸지는 않습니다. 동등 URL의 저장 문서가 서로 다르면 평가를 거부하므로 정답과 저장 문서의 문맥을 확인합니다.

2026-10-25 광주 교육청 어린이 게시판의 [도박 홍보성 게시물](https://gen.go.kr/child/xboard/board.php?mode=view&number=107&tbnum=6)과 [성인물 홍보성 게시물](https://gen.go.kr/child/xboard/board.php?mode=view&number=151&tbnum=6)에 기존 분석이 0건을 반환했던 문제를 확인했습니다. 내용 판별 추가 후 API는 게시물마다 제목·본문 2개씩 후보를 반환합니다. 4종 기법은 여전히 0건이며 내용 후보와 구분합니다. 같은 교육청의 [예방 홍보 자료](https://gen.go.kr/xboard/board.php?mode=view&number=454470&tbnum=520)는 내용 후보 0건을 확인했습니다. 전체 사이트 정확도 수치가 아니며 근거·범위는 project.md 19~20절을 따릅니다.
