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

Python, FastAPI, Uvicorn, httpx, BeautifulSoup4, html5lib 및 HTML/JavaScript를 사용합니다. HTML5 파싱으로 브라우저의 tbody 삽입 등을 반영합니다. 수집용 브라우저 렌더링 도구와 Python 지원 버전은 추가 검증 후 확정합니다. 상세 구조는 [wiki.md](wiki.md)를 참조합니다.

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

## 분석 한도

현재 UI는 기본값(링크 깊이 2, 수집·탐지 공유 시간 예산 60초)을 사용합니다. API에서는 다음과 같이 지정할 수 있습니다.

```json
{"url": "https://example.com", "max_depth": 2, "total_timeout_sec": 60}
```

시작 페이지의 깊이는 0이며 iframe은 같은 링크 깊이를 유지합니다. iframe 깊이와 문서 수 제한은 별도로 적용합니다. 분석 완료 전 시간 초과는 HTTP 504이고, 완료한 페이지가 있으면 해당 결과와 warnings를 반환합니다. 시간 제한은 처리 구간 사이에서 확인하는 방식으로 네트워크 대기·파싱을 즉시 강제 종료하지 않습니다. 세부 기준과 기본값은 [wiki.md](wiki.md)의 4·8절을 참조합니다.

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

실제 브라우저 검사는 Windows의 설치된 Microsoft Edge와 Playwright를 사용합니다. Playwright는 검증 도구이며 앱 실행에 필요하지 않습니다.

```powershell
.\.venv\Scripts\python.exe -m pip install playwright==1.64.0
.\.venv\Scripts\python.exe -B scripts/test_browser.py
```

로컬 임시 서버를 열어 표의 DOM 보정·특수문자 ID·반복/중첩 iframe·srcdoc 위치, UI 필터·부분 결과·실패 후 복구·정상 0건을 검사합니다. 결과 파일은 임시 디렉터리로 격리하고 서버와 브라우저는 종료합니다. JS가 추가한 요소는 브라우저에 존재해도 현재 정적 수집에서 탐지되지 않는 한계를 함께 확인합니다. 외부 사이트 정확도 검사와는 별도입니다.
