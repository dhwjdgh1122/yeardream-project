# YearDream — 진행 기록

최종 확인일: 2026-10-25 (Asia/Seoul)

## 1. 문서 역할

현재 상태·검증 근거·문제·다음 작업을 기록합니다. 목표와 규격을 여기에서 새로 정의하지 않습니다.

- [요구사항정의서.md](요구사항정의서.md): 요구사항·담당·통과 기준.
- [wiki.md](wiki.md): 구조·탐지·API·location·결과 규격.
- [README.md](README.md): 설치·서버·테스트 명령.
- [project-guide.md](project-guide.md): 작업 진행·설명·보고 방식.

공통 목표는 URL 기반 탐색, 필수 4종 탐지, 정확한 위치·근거, result.json, 결과 UI입니다. 공식 모집요강·출력 스키마는 원문 대조 전입니다.

## 2. 상태 표현

| 상태 | 의미 |
|---|---|
| 미구현 | 해당 기능의 구현을 확인하지 못함 |
| 구현됨·검증 전 | 코드가 있으나 요구사항 통과를 입증하지 못함 |
| 검증 통과 | 명시한 환경·입력·범위에서 예상 결과 확인 |
| 문제 확인 | 재현 실행 또는 코드 점검으로 결함 확인 |

코드 점검과 실행 결과는 구분합니다. 과거 기록·결과 파일·테스트 존재만으로 현재 검증 통과로 표시하지 않습니다. 부분 검증을 요구사항 전체 통과로 확대하지 않습니다.

## 3. 현재 요약

사용자 혼자 구현·탐지 기준·데이터·검증을 모두 담당합니다. 기본/동적 분석·JSON 다운로드에 이어 Windows 11 x64·Python 3.14.6의 새 가상환경에서 고정 의존성을 재현했습니다. 설치 문제를 수정하고 하위 의존성 31개를 고정했습니다. 최신 검증은 17절의 Python 66개 통과, pip check, Node·Edge·실제 Uvicorn 기동 검사입니다. 실제 사이트·광고 판정 정확도·computed style 판정·엄격한 시간 강제 종료 검증은 남아 있습니다.

## 4. 기능별 현황

| 범위 | 관련 요구사항 | 상태 | 확인 근거·한계 |
|---|---|---|---|
| FastAPI·분석 API | FR-001~003, FR-022 | 검증 통과(부분) | TestClient 및 실제 로컬 서버·Edge에서 UI→API→파일 흐름 확인. 입력 오류 전체 검증은 남음 |
| 정적 수집·하위 링크 | FR-004~007, FR-010~011 | 검증 통과(부분) | 상대 링크·fragment 중복·실패 처리 검증, 실제 게시글·댓글은 미검증 |
| iframe·중첩 경로 | FR-008~009, FR-017, FR-034 | 검증 통과(부분) | 정적 경로 및 JS 생성·반복/중첩·실행된 srcdoc/about:blank의 실제 DOM 경로를 로컬 Edge에서 재식별. 외부 도메인 분석은 미지원 |
| 탐지 통합·복수 요소 | FR-012~014, FR-038 | 검증 통과(부분) | 반복 태그/class·중복 ID·반복 프레임 삽입의 복수 요소를 위치별 보존 |
| selector·location | FR-015~018 | 검증 통과(부분) | 정적 DOM 자동 검증 및 Edge에서 표·특수문자 ID·프레임 경로 재식별. 실제 사이트는 미검증 |
| JSON 생성 | FR-019 | 검증 통과(부분) | 필드·비어 있지 않은 위치/근거·기법·Boolean·중복·시간·빈 결과·새 location·파일 일치 검증, 공식 스키마는 미확인 |
| UI·필터 | FR-020~021 | 검증 통과(부분) | Edge에서 기본/동적 분석 선택·4종 필터·전체 복귀·근거·부분 결과·오류 후 복구·정상 0건 확인. 별도 유형별 집계 UI는 미검증 |
| 탐지·정확도 | FR-023~033 | 구현됨·검증 전 | 합성 특징 사례 통과, 사용자의 광고 판정 기준 확정·실사이트 정확도 검증 필요 |
| 상태 안내 | FR-035 | 검증 통과(부분) | Edge에서 완료·부분 완료·오류·정상 0건 상태 확인. 진행 중 문구·중복 클릭의 브라우저 검증은 남음 |
| JSON 다운로드 | FR-036 | 검증 통과(부분) | Edge에서 기본/동적·부분/0건·필터 적용·서버 파일 변경 후 화면별 보존·파일명/UTF-8·API 값 일치 확인. 공식 스키마 원문 대조는 남음 |
| 한도·실패 구분 | FR-037, FR-039 | 검증 통과(부분) | 문서 수·링크 깊이·프레임 깊이·공유 시간 예산, 전체 실패502/시간 초과504/부분 경고 검증. 즉시 강제 종료는 아님 |
| 동적 콘텐츠 | FR-040 | 검증 통과(부분) | 선택적 browser 모드에서 JS 본문·fetch 댓글·링크·프레임 수집을 로컬 합성 페이지로 검증. 실제 사이트·클릭/스크롤·Shadow DOM·computed style은 미검증/미지원 |

