# YearDream — 공공 웹사이트 불법광고 탐지 도구

## 문서 역할과 읽는 순서

이 문서는 **프로젝트 소개와 설치·실행·검증 명령의 진입점**입니다. 기능 요구·기술 규격·진행 이력은 각 기준 문서에서 관리합니다. 아래 명령은 필요할 때 사용하는 안내이며 이번 문서 점검에서 실행하는 작업 목록이 아닙니다.

| 핵심 문서 | 담당하는 내용 | 다른 문서에서 관리하는 내용 |
|---|---|---|
| [README.md](README.md) | 소개·설치·실행·검증 도구 명령·문서 안내 | 요구사항 상세·기술 계약·실행 이력 |
| [요구사항정의서.md](요구사항정의서.md) | 공식 요구 범위·FR/NFR·통과 기준·FS 기능 명세 | 실제 통과 여부·화면 배치·DB 물리 구조 |
| [wiki.md](wiki.md) | 아키텍처·수집/탐지·API·location·결과 규격·향후 방향 | 설치 절차·날짜별 검사 결과 |
| [project.md](project.md) | 현재 상태·검증 근거·알려진 문제·남은 일·과거 기록 | 새로운 요구사항·기술 규격 정의 |
| [project-guide.md](project-guide.md) | 작업 범위·변경·검증·보고·Git·문서 유지 원칙 | 초기 개발 순서 반복·기술 명세·진행 현황 |

처음 사용하는 사람은 이 문서와 [사용 설명서](docs/USER_MANUAL.md)를, 기능·설계를 확인하는 사람은 요구사항정의서와 wiki를, 실제 확인 범위를 확인하는 사람은 project.md를 읽습니다. 별도 [화면설계서](docs/SCREEN_DESIGN.md)와 [DB 설계서·ERD](docs/DATABASE_DESIGN.md)는 화면 구성과 물리 저장 구조의 기준입니다.

## 프로젝트와 현재 제공 범위

사용자가 자기 PC에서 실행하는 **웹 화면 기반 로컬 탐지·검토 도구**입니다. 입력한 공개 HTTP(S) URL에서 링크·게시글·댓글·iframe을 설정 한도 안에서 수집·분석하고 필수 4종 위장·은닉 특징과 도박/성인물 홍보 내용 후보를 구분합니다. 결과·원문/위치·SQLite 이력을 해당 PC에 저장합니다.

