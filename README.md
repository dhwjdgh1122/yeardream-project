# YearDream — 공공 웹사이트 불법광고 탐지 도구

URL을 시작으로 하위 페이지·게시글·댓글·iframe·중첩 iframe을 탐색하고 HOMOGLYPH·JAMO·TRANSPARENT·OFFSCREEN을 탐지합니다. 정확한 요소 위치와 근거를 `result.json` 및 결과 화면으로 제공합니다.

사용자 1명이 구현·탐지 기준·데이터 구성·정확도 검증을 모두 담당하며 코딩 에이전트가 이를 돕습니다.

## 문서 안내

| 문서 | 관리하는 기준 |
|---|---|
| [요구사항정의서.md](요구사항정의서.md) | 요구사항 ID, 필수 범위, 담당 역할, 통과 기준 |
| [wiki.md](wiki.md) | 구조, 탐지 기준, API, location, 결과 데이터 규격 |
| [README.md](README.md) | 설치·실행·테스트 절차와 문서 진입점 |
| [project.md](project.md) | 확인 날짜, 현재 상태, 검증 근거, 문제, 다음 작업 |
| [project-guide.md](project-guide.md) | 작은 단위 개발, 설명·검증·보고 방식 |

요구사항과 설계는목표 기준이며 구현 완료를 뜻하지 않습니다. 실제 상태는 `project.md`를 확인합니다. 공모전 공식 모집요강·출력 스키마는 아직 원문 대조 전이며, 확보되면 최우선으로 적용합니다.

## 구성과 현재 상태

Python, FastAPI, Uvicorn, httpx, BeautifulSoup4, html5lib 및 HTML/JavaScript를 사용합니다. HTML5 파싱으로 브라우저의 tbody 삽입 등을 반영합니다. 선택 가능한 동적 분석은 Playwright와 Microsoft Edge를 사용합니다. Python 지원 버전은 추가 검증 후 확정합니다. 상세 구조는 [wiki.md](wiki.md)를 참조합니다.

최신 검증 결과는 [project.md](project.md)에서 관리합니다. 고유 selector·중첩/반복 iframe 경로·API/JSON 위치 보존에 더해 링크 깊이·수집/탐지 공유 시간 예산을 구현했습니다. 로컬 합성 페이지의 실제 Edge 검사로 위치 재식별과 UI 흐름을 확인했습니다. 실제 사이트·광고 판정 정확도와 requirements.txt의 고정 버전 환경은 아직 확인하지 않았습니다.

## 설치 및 실행

프로젝트 루트에서 PowerShell로 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

브라우저 주소: http://127.0.0.1:8000

문서의 기본 포트는 8000입니다. UI가 같은 서버의 상대 API 경로를 사용하므로 다른 포트에서도 해당 서버 주소로 화면을 열면 됩니다.

`python` 명령이 실행되지 않으면 설치된 Python 실행 파일의 전체 경로로 가상환경을 생성합니다. 개인 PC의 절대 경로는 공통 절차에 고정하지 않습니다. 위 명령은 가상환경 활성화 없이 사용할 수 있습니다.

## 동적 페이지 분석