NFR-001은 Windows 11 x64의 설치·시작·로컬 합성 분석을 부분 검증했습니다. GPU 없는 별도 PC와 공식 평가환경 조건은 미확인입니다. NFR-002~004는 평가 조건 원문 대조·시간·패키징 검증이 필요합니다. 표의 FR 묶음은 요약이며 개별 통과 판정을 뜻하지 않습니다.

## 5. 최초 점검 근거(복구 전 기록)

### 실행 확인

- 로컬 Python 3.14 실행 파일을 직접 지정해 테스트 실행. 이번 점검 환경이며 공식 지원 버전 확정이 아닙니다.
- 인자: `-B -m pytest tests/test_detection.py -q -p no:cacheprovider`
- 결과: 수집 단계 오류 1건. `ImportError: cannot import name 'build_result_json' from 'backend.app.detection'`
- 테스트 함수는 5개지만 본문 실행 전 실패했습니다. 이번 실행에서 통과로 확인된 테스트는 없습니다.
- WindowsApps py.exe는 파일 접근 오류로 실행되지 않아 설치된 Python 실행 파일로 우회했습니다.
- `git status --short`: 현재 폴더가 Git 저장소로 인식되지 않음. 원격·브랜치·commit 이력 확인 불가.
- 서버 시작·외부 사이트 분석·브라우저 동작은 이번 점검에서 실행하지 않았습니다.

### 기존 테스트 범위

iframe src 추출, selector 문자열, TRANSPARENT 양성, 정상 페이지, JSON 일부 필드를 검사합니다. HOMOGLYPH·JAMO·OFFSCREEN 직접 탐지, 유형별 정상·경계 사례, selector 재식별, 실제 중첩 프레임 탐색은 검증하지 않습니다. nested_frames라는 이름의 테스트도 단일 HTML의 src 추출 검사입니다.

### 코드 점검으로 확인한 문제

1. 결과 생성 함수 누락으로 API·테스트 import 실패.
2. 화면 경로가 frontend/static 대신 backend/frontend/static을 가리킴.
3. 결과 저장 경로가 프로젝트 루트 대신 backend/result.json을 가리킴.
4. UI 요청이 localhost:8000에 고정돼 포트·호스트 변경에 대응하지 못함.
5. 필터가 서버 원본 대신 화면용 요약을 재사용해 필요한 필드가 없어짐.
6. 유형별 첫 요소 탐지 후 종료하며 상위 요소의 하위 전체 텍스트도 매칭해 위치가 어긋날 수 있음.
7. opacity 정규식이 0.5 등도 매칭하고 absolute·overflow:hidden을 단독 OFFSCREEN 조건으로 사용함. 실제 오탐 범위는 정답 사례로 검증 필요.
8. 요청·실패 URL 방문 처리가 부족해 중복 요청·재시도가 가능하고 전체 시간 제한이 없음.

## 6. 문서 정리 내역

2026-10-23: 네 주요 문서의 역할과 공통 목표를 통일했습니다. 현재 API와 향후 제안, location 목표와 현재 구현, 팀 기준과 공식 원문 미확인 항목을 구분했습니다. 기존 FR-001~033을 유지하고 기존 wiki 범위를 FR-034~040·NFR-001~004로 연결했습니다. project-guide.md도 같은 기준을 참조하도록 맞췄습니다.

이 문서 정리 단계에서는 소스·테스트·requirements·기존 result.json을 수정하지 않았습니다. 당시 코드 문제의 후속 처리 결과는 아래 실행 흐름 복구 기록을 따릅니다.

문서 검증: 5개 파일의 UTF-8·BOM 없음·코드 블록 닫힘·로컬 링크 대상을 확인했습니다. JSON 예시는 파싱에 성공했고 FR-001~040의 중복·누락과 NFR-001~004 존재를 확인했습니다. 문서만 변경해 앱 테스트는 재실행하지 않았으며, 최신 앱 검증 결과는 위의 import 실패입니다.

## 7. 실행 흐름 복구 기록(당시 결과)

2026-10-23 사용자 승인으로 첫 코드 복구 단계를 진행했습니다.

- backend/app/result.py 추가: 내부 finding 변환, 팀 필드·허용 기법·Boolean·시간 검증, Detection Unit 중복 제거, 고유 ID, 빈 결과 처리. 기존 detection 모듈 import는 호환 유지.
- backend/app/main.py: 화면 경로와 저장 경로를 프로젝트 루트 기준으로 수정.
- frontend/static/index.html: 상대 API 호출, 원본 응답 보존, 필터 복귀, 근거 표시, 실행 중 중복 클릭 차단 및 오류 후 복구.
- tests/test_api.py·tests/test_result.py 추가, scripts/test_frontend.cjs 추가.
- README·wiki·이 진행 기록을 실제 결과에 맞게 갱신. 기존 result.json과 requirements.txt는 변경하지 않음. 테스트 저장은 임시 디렉터리로 격리.

검증 명령과 결과:

```text
설치된 Python 실행 파일 -B -m pytest tests -q -p no:cacheprovider
13 passed, 1 warning

node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
Frontend checks passed
```

Python 3.14.6 / FastAPI 0.150.0 / Starlette 1.9.0 / httpx 0.28.1 / Pydantic 2.14.1 / BeautifulSoup4 4.15.0 / Uvicorn 0.54.0에서 수행했습니다. requirements.txt의 고정 버전과 다르며 해당 고정 버전 환경은 아직 재현하지 않았습니다. 경고는 설치 환경의 TestClient/httpx 사용에 관한 Starlette 사용 중단 예고 1건입니다. 이번 범위에서 패키지를 변경하지 않았습니다.