중앙 서버에 배포한 공동 서비스가 아니며 외부 AI API·로컬 생성 모델·RAG는 사용하지 않습니다. DB 이력·후보 검토는 구현되어 있고 플랫폼·사례 검색·RAG 확장은 [향후 발전 방향](wiki.md#future-roadmap)으로 보류했습니다.

현재 dist에는 **release-20261025-08 하나만 유지**합니다. 이전 실행 배포본과 제출 묶음은 사용자 요청으로 삭제했습니다. 실행 ZIP과 전체 소스·설계서·공식 서류를 합친 제출 묶음은 다르며 새 전체 제출 묶음은 아직 만들지 않았습니다. 사용자 확인·검사·알려진 한계는 [project.md](project.md#3-현재-요약)를 따릅니다.

## Windows 실행 파일

현재 실행본은 `dist/release-20261025-08/YearDream/YearDream.exe`입니다. 프로젝트 루트의 PowerShell에서 실행합니다.

```powershell
.\dist\release-20261025-08\YearDream\YearDream.exe
```

다른 PC에는 같은 release 폴더의 `YearDream-windows-x64.zip`을 전달하고 **전체 압축 해제**한 뒤 exe를 실행합니다. Python 런타임은 포함되어 있고 동적 분석에는 설치된 Microsoft Edge가 필요합니다. exe만 따로 복사하지 않습니다.

기본 브라우저가 열리며 주소는 `http://127.0.0.1:8000`입니다. 포트가 사용 중이면 명령 뒤에 `--port 8010`, 브라우저 자동 열기를 생략하려면 `--no-browser`를 붙입니다. 콘솔에서 `Ctrl+C`로 종료하며 탭만 닫아서는 서버가 종료되지 않습니다. 이전 화면이면 실행 경로·주소를 확인하고 `Ctrl+F5`로 새로고침합니다. 자세한 절차는 [사용 설명서](docs/USER_MANUAL.md)를 따릅니다.

## 빌드·제출 준비 안내

실행 ZIP은 구동 파일과 생성 당시의 사용/빌드 설명서를 담습니다. 전체 소스·최신 설계서·공식 서류를 합친 제출 묶음은 별도이며 현재 새 묶음을 만들지 않았습니다. 과거 제출 후보는 삭제했고 생성/검사 기록만 project.md에 보존합니다.

필요 시 새 빌드·패키지 검사·전체 제출 묶음 생성 명령은 [빌드 설명서](docs/BUILD_MANUAL.md)를 따릅니다. `scripts/build_windows.py`와 `scripts/package_submission.py`는 기존 폴더를 덮어쓰지 않고 새 출력 경로를 사용합니다. **이번 문서 점검에서는 빌드·프로그램 검사·제출 묶음 생성을 수행하지 않습니다.**

서류·서명·접수 확인은 [제출 점검표](docs/SUBMISSION_CHECKLIST.md), 환경별 사용자 확인은 [다른 PC 점검표](docs/OTHER_PC_CHECKLIST.md), 실사이트 결과 보관/해석은 [실사이트 확인표](docs/SITE_VALIDATION_CHECKLIST.md)를 참조합니다. 제출 조건의 공식 기준은 요구사항정의서 4절이며 실행 ZIP 보관이나 제출 후보 생성은 공식 접수 완료를 뜻하지 않습니다.

## 구성과 현재 상태

Python, FastAPI, Uvicorn, httpx, BeautifulSoup4, html5lib 및 HTML/JavaScript를 사용합니다. HTML5 파싱으로 브라우저의 tbody 삽입 등을 반영합니다. 선택 가능한 동적 분석은 Playwright와 Microsoft Edge를 사용합니다. 설치·검증 기준은 **Windows 11 x64 / CPython 3.14.6**이며 다른 Python·OS 조합은 미검증입니다. 상세 구조는 [wiki.md](wiki.md)를 참조합니다.

최신 검증 수치·사용자 확인·알려진 문제는 [project.md](project.md)에만 요약하고, 기술별 상세 범위는 wiki를 참조합니다.

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

모든 설치 경로는 `constraints-windows-py314.txt`의 하위 의존성 고정 버전을 공유합니다. constraints는 버전만 제한하므로 기본 설치 시 pytest·Playwright를 추가하지 않습니다. 기준 pip는 26.1.2입니다. 설치 조합 변경 경위는 project.md 17절을 참조합니다.

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

기본 분석은 응답 HTML을, 동적 분석은 관찰 시점의 DOM·계산 스타일을 사용합니다. 동적 분석이 모든 콘텐츠의 수집이나 더 높은 정확도를 보장하지는 않습니다. 자동 클릭·스크롤·로그인·OCR·Shadow DOM 등은 미지원입니다. 스타일·프레임·지원 한계의 기술 기준은 [wiki 4~5절](wiki.md#4-수집-규격)을 따릅니다.

위 요청 예시는 동기 `POST /api/analyze`용입니다. 화면은 `POST /api/jobs`를 사용하며 생성된 작업의 결과를 조회합니다. 비동기 작업의 실행 오류는 작업 상태 안의 error로 전달될 수 있습니다.

## 분석 한도

| 화면 설정 | 기본값 | 변경 가능한 범위·의미 |
|---|---|---|
| 문서 한도 | 100개 | 1~1,000개. 실패·iframe을 포함한 수집 시도 상한 |
| 링크 깊이 | 4단계 | 0~20단계. 시작 URL 0에서 링크 이동마다 1 증가 |
| 시간 예산 | 25분 | 1~30분. 수집·탐지 공유 예산이며 즉시 강제 종료는 아님 |

100개·4단계·25분은 고정 최대치가 아닌 시험 기본값입니다. 300개·깊이 11도 허용되며 시간 제한이나 링크 소진으로 더 적게 처리할 수 있습니다. iframe 진입 깊이는 별도 제한입니다. 공모전 지정 문서 수나 전수 탐지·엄격한 시간 준수 보장은 아닙니다.

진행 중에는 움직이는 막대·실제 건수·현재 URL·경과 시간을 표시하고 중단 요청 시 완료한 문서의 부분 결과를 반환합니다. 전체량이 미확정이므로 검사율·정확한 남은 시간은 표시하지 않습니다. 분석 안내는 사유별 건수로 묶고 원문·URL은 펼쳐 확인합니다. ‘전체 유형’은 결과 필터이며 탐색 범위를 늘리지 않습니다.

입력한 URL에서 설정한 한도 내에 탐색·분석한 결과입니다. 미방문하거나 접근하지 못한 페이지에는 탐지되지 않은 광고가 남아 있을 수 있습니다. 설정 예시·중단/재연결은 [사용 설명서](docs/USER_MANUAL.md#진행-표시설정중단-release-20261025-06), API별 기본값과 한도 계약은 [wiki](wiki.md#8-api와-ui)를 참조합니다.

## 결과 파일·이력·검토

| 파일·저장소 | 의미·위치 |
|---|---|
| result.json | 선택된 필수 4종 제출 후보. 실행 파일 옆, 소스 실행은 프로젝트 루트 |
| result_extra.json | 추가 홍보 후보. 위와 같은 위치 |
| content-candidates.json | 광고 후보 다운로드의 검수용 후보·범위·원문 안내 |
| history.sqlite3 | Windows의 `%LOCALAPPDATA%\YearDream`에 보관하는 분석 이력·검토 DB |

화면 다운로드는 브라우저 다운로드 설정에 따른 위치에 사본을 저장합니다. 세 다운로드는 표시 필터와 무관하게 현재 화면이 보관한 마지막 분석의 해당 전체 결과를 사용합니다. 완료 문서 없는 실패/중단은 이전 파일을 유지하며 새 다운로드는 비활성화합니다.

특징 발견·홍보 후보·필수 4종 제출 선택·사람의 검토는 구분합니다. 홍보 구간과 관련된 특징만 현 정책의 제출 후보로 선택하고 나머지는 검토 상태로 보존합니다. 일반 표시 홍보에 필수 기법을 임의 부여하지 않습니다. 0건은 광고 부재 확정이 아니며 후보 검출·검토는 법적 확정이 아닙니다. 원문·location·필드와 판정 계약은 [wiki 5~7절](wiki.md#5-탐지-기준)을 따릅니다.

‘분석 이력·후보 검토 관리’(`/history`)에서 분석을 다시 보고 검토자·이유와 함께 홍보/정상/보류 판단을 누적할 수 있습니다. 기존 제출 JSON은 바꾸지 않습니다. DB 저장 실패는 경고로 안내하고 현재 분석·다운로드를 유지합니다. 앱 종료 후 DB를 복사해 백업하며 실제 DB·원문/검토 기록은 Git·배포 ZIP에 넣지 않습니다. 과거 JSON을 자동으로 가져오지는 않습니다. 화면 사용법은 [사용 설명서](docs/USER_MANUAL.md), 저장 구조는 [DB 설계서](docs/DATABASE_DESIGN.md)를 참조합니다.

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

내용 정답은 검출 후보뿐 아니라 놓친/정상 블록도 직접 검수합니다. `complete:false`는 부분 검수이며 지표를 전체 정확도로 해석하지 않습니다. 정답 형식·완료 선언·평가 단위·법적 판단 메모의 규칙은 [wiki 9절](wiki.md#9-검증변경-원칙)을 따릅니다. 실제 검수 수치·근거는 [검증 기록](docs/VALIDATION.md)에 보존합니다.

## 테스트

아래는 개발자가 필요에 따라 사용하는 명령입니다. 변경 영향·실패 위험에 따라 검사 범위를 선택하며 문서만 변경할 때는 프로그램 테스트/빌드를 반복하지 않습니다. 실제 브라우저 검사에는 설치된 Microsoft Edge가 필요합니다.

```powershell
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
```

프론트엔드의 필터 전환·전체 복귀·오류 후 초기화는 Node.js가 설치된 환경에서 다음과 같이 검증합니다. DOM·API 대역을 사용하는 스크립트 검사이며 실제 브라우저 검증은 별도입니다.

```powershell
node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
```

통과 여부는 실제 실행 결과로 판단하며 최신 검증 범위와 실패 원인은 [project.md](project.md)에 기록합니다.

실제 브라우저 검사는 Windows에 설치된 Microsoft Edge와 Playwright를 사용합니다. 아래 스크립트는 기본·동적 분석 흐름을 함께 확인합니다.

```powershell
.\.venv\Scripts\python.exe -B scripts/test_browser.py
```

로컬 임시 서버를 열어 표·특수문자 ID·반복/중첩 iframe·srcdoc 위치, UI 필터·부분 결과·실패 복구·정상 0건을 검사합니다. JS 생성 본문·fetch 댓글·링크·프레임의 기본 분석 0건과 동적 분석 11건, 위치·파일 일치·502/504 파일 보존도 확인합니다. 실제 다운로드의 파일명·UTF-8·API 결과 일치·필터 독립성·부분/빈 결과·화면별 결과 보존을 확인합니다. 결과는 임시 디렉터리로 격리하고 서버와 브라우저를 종료합니다. 외부 사이트 정확도 검사와는 별도입니다.

과거 검사에서 기록한 재현 환경은 Python 3.14.6·pip 26.1.2·Edge 156.0.4314.42·Node 20.12.2입니다. Edge는 별도 설치 앱이므로 버전이 바뀌면 브라우저 검사를 다시 확인합니다. 버전 변경 시 격리 환경의 설치·pip check·Python·Node·브라우저·기동 검증을 마친 뒤 requirements와 constraints를 함께 갱신합니다.

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


## 저장본의 제출 후보 수동 검토

자동 규칙이 놓친 특징을 검토한 뒤 포함하거나, 자동 선택된 특징을 제외할 수 있습니다. 먼저 아래 capture 명령으로 저장본을 만들고, 해당 RUN 폴더에서 검토를 시작합니다. 제출 포함/제외를 정하는 이 기능은 CLI 전용이며, `/history`의 내용 분류 검토와 별개입니다.

```powershell
.venv\Scripts\python.exe -B scripts/review_submission.py init .validation/RUN
```

생성된 `submission-review.json`의 `items`를 편집합니다. 모든 항목의 최초 `decision`은 `pending`이며 자동 선택을 사람의 승인으로 취급하지 않습니다. 실제로 검토한 항목만 `include`(제출 포함) 또는 `exclude`(제출 제외)로 바꾸고, `reviewer`·`reason`·시간대가 있는 ISO 8601 `reviewed_at`을 기록합니다. 예: `2026-10-25T15:00:00+09:00`. `source_text`와 `capture_sha256`는 변경하지 않습니다.

```powershell
.venv\Scripts\python.exe -B scripts/review_submission.py export .validation/RUN --output .validation/RUN-reviewed-01
```

새 폴더에 포함 결정만 담은 `result.json`, 검토 파일의 원본 사본, 해시·건수·자동 평가·코드 해시를 담은 `review-audit.json`이 생성됩니다. `pending`과 `exclude`는 결과에서 빠지며 정상(false)으로 단정하지 않습니다. 부분 검토도 내보낼 수 있지만 감사 기록의 `review_complete`는 false입니다. 이 완료 값은 **검출된 특징 목록**에 대한 검토만 뜻하며 전체 사이트 검수·정확도·법적 확정을 뜻하지 않습니다. 일반 홍보 내용에 임의의 4종 기법을 붙이거나 탐지되지 않은 요소를 추가하는 기능은 없습니다.

기존 검토·출력 폴더를 덮어쓰지 않습니다. `Review failed`가 나오면 원문/요소·항목 누락·검토 근거·시간대·기존 출력 경로를 확인합니다. 코드 변경으로 검출 목록이 달라지면 이전 검토를 자동 이식하지 말고 새 capture에서 다시 검토합니다. 원본 수집·정답·자동 API 결과·루트 결과 파일은 유지됩니다. 내보내기는 추가 유형 파일을 재생성하지 않습니다. 저장 중 디스크 오류가 나면 불완전한 출력 폴더가 남을 수 있으므로 오류를 해결하고 새 경로로 다시 실행합니다.