기본 분석은 HTTP 응답 HTML을 사용합니다. JavaScript가 본문·댓글·iframe을 생성하는 페이지는 화면의 **동적 페이지 분석**을 선택합니다. 이 모드는 서버 PC에 Microsoft Edge와 다음 선택 의존성이 필요합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-browser.txt
```

별도의 Playwright Chromium 다운로드는 필요하지 않습니다. 설치된 Edge를 headless로 실행하며 개인 브라우저의 로그인·프로필을 사용하지 않습니다. 설치·실행이 불가능하면 HTTP 503으로 안내하고 기존 결과 파일을 보존합니다. 기본 분석에는 Playwright가 필요하지 않습니다.

API 예시:

```json
{"url": "https://example.com", "collection_mode": "browser", "render_wait_ms": 500}
```

`collection_mode`는 `static`(기본) 또는 `browser`입니다. 동적 모드는 DOMContentLoaded 후 `render_wait_ms`만큼 추가 대기합니다(기본 500ms, 0~5000). 브라우저 시작·이동·대기·수집·탐지는 같은 시간 예산을 사용합니다. 실제 프레임을 읽어 부모 JS가 바꾼 내용과 반복 삽입 위치를 보존합니다. 분석 방식은 API 응답·화면 요약에 표시하며 제출용 JSON 규격은 유지합니다.

이는 대기 시점의 DOM 수집입니다. 자동 스크롤·클릭·로그인·Shadow DOM·computed style 판정은 지원하지 않으며, 대기 이후의 콘텐츠·변경되는 DOM 위치는 보장하지 않습니다. 외부 프레임은 분석에서 제외하지만 브라우저가 로딩하는 하위 리소스·외부 요청을 차단하는 기능은 아닙니다. 문서 수·깊이 제한은 분석 컨텍스트에 적용하며 브라우저의 총 요청 수 제한이 아닙니다.

## 분석 한도

현재 UI는 기본값(링크 깊이 2, 수집·탐지 공유 시간 예산 60초)을 사용합니다. API에서는 다음과 같이 지정할 수 있습니다.

```json
{"url": "https://example.com", "max_depth": 2, "total_timeout_sec": 60}
```

시작 페이지의 깊이는 0이며 iframe은 같은 링크 깊이를 유지합니다. iframe 깊이와 문서 수 제한은 별도로 적용합니다. 분석 완료 전 시간 초과는 HTTP 504이고, 완료한 페이지가 있으면 해당 결과와 warnings를 반환합니다. 시간 제한은 처리 구간 사이에서 확인하는 방식으로 네트워크 대기·파싱을 즉시 강제 종료하지 않습니다. 세부 기준과 기본값은 [wiki.md](wiki.md)의 4·8절을 참조합니다.

## JSON 다운로드

분석 완료 후 **JSON 다운로드**를 누르면 `result.json`을 저장합니다. 화면의 유형 필터와 관계없이 마지막으로 완료한 분석의 전체 제출용 결과를 포함합니다. 기본·동적 분석, 부분 결과, 탐지 0건 결과를 지원합니다. 분석 전·새 분석 진행 중·요청 실패·빈 URL 제출 후에는 버튼을 비활성화합니다.

현재 화면이 보관한 API 응답의 `result_json`을 UTF-8(BOM 없음)으로 저장합니다. 서버 파일과의 일치는 파싱한 JSON 값 기준으로 검증합니다. 다른 화면의 분석이 서버 파일을 바꾸더라도 현재 화면의 결과를 내려받습니다. 부분 분석의 warnings는 화면에서 확인해야 하며 제출 JSON에는 포함하지 않습니다.

## 테스트

현재 `requirements.txt`에 pytest가 없어 별도로 설치합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest tests -q
```

프론트엔드의 필터 전환·전체 복귀·오류 후 초기화는 Node.js가 설치된 환경에서 다음과 같이 검증합니다. DOM·API 대역을 사용하는 스크립트 검사이며 실제 브라우저 검증은 별도입니다.

```powershell
node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
```

통과 여부는 실제 실행 결과로 판단하며 최신 검증 범위와 실패 원인은 [project.md](project.md)에 기록합니다.

실제 브라우저 검사는 Windows의 설치된 Microsoft Edge와 Playwright를 사용합니다. 기본 분석 검증과 동적 분석 검증을 함께 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-browser.txt
.\.venv\Scripts\python.exe -B scripts/test_browser.py
```

로컬 임시 서버를 열어 표·특수문자 ID·반복/중첩 iframe·srcdoc 위치, UI 필터·부분 결과·실패 복구·정상 0건을 검사합니다. JS 생성 본문·fetch 댓글·링크·프레임의 기본 분석 0건과 동적 분석 11건, 위치·파일 일치·502/504 파일 보존도 확인합니다. 실제 다운로드의 파일명·UTF-8·API 결과 일치·필터 독립성·부분/빈 결과·화면별 결과 보존을 확인합니다. 결과는 임시 디렉터리로 격리하고 서버와 브라우저를 종료합니다. 외부 사이트 정확도 검사와는 별도입니다.