Node 기본 실행은 상위 디렉터리 realpath 조회 권한 오류로 실패했고 symlink 보존 옵션으로 통과했습니다. 브라우저 대신 실제 inline script를 최소 DOM·API 대역으로 실행한 검증입니다. FastAPI는 TestClient를 사용했으며 실제 서버 포트 바인딩·브라우저 클릭·외부 네트워크는 검증하지 않았습니다.

남은 제한: 기존 URL::selector와 유형별 첫 요소 탐지 방식은 그대로입니다. Result Builder의 위반 판정 기본값 true는 과거 테스트 계약을 복구하기 위한 임시 동작이며 광고 판정 정책은 미확정입니다. 수집 실패를 0건으로 처리할 수 있는 문제도 후속 항목입니다. 최초 점검의 경로·import·필터 문제는 수정했으나 위치·탐지·수집 문제는 남아 있습니다. Git 저장소 연결이 확인되지 않아 commit은 하지 않았습니다.

## 8. 정적 탐지 사례·보완 기록(당시 결과)

2026-10-23 사용자 승인으로 정답 페이지와 경계 사례를 추가했습니다.

- tests/fixtures/detection/positive.html: 4종·동일 유형 복수 요소·동일 요소 복수 기법·부모 opacity·!important, 11개 요소의 12개 finding.
- tests/fixtures/detection/negative.html: 반투명·정상 배치·overflow·클래스 이름·속성·빈 요소·스크립트·주석 등 0건 사례.
- cases.json에 정답 요소 ID·유형, README.md에 근거·지원 한계 기록.
- tests/test_detection_cases.py에서 selector로 실제 정답 요소를 재식별하고 유형·건수·결과 변환 보존 확인.
- detection.py에서 직접 텍스트 요소만 분석, 비콘텐츠 문자열 제외, 첫 결과 후 중단 제거, opacity 부분 매칭·클래스 이름 오탐 제거, 단독 absolute·overflow 제외. 단순 inline 선언의 중복·!important 처리와 팀 문서의 작은 글꼴·display:none 예시 반영.
- 근거에 검출 원문 추가. 광고 여부 기본값·confidence·URL::selector는 이번 단계에서 변경하지 않음.

변경 전 새 사례 2개는 실패했고, 수정 후 `-B -m pytest tests -q -p no:cacheprovider`는 **15 passed, 1 warning**입니다. 환경·경고는 7절과 같습니다. 외부 인터넷·실제 브라우저·패키지 변경 없이 수행했습니다. 프론트엔드 코드는 변경하지 않아 Node 검증은 반복하지 않았습니다.

최초 점검의 상위 요소 오지정·첫 결과 누락·단순 opacity/absolute/overflow 오탐은 이번 사례에서 해결했습니다. 그러나 합성 데이터 특징 정답을 불법광고 판정 정답으로 취급하지 않습니다. 정상 외국어·초성·접근성 텍스트 정책은 사용자의 기준 확정이 필요합니다. 외부 CSS·computed style·전체 상속·조상 display:none 전파·노드 간 문자 조합·실제 음수 좌표의 화면 이탈·selector 고유성·iframe 경로는 남아 있습니다.

README·wiki·이 문서를 갱신했습니다. requirements.txt·기존 result.json은 변경하지 않았으며 Git 저장소 연결 미확인으로 commit은 하지 않았습니다.

## 9. 승인된 연속 3개 작업 결과

사용자가 중간 승인을 대신해 세 작업의 연속 진행을 허용했습니다. 아래 범위를 구현·검증·문서 반영까지 마쳤으며 이 승인으로 다른 작업을 자동으로 시작하지 않습니다.

### 작업 1 — 일반 selector·location

location.py를 추가했습니다. 실제 DOM에서는 ID/class의 CSS 특수문자를 escaping하고, 짧은 selector가 고유하지 않으면 조상 경로와 nth-of-type으로 구분합니다. DOM 검색 결과가 정확히 원본 요소 하나인지 확인합니다. 기존 dict 입력은 문자열 조각 호환 API로 유지하며 그 입력만으로 고유성을 보장하지 않습니다.

일반 location은 URL 접두사 없는 selector로 전환했습니다. test_location.py에서 중복 ID·동일 태그/class·동일 내용·ID 없는 요소·특수문자 ID를 검증했습니다. 이 단계에서 25개 테스트가 통과했습니다.

### 작업 2 — iframe·중첩 iframe

crawler.py에서 top_url·parent_url·frame_path를 수집합니다. 같은 src라도 삽입 위치마다 컨텍스트를 유지하고 HTTP 응답은 URL별 캐시로 재사용합니다. 상대 src·정적 srcdoc·실패한 형제 프레임·깊이 초과·순환을 테스트했습니다. 일반 링크의 fragment 중복과 비HTTP 링크도 제외합니다.

현재 max_pages는 실패를 포함한 문서 컨텍스트 수입니다(API 8). iframe 깊이 기본값은 3이며 한도·제외 사유를 기록합니다. 외부 도메인·동적 DOM·HTML base 요소·about:blank 런타임 DOM은 미지원입니다. 리디렉션 후 범위 밖으로 확인된 문서는 분석하지 않지만 HTTP 클라이언트는 이미 리디렉션을 따라갔으므로 외부 접속 자체를 차단하는 기능은 아닙니다.

### 작업 3 — API·결과 통합

API 중복 제거 키를 URL + location + technique으로 변경했습니다. 내부 selector는 프레임 안의 요소 selector, location은 최상위 페이지부터의 전체 경로입니다. 두 삽입 위치의 동일 iframe 내용이 합쳐지지 않는지 확인했습니다.

최종 JSON 필드의 빈 위치·근거를 거부하고, 전체 수집 실패는 HTTP 502 및 기존 파일 보존으로 처리합니다. 일부 실패·제외·한도는 API warnings로 반환하고 UI에서도 부분 분석임을 표시합니다. warnings는 제출 JSON에 넣지 않으므로 파일 단독의 완전성 표시는 후속 정책 항목입니다.

test_location_integration.py에서 수집 → 탐지 → 프레임 경로 재식별 → API → 결과 파일 일치를 검증했습니다. 저장은 임시 경로로 격리해 기존 result.json은 변경하지 않았습니다.

최종 검증:

```text
설치된 Python 실행 파일 -B -m pytest tests -q -p no:cacheprovider
37 passed, 1 warning

node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
Frontend checks passed (partial results 포함)
```

환경·경고는 7절과 같습니다. 정적 HTML·HTTP 수집 대역·TestClient·최소 DOM 대역 기반 검증이며 실제 브라우저·외부 사이트·고정 의존성 환경은 검증하지 않았습니다. 현재 parser가 만든 DOM과 브라우저가 보정한 DOM이 다를 가능성도 후속 검증 대상입니다. requirements.txt는 수정하지 않았고 Git commit은 하지 않았습니다.

README·wiki·요구사항정의서·project-guide·fixture 설명·이 문서에 1인 작업 체계와 최신 상태를 반영했습니다. 별도 분석가의 승인을 기다리는 전제는 제거했습니다. 사용자와 코딩 에이전트가 근거를 검토해 광고 판정 기준을 정합니다.

## 10. 링크 깊이·시간 예산 작업 결과

2026-10-24 사용자 승인으로 구현·검증했습니다. 관련 요구사항은 FR-003·FR-011·FR-035·FR-037·FR-039이며 공식 평가 시간 조건 NFR-002 검증 완료를 뜻하지 않습니다.

- limits.py에 monotonic 기반 공유 Deadline 추가. 수집·탐지가 같은 종료시각을 사용하며 무한대·NaN·0 이하 예산 거부.
- API 요청에 max_depth(기본 2, 0~20)·total_timeout_sec(기본 60초, 0 초과~1800 이하) 추가. 기존 URL만 보내는 UI는 기본값 사용.
- 일반 링크는 시작 페이지 0에서 이동마다 깊이 증가. iframe·srcdoc은 링크 깊이를 유지하며 그 안의 링크도 동일 한도를 적용. 프레임을 먼저 확장해 링크 깊이가 낮은 경로를 우선함.
- HTTP 요청 시작 시 남은 예산을 고려한 timeout 사용. 응답을 스트리밍하며 청크 사이, 수집 반복, 탐지 요소 사이에서 예산 확인.
- 깊이·문서 수·시간 제한 원인을 구분해 API warnings로 안내. 분석 완료 페이지가 없는 시간 초과는 HTTP 504와 기존 파일 보존, 완료 페이지가 있으면 그 페이지 결과와 부분 분석 안내 반환.
- tests/test_limits.py에 가상 시계·HTTP 대역으로 경계 검증 추가. 기존 수집 대역은 새 timeout 인자를 허용하도록 수정. 프레임 우선순위 변경에 맞춰 문서 수 제한 테스트의 입력을 일반 링크로 고정.

검증 명령: 설치된 Python 실행 파일에 `-B -m pytest tests -q -p no:cacheprovider` 전달. 최종 결과는 **53 passed, 1 warning**입니다. 설치 환경·경고는 7절과 같습니다. 실제 대기·외부 인터넷 없이 깊이 0/1, 프레임 독립 깊이, 요청 전 만료, 늦은 응답·스트림 중 만료, 남은 HTTP timeout, 504 파일 보존, 부분 결과, 잘못된 입력을 확인했습니다. UI 스크립트는 변경하지 않았고 기존 warnings 계약을 사용해 Node 검증은 반복하지 않았습니다.

시간 제한은 협력적 중단입니다. 진행 중인 네트워크 대기·HTML 파싱·selector 계산을 즉시 강제 종료하지 못하며 일부 초과할 수 있습니다. 결과 변환·직렬화·저장은 중단 결과를 반환하기 위한 마무리로 예산 밖에서 수행합니다. 실제 평가환경에서의 엄격한 시간 제한 검증은 남아 있습니다. crawled_pages는 수집 성공 목록이며 시간 초과 시 모든 페이지의 탐지가 완료됐다는 뜻은 아닙니다.

README·wiki·이 문서를 갱신했습니다. 기존 result.json·requirements.txt는 변경하지 않았고 Git commit은 하지 않았습니다.

## 11. 다음 작업

1. 실행 흐름 복구: 자동 검증 및 새 고정 의존성 환경의 설치·CLI 기동·로컬 Edge 흐름 통과. 다른 PC에서의 재현은 남아 있음.
2. 기준 테스트: 개발자 합성 특징·경계 사례 자동 검증 통과. 사용자의 광고 판정 기준·실제 정답 데이터 검수는 남아 있음.
3. 위치·결과: 정적 DOM 및 로컬 Edge의 표·프레임 경로 재식별·API/파일 일치 통과. 실제 사이트 재식별은 남아 있음.
4. 수집: 한도·공유 시간 예산·실패 기본 검증 및 로컬 동적 본문/댓글/프레임 검증 완료. 실제 게시글/댓글·computed style·엄격한 시간 중단 검증은 필요.
5. 실제 사이트: 허용 범위·오탐·미탐·근거·상태·다운로드 검증.
6. 평가·제출: 공식 원문 대조, 실제 Windows·시간 제한·배포 산출물 확인.

한도·Git 연결·로컬 브라우저 검증·동적 수집·JSON 다운로드·고정 의존성 재현 작업은 완료했습니다. 다음 우선순위는 실제 사이트의 검증 범위·정답 기준을 정하고 오탐·미탐·위치·근거를 확인하는 것입니다. 공식 원문 미확인은 별도로 관리합니다. Git 연결은 13절, 브라우저 검증은 14절, 동적 수집은 15절, 다운로드는 16절, 환경 재현은 17절에 기록합니다.

## 12. 재개·마무리

재개 시 이 문서 → README → 관련 요구사항·wiki → 실제 코드를 확인합니다. 이전 서버·터미널은 자동 복원되지 않으므로 README 절차로 다시 실행합니다.

단계 종료 시 날짜·변경 파일·실행 명령/결과·관련 FR·남은 문제·다음 작업·Git 기록 여부를 갱신합니다.

이전 문서의 '4개/5개 통과', 'health·분석 API 정상', '핵심 검증 완료'는 과거 기록으로만 보존합니다. 최초 재점검은 import 실패였으며 최신 검증 근거는 17절의 실행 결과입니다. 과거의 완료 주장을 현재 전체 완료 근거로 사용하지 않습니다.

## 13. GitHub 연결·최초 업로드

2026-10-24 사용자가 저장소 연결·문서 갱신·커밋·업로드를 승인했습니다.

- 저장소: https://github.com/dhwjdgh1122/yeardream-project
- 원격 이름: `origin`, HTTPS 주소: `https://github.com/dhwjdgh1122/yeardream-project.git`
- 원격 조회 시 기존 HEAD가 없는 빈 저장소임을 확인하고 로컬 `main` 브랜치를 초기화했습니다.
- 기존 구현·문서·테스트를 첫 커밋으로 보존합니다. 과거 작업별 commit 이력은 없으며 앞 절의 미커밋 기록은 당시 상태입니다.
- `.gitignore`로 Python 캐시·pytest 캐시·가상환경·`.env`를 제외합니다. 기존 `result.json`은 과거 실행 산출물 그대로 보존하며 최신 검증 결과로 취급하지 않습니다.
- 업로드 전 재검증: Python 3.14에서 `-B -m pytest tests -q -p no:cacheprovider` 실행 결과 **53 passed, 1 warning**. 경고는 7절과 같은 TestClient/httpx 사용 중단 예고입니다.
- `node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs`: **Frontend checks passed**. 상대 API 경로·필터·전체 복귀·근거·부분 결과·오류 후 초기화를 확인했습니다.
- 앱 코드는 변경하지 않았습니다. 실제 브라우저·외부 사이트·고정 의존성 환경 검증은 여전히 남아 있습니다.

최초 커밋 메시지는 `feat: initialize YearDream detection project`이며 원격 업로드 결과는 Git 이력과 원격 브랜치 조회로 확인합니다.

## 14. 실제 브라우저 위치·화면 검증

2026-10-24 다음 우선순위인 실제 브라우저 검증을 진행했습니다. 관련 요구사항은 FR-015~021·FR-034~035·FR-039~040입니다. 해당 요구사항 전체 완료를 뜻하지 않습니다.

- scripts/test_browser.py 추가: 임시 포트의 실제 Uvicorn 서버와 설치된 Microsoft Edge(headless)를 사용합니다. API 요청·HTTP 수집·UI를 대역 없이 연결하며 입력은 로컬 합성 HTML입니다. result.json은 임시 디렉터리로 격리하고 종료 시 서버·브라우저·출력 경로를 정리합니다.
- 수정 전 반복 표의 `table > tr > td` 위치가 실제 Edge에서 0개를 선택하는 실패를 재현했습니다. 브라우저가 tbody를 삽입하는 것이 원인입니다.
- crawler.py·detection.py의 파서를 html.parser에서 html5lib로 통일했습니다. requirements.txt에 html5lib==1.1을 추가하고 설치했습니다. tests/test_location.py에 표의 DOM 보정 회귀 검사를 추가하고 위치 재식별 테스트의 파서를 맞췄습니다.
- 수정 후 9개 finding의 표·특수문자 ID·반복/중첩 iframe·srcdoc 위치를 실제 Edge에서 하나씩 재식별하고 근거 원문과 대조했습니다. API 결과와 임시 결과 파일 일치도 확인했습니다.
- 실제 화면의 4종 필터·전체 복귀·근거·부분 결과 안내·수집 실패 502·기존 결과 파일 보존·필터 변경 시 과거 결과 부활 방지·정상 0건으로 재실행을 확인했습니다. 페이지 JavaScript 오류는 없었습니다.
- JS가 추가한 요소가 Edge DOM에는 있으나 정적 API 탐지에는 없는 사례를 확인했습니다. 현재 지원 범위는 응답 HTML과 정적 iframe/srcdoc이며 JS 렌더링·computed style·동적 iframe·Shadow DOM은 이번 작업에서 구현하지 않았습니다. HTML5 파싱만으로 동적 DOM과의 일치를 보장하지 않습니다.

검증 명령과 결과:

```text
설치된 Python 실행 파일 -B -m pytest tests -q -p no:cacheprovider
54 passed, 1 warning

설치된 Python 실행 파일 -B scripts/test_browser.py
Browser locations passed: tables, escaped IDs, repeated/nested frames, srcdoc
Browser checks passed: Edge 156.0.4314.42; UI, filters, partial results, failure recovery, empty results
Dynamic limitation confirmed: runtime element exists in browser but is absent from static findings
```

Playwright 1.64.0·html5lib 1.1을 사용했습니다. 나머지 Python 환경·TestClient 경고는 7절과 같습니다. Playwright는 검증 도구이며 앱 런타임 요구사항에는 추가하지 않았습니다. requirements.txt의 전체 고정 환경 재현·외부 사이트·실제 광고 판정 정확도·다른 브라우저·엄격한 시간 제한은 미검증입니다.

README·wiki·fixture 설명·진행 기록을 갱신했습니다. 기존 result.json은 보존했습니다. 이번 수정은 `fix: align static locations with browser HTML5 parsing` 커밋으로 기록하며 커밋·원격 동기화 여부는 Git 상태로 확인합니다.

## 15. 선택적 동적 페이지 수집

2026-10-25 다음 우선순위인 동적 수집을 구현·검증했습니다. 관련 요구사항은 FR-003~011·FR-017·FR-020~022·FR-034~035·FR-037·FR-039~040입니다. 로컬 합성 입력의 부분 검증이며 실제 사이트나 광고 판정 정확도의 전체 통과가 아닙니다.

- backend/app/browser.py 추가: Playwright를 지연 import하여 기본 분석은 별도 설치 없이 유지합니다. 요청마다 새 Edge 컨텍스트를 열고 종료·오류 시 브라우저와 드라이버를 정리합니다. 개인 프로필·로그인을 사용하지 않습니다.
- API에 collection_mode(static 기본/browser)·render_wait_ms(500 기본, 0~5000) 추가. DOMContentLoaded 후 지정 시간만큼 대기하며 브라우저 시작·이동·대기·수집·탐지가 같은 Deadline을 사용합니다. 동적 기능 시작 실패는 503, 분석 완료 전 시간 예산 소진은 504이며 기존 파일을 보존합니다. 정적으로 자동 대체하지 않습니다.
- crawler.py에서 기존 링크/프레임 깊이·문서 수·실패 처리 흐름을 재사용합니다. 렌더링한 DOM의 링크를 탐색하고 iframe은 URL을 다시 열지 않고 실제 삽입된 Frame을 읽습니다. 같은 src의 두 프레임에 부모 JS가 넣은 서로 다른 텍스트가 보존됩니다.
- 실행된 srcdoc·about:blank의 DOM과 JS 생성 중첩 iframe을 지원합니다. 외부 URL·미로딩·제거/접근 실패 프레임은 제외 사유를 기록하고, 문서 HTTP 400 이상은 실패, 페이지 JS 예외는 warnings로 안내합니다.
- 화면에 기본/동적 분석 선택과 지원 범위 안내를 추가했습니다. 요청 중 분석 방식 선택을 잠그고 성공·실패 후 복구합니다. API 응답과 화면 요약에 collection_mode를 표시합니다. 제출 JSON 필드·기본 광고 판정·탐지 규칙은 변경하지 않았습니다.
- requirements-browser.txt에 기존 런타임 요구사항과 playwright==1.64.0을 연결했습니다. 동적 분석은 서버 PC의 Microsoft Edge가 필요하며 설치 절차는 README에 기록했습니다.

검증 근거:

1. 구현 전 새 동적 수집·입력 검증 테스트 6개가 실패했습니다. 구현 후 기존 테스트와 동적 삽입별 컨텍스트·링크 깊이·문서/프레임 한도·공유 시간·형제 프레임 실패 보존·미로딩/제거·외부 리디렉션 제외·503/504 파일 보존·자원 정리·잘못된 입력을 검사했습니다.
2. 실제 Edge에서 같은 합성 페이지의 기본 분석은 **0건**, 동적 분석은 **11건**입니다. JS 생성 본문, fetch 댓글, JS 생성 링크의 하위 페이지, 부모가 서로 다르게 수정한 동일 src 프레임, 중첩 프레임, 실행된 srcdoc·about:blank를 포함합니다. 위치를 새 브라우저 페이지에서 재식별하고 근거 원문·API/파일 일치를 확인했습니다.
3. max_depth=0에서는 하위 링크를 제외해 **10건**과 깊이 제한 warnings를 반환했습니다. 페이지 JS 오류·iframe 404에서도 남은 finding과 부분 안내를 보존했습니다. 동적 502·504 발생 시 기존 파일 보존과 정상 0건 재실행도 확인했습니다.

```text
설치된 Python 실행 파일 -B -m pytest tests -q -p no:cacheprovider
66 passed, 1 warning

node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
Frontend checks passed: API path, filters, restore all, evidence, partial results, failure reset.

설치된 Python 실행 파일 -B scripts/test_browser.py
Browser locations passed: tables, escaped IDs, repeated/nested frames, srcdoc
Browser checks passed: Edge 156.0.4314.42; UI, filters, partial results, failure recovery, empty results
Dynamic checks passed: static=0/browser=11; fetched comments, runtime links/depth, live repeated/nested frames, scripted srcdoc/about:blank, locations, file, JS/frame failure warnings, 502/504 preservation
```

Playwright 1.64.0·Edge 156.0.4314.42와 앞 절과 같은 Python 환경에서 검증했습니다. 경고는 기존 TestClient/httpx 사용 중단 예고입니다. requirements.txt/requirements-browser.txt의 전체 고정 환경은 아직 재현하지 않았습니다. 기존 result.json은 변경하지 않았습니다.

지원 범위는 관찰 시점까지 생성된 DOM입니다. 자동 스크롤·클릭·로그인·Shadow DOM·CSS computed style 판정·HTML base 요소는 미지원입니다. 늦은 비동기 처리·관찰 이후의 DOM 변화·전체 프레임의 동일 시점 고정을 보장하지 않습니다. 문서/깊이 제한은 분석 컨텍스트에 적용하며 브라우저 리소스 로딩 수 제한이 아닙니다. 외부 프레임은 분석에서 제외하지만 외부 통신 자체를 차단하지 않습니다. 드라이버 시작·DOM 직렬화·종료를 포함한 엄격한 강제 중단도 미지원입니다.

README·wiki·이 진행 기록을 갱신했습니다. 커밋 메시지는 `feat: add optional browser collection for dynamic pages`로 기록하고 Git 상태와 원격 조회로 업로드를 확인합니다.

## 16. JSON 다운로드·결과 일치

2026-10-25 사용자가 다음 작업 진행을 승인해 JSON 다운로드를 구현·검증했습니다. 관련 요구사항은 FR-019~021·FR-035~036·FR-039입니다.

- frontend/static/index.html에 JSON 다운로드 버튼을 추가했습니다. 마지막 성공 응답의 result_json 전체를 UTF-8(BOM 없음) Blob으로 직렬화해 result.json으로 저장합니다. 화면 요약·유형 필터와 독립적이며 기본/동적·부분/0건 결과를 지원합니다.
- 분석 전·새 분석 진행 중·요청 실패·빈 URL 제출 후에는 다운로드를 비활성화합니다. 빈 URL 제출도 이전 응답을 비워 과거 결과의 재다운로드와 필터 복원을 막습니다. 다운로드 후 임시 링크와 object URL을 정리합니다.
- 부분 분석의 warnings는 화면 안내로 유지하고 제출 JSON에 추가하지 않습니다. 서버의 공유 result.json을 다시 받지 않으므로 다른 요청이 서버 파일을 바꾸더라도 현재 화면의 결과를 보존합니다.
- scripts/test_frontend.cjs에 전체 결과·필터 독립성·빈 결과·비활성 상태·MIME·UTF-8·object URL 정리 검증을 추가했습니다. scripts/test_browser.py는 실제 Edge 다운로드 파일을 임시 디렉터리에 저장해 파일명·인코딩·API 결과와의 동등성을 검사합니다. JSON 동등성은 파싱한 값 기준입니다.
- Edge에서 정적 부분 결과 9건, 필터로 1건만 표시한 상태의 전체 결과, 다른 클라이언트가 서버 파일을 0건으로 바꾼 후의 기존 화면 결과, 정적 0건, 동적 전체 11건·부분 1건·0건 다운로드를 확인했습니다. 초기와 UI 분석 실패 502 후 버튼 비활성화도 확인했습니다.

```text
설치된 Python 실행 파일 -B -m pytest tests -q -p no:cacheprovider
66 passed, 1 warning

node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
Frontend checks passed: API, modes, filters, partial results, failure reset, full JSON downloads, empty results, UTF-8, URL cleanup.

설치된 Python 실행 파일 -B scripts/test_browser.py
Browser locations passed: tables, escaped IDs, repeated/nested frames, srcdoc
Browser checks passed: Edge 156.0.4314.42; UI, filters, partial results, failure recovery, empty results
Dynamic checks passed: static=0/browser=11; fetched comments, runtime links/depth, live repeated/nested frames, scripted srcdoc/about:blank, locations, file, JS/frame failure warnings, 502/504 preservation
Download checks passed: filename, UTF-8 without BOM, full/filtered/partial/empty/static/dynamic results, per-page retention, failure disabled
```

환경·TestClient 경고는 15절과 같습니다. 백엔드·의존성·기존 result.json은 변경하지 않았습니다. 실제 브라우저 입력은 로컬 합성 페이지이며 실제 사이트 정확도·공식 스키마·전체 고정 의존성 환경·타 브라우저는 미검증입니다.

README·wiki·진행 기록을 갱신했습니다. 커밋 메시지는 `feat: download full analysis results as JSON`이며 Git 상태·원격 조회로 업로드를 확인합니다. 다음 작업은 고정 의존성 환경 재현과 실행 절차 검증입니다.

## 17. 고정 의존성·설치/기동 재현

2026-10-25 새 격리 환경에서 설치·기동·전체 검증을 진행했습니다. 관련 항목은 FR-001~003·FR-019~022·FR-036·FR-040 및 NFR-001·NFR-003의 일부입니다. 공식 평가환경·최종 배포 산출물 전체 검증은 아닙니다.

### 설치 문제와 수정

- Windows 11 x64(빌드 26200)·CPython 3.14.6·pip 26.1.2를 확인하고 시스템 패키지를 사용하지 않는 .venv를 생성했습니다.
- 기존 requirements.txt로 `pip install --only-binary=:all: -r requirements.txt`를 실행하자 pydantic==2.9.2가 요구하는 pydantic-core==2.23.4의 호환 휠을 찾지 못해 실패했습니다. 소스 빌드와 이전 Python 버전의 설치는 시도하지 않았습니다.
- 기존에 앱 검증에 사용한 직접 의존성으로 갱신했습니다: FastAPI 0.150.0·Uvicorn 0.54.0·httpx 0.28.1·BeautifulSoup4 4.15.0·Pydantic 2.14.1. html5lib 1.1·Playwright 1.64.0은 유지했습니다.
- requirements-dev.txt에 전체 브라우저 환경과 pytest==9.1.1을 추가했습니다. 새 환경 설치 후 constraints-windows-py314.txt에 직접/하위 의존성 31개를 고정하고 requirements.txt에서 공통 적용합니다. Starlette는 새로 해석된 1.10.0이며 pydantic-core는 2.50.1입니다. 전체 버전 목록은 constraints 파일을 기준으로 합니다.
- .venv에서 최종 requirements-dev.txt 재적용(--no-index), 설치 버전과 constraints의 31개 일치, 시스템 패키지 격리, pip check를 확인했습니다.
- 별도의 빈 .venv/runtime-check에 최종 constraints를 적용한 requirements.txt만 설치했습니다. 설치된 22개 런타임 패키지의 의존성이 정상이며 pytest·Playwright가 없는 상태에서 기본 기동이 성공했습니다. 로컬 가상환경 두 개는 모두 .venv 아래에 있어 Git에서 제외됩니다.

### 실행 절차와 검증

scripts/smoke_test.py를 외부 example.com 요청 예제에서 로컬 CLI 기동 검사로 바꿨습니다. 선택한 Python으로 실제 `-m uvicorn backend.app.main:app --host 127.0.0.1 --port 임시포트`를 실행하고 health·UI·OpenAPI·잘못된 입력 422를 확인한 뒤 프로세스를 종료합니다. 실제 사이트 수집이나 기존 result.json 변경은 하지 않습니다. 기본 런타임 전용 환경과 전체 개발 환경에서 모두 통과했습니다.

```text
.venv\Scripts\python.exe -m pip check
No broken requirements found.

.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
66 passed, 1 warning

.venv\Scripts\python.exe -B scripts/smoke_test.py
Startup checks passed: Uvicorn CLI, health, UI, OpenAPI, input validation; local requests only

.venv\runtime-check\Scripts\python.exe -m pip check
No broken requirements found.

.venv\runtime-check\Scripts\python.exe -B scripts/smoke_test.py
Startup checks passed: Uvicorn CLI, health, UI, OpenAPI, input validation; local requests only

node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
Frontend checks passed: API, modes, filters, partial results, failure reset, full JSON downloads, empty results, UTF-8, URL cleanup.

.venv\Scripts\python.exe -B scripts/test_browser.py
Browser locations passed: tables, escaped IDs, repeated/nested frames, srcdoc
Browser checks passed: Edge 156.0.4314.42; UI, filters, partial results, failure recovery, empty results
Dynamic checks passed: static=0/browser=11; fetched comments, runtime links/depth, live repeated/nested frames, scripted srcdoc/about:blank, locations, file, JS/frame failure warnings, 502/504 preservation
Download checks passed: filename, UTF-8 without BOM, full/filtered/partial/empty/static/dynamic results, per-page retention, failure disabled
```

Node는 20.12.2입니다. Python 경고 1건은 기존 Starlette TestClient/httpx 사용 중단 예고이며 테스트는 통과했습니다. README에 Python·설치 프로필·휠 설치·pip check·CLI 기동 검사·종료 절차를 반영했습니다. wiki와 진행 기록도 갱신했습니다.

이번 검증은 같은 Windows PC의 새 격리 환경에서 수행했습니다. 다른 OS/Python·별도 PC·GPU 없는 조건·공식 평가 조건·오프라인 배포·실행 파일·장시간 제한·실제 사이트 광고 판정은 미검증입니다. Edge는 별도 설치 앱이며 Python constraints로 버전을 고정하지 않습니다. 앱의 탐지·API·UI 코드와 기존 result.json은 변경하지 않았습니다.

커밋 메시지는 `build: pin reproducible Windows Python 3.14 environment`이며 Git 상태·원격 조회로 업로드를 확인합니다. 다음은 실제 사이트의 검증 범위·정답 기준 확정과 정확도·위치 검증입니다.
