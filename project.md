# YearDream — 진행 기록

최종 확인일: 2026-10-25 (Asia/Seoul)

## 1. 문서 역할

현재 상태·검증 근거·문제·다음 작업을 기록합니다. 목표와 규격을 여기에서 새로 정의하지 않습니다.

- [요구사항정의서.md](요구사항정의서.md): 요구사항·담당·통과 기준.
- [wiki.md](wiki.md): 구조·탐지·API·location·결과 규격.
- [README.md](README.md): 설치·서버·테스트 명령.
- [project-guide.md](project-guide.md): 작업 진행·설명·보고 방식.

공통 목표는 URL 기반 탐색, 필수 4종 탐지, 정확한 위치·근거, result.json, 결과 UI입니다. 2026-10-25 업로드 PDF 18쪽의 요구사항·출력 표/예시를 대조해 반영했습니다. 과거 절의 ‘원문 미확인’·‘computed style 미지원’·‘is_violation 임시 기본 true’는 당시 기록이며 현재 상태는 25절을 따릅니다.

## 2. 상태 표현

| 상태 | 의미 |
|---|---|
| 미구현 | 해당 기능의 구현을 확인하지 못함 |
| 구현됨·검증 전 | 코드가 있으나 요구사항 통과를 입증하지 못함 |
| 검증 통과 | 명시한 환경·입력·범위에서 예상 결과 확인 |
| 문제 확인 | 재현 실행 또는 코드 점검으로 결함 확인 |

코드 점검과 실행 결과는 구분합니다. 과거 기록·결과 파일·테스트 존재만으로 현재 검증 통과로 표시하지 않습니다. 부분 검증을 요구사항 전체 통과로 확대하지 않습니다.

## 3. 현재 요약

사용자 혼자 구현·탐지 기준·데이터·검증을 모두 담당합니다. 필수 4종·홍보 후보·동적 CSS 판별과 PDF 출력 규격을 구현했고, 실제 홍보 구간과 겹치는 특징만 제출하는 정책을 연결했습니다. is_violation 누락 시 true로 바꾸는 동작은 제거했습니다. Python 219개와 실제 Edge에서 위장 홍보 4종 제출·무관한 특징 4개 검토 보존을 검증했습니다. 이는 합성 입력 검증이며 실제 저장본 본문 검수(홍보 TP 2·예방교육 TN 2)는 부분 검수로 전체 지표가 없습니다. 최신 결과는 25절입니다. 어휘 밖 광고·실제 정확도·검토 결과 확정 흐름·배포 패키지·제출 서류·접수 확인은 남아 있습니다.

## 4. 기능별 현황

| 범위 | 관련 요구사항 | 상태 | 확인 근거·한계 |
|---|---|---|---|
| FastAPI·분석 API | FR-001~003, FR-022 | 검증 통과(부분) | TestClient 및 실제 로컬 서버·Edge에서 UI→API→파일 흐름 확인. 입력 오류 전체 검증은 남음 |
| 정적 수집·하위 링크 | FR-004~007, FR-010~011 | 검증 통과(부분) | 상대 링크·fragment 중복·실패 처리 검증, 실제 게시글·댓글은 미검증 |
| iframe·중첩 경로 | FR-008~009, FR-017, FR-034 | 검증 통과(부분) | 정적 경로 및 JS 생성·반복/중첩·실행된 srcdoc/about:blank의 실제 DOM 경로를 로컬 Edge에서 재식별. 외부 도메인 분석은 미지원 |
| 탐지 통합·복수 요소 | FR-012~014, FR-038 | 검증 통과(부분) | 반복 태그/class·중복 ID·반복 프레임 삽입의 복수 요소를 위치별 보존 |
| selector·location | FR-015~018 | 검증 통과(부분) | 정적 DOM 자동 검증 및 Edge에서 표·특수문자 ID·프레임 경로 재식별. 실제 사이트는 미검증 |
| JSON 생성 | FR-019 | 검증 통과(부분) | PDF 표/예시 기반 TOPIC·원문 근거·별도 ETC 파일·URL 동등성·형식 및 파일 일치 검증. 주최 측 실제 채점은 미확인 |
| UI·필터 | FR-020~021 | 검증 통과(부분) | Edge에서 기본/동적 분석 선택·4종 필터·전체 복귀·근거·부분 결과·오류 후 복구·정상 0건 확인. 별도 유형별 집계 UI는 미검증 |
| 탐지·정확도 | FR-023~033 | 검증 통과(부분) | 내용 규칙·원문 구간에 의한 제출 선택·정상 특징 검토 보존을 합성 입력으로 검증. 실제 양성 2·예방자료 1 저장본 회귀 확인. 전체 정확도·미확정 검수 흐름은 미검증 |
| 상태 안내 | FR-035 | 검증 통과(부분) | Edge에서 완료·부분 완료·오류·정상 0건 상태 확인. 진행 중 문구·중복 클릭의 브라우저 검증은 남음 |
| JSON 다운로드 | FR-036 | 검증 통과(부분) | 필수/추가 결과 및 검수용 후보 파일을 Edge에서 검증. 필터 독립성·이전 화면 결과 보존·0건·실패 비활성 확인 |
| 한도·실패 구분 | FR-037, FR-039 | 검증 통과(부분) | 문서 수·링크 깊이·프레임 깊이·공유 시간 예산, 전체 실패502/시간 초과504/부분 경고 검증. 즉시 강제 종료는 아님 |
| 동적 콘텐츠 | FR-040 | 검증 통과(부분) | JS 본문·댓글·프레임 및 계산 CSS·은닉 상속·문서 좌표를 실제 Edge 합성 입력으로 검증. 실제 사이트 정확도·클릭/스크롤·Shadow DOM은 미검증/미지원 |

NFR-001의 공식 Windows 11·GPU 없는 PC 조건은 확인했습니다. 로컬 설치·시작·합성 분석은 부분 검증했지만 별도 평가 PC에서의 배포는 미검증입니다. NFR-002는 시작~완료 시간 30분 초과 시 시간 항목 0점이라는 조건을 확인했고 실제 평가 범위의 시간 검증은 남아 있습니다. NFR-003~005의 패키징·설명서·신청 서류도 필요합니다. 표의 FR 묶음은 요약이며 개별 통과 판정을 뜻하지 않습니다.

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

한도·Git 연결·동적 수집·JSON 다운로드·고정 환경·평가 도구·첫 실제 점검과 내용 후보 판별을 마쳤습니다. 다음 우선순위는 내용 후보용 정답 데이터·정확도 평가를 확장하고 오탐/미탐을 보완하는 것입니다. 기존 is_violation 임시 기본값과 내용 후보의 연계, 일반 광고의 제출 표현은 공식 출력 원문과 함께 정리해야 합니다. 초기 점검은 19절, 내용 후보 보완은 20절에 기록합니다.

## 12. 재개·마무리

재개 시 이 문서 → README → 관련 요구사항·wiki → 실제 코드를 확인합니다. 이전 서버·터미널은 자동 복원되지 않으므로 README 절차로 다시 실행합니다.

단계 종료 시 날짜·변경 파일·실행 명령/결과·관련 FR·남은 문제·다음 작업·Git 기록 여부를 갱신합니다.

이전 문서의 '4개/5개 통과', 'health·분석 API 정상', '핵심 검증 완료'는 과거 기록으로만 보존합니다. 최초 재점검은 import 실패였습니다. 초기 누락은 19절, 최신 자동 검증과 실제 보완 결과는 20절을 따릅니다. 과거의 완료 주장을 현재 전체 완료 근거로 사용하지 않습니다.

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

## 18. 실제 사이트 검증 도구 준비·입력 대기

2026-10-25 사용자가 실제 사이트 검증 진행을 요청했습니다. 최초 문서·fixture 점검에서는 실제 대상 URL·공식 광고 기준·검수 정답이 없어 URL과 기준을 요청하고 독립적으로 가능한 도구 준비를 진행했습니다. 이후 같은 작업 중 사용자가 gen.go.kr 어린이 게시판과 도박·성인물 홍보 범위를 제공해 19절의 실제 수집·점검으로 이어갔습니다. 관련 항목은 FR-027~033·FR-015~019·FR-039입니다.

- backend/app/evaluation.py·scripts/validate_site.py 추가. capture는 링크 깊이 기본 0·컨텍스트 8·프레임 깊이 3·공유 60초로 정적/동적 입력을 저장합니다. HTML·최상위 URL/프레임 경로·시각·환경/코드 해시·탐지 후보·실패/제외 사유를 capture.json에 기록합니다. 앱 result.json은 변경하지 않습니다.
- labels.json의 후보는 expected=null·reviewed=false, 전체는 complete=false로 생성합니다. 사용자가 실제 정상 사례와 놓친 양성도 추가해 판단·근거를 검수합니다. 위반 기본값 true·고정 confidence·합성 사례를 실제 광고 정답으로 자동 채택하지 않습니다.
- evaluate는 네트워크 없이 저장된 HTML을 재분석합니다. 부분 검수에서는 미검토 탐지를 오탐으로 세지 않고 지표를 null로 둡니다. 전체 양성 검수를 선언하고 policy·Boolean 정답·근거를 갖추면 TP/FP/FN·명시적 TN과 유형별 precision/recall/F1을 계산합니다. 분모가 없으면 null이며 정확도 100%를 만들지 않습니다.
- 정답 경로는 저장 DOM의 실제 요소로 재식별하며 같은 요소의 다른 selector도 일치시킵니다. 중복·모호/잘못된 경로·다른 수집의 정답·HTML 해시 불일치를 거부합니다. 수집 경고와 성공 문서 범위를 보고서에 보존합니다. 실패 수집만 있는 입력은 점수를 계산하지 않습니다.
- 기존 run 폴더는 덮어쓰지 않으며 .validation/은 Git에서 제외합니다. 재평가 보고서는 해당 run의 report.json으로 저장하고 기존 검수 정답은 수정하지 않습니다.

검증: `.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider` → **81 passed, 1 warning**. 기존 66개와 평가 관련 15개를 확인했습니다. 합성 입력의 TP/FP/FN/TN 집계·부분 검수·잘못된 정답·해시·중첩 프레임 selector·수집 실패를 검사했습니다. 실제 CLI를 로컬 HTTP 서버에 연결해 capture하고 서버를 종료한 뒤 오프라인 evaluate를 실행하는 흐름도 통과했습니다. 경고는 기존 TestClient/httpx 사용 중단 예고입니다.

탐지·API·UI·의존성은 변경하지 않았습니다. README·wiki에 검수 절차와 특징 평가 범위를 기록했습니다. 실제 사이트의 전체 광고 정확도 수치는 아직 없습니다. 도구와 아래 실제 점검을 `test: add snapshot evaluation and record real-site detection gaps` 커밋으로 기록하고 Git 상태·원격 조회로 업로드를 확인합니다.

## 19. gen.go.kr 실제 게시판 점검·내용 탐지 누락

2026-10-25 사용자가 광주 교육청 gen.go.kr 어린이 홈페이지 게시판에서 광고를 확인한 경험과 공공 웹사이트의 게시·은닉된 도박/성인물 홍보라는 검증 범위를 제공했습니다. 기존 문서에는 불법광고 목표와 4종 기법이 있었지만 도박·성인물이라는 구체 범주는 명시되지 않아 요구사항정의서·wiki에 사용자 확인 기준으로 반영했습니다. 공식 모집요강 원문 확인과는 구분합니다.

검색으로 어린이 홈페이지 `/child/xboard/board.php?tbnum=6`의 ‘배너모음’ 게시판을 찾았고, 프로그램으로 실제 응답을 수집했습니다. 검색 결과와 현재 수집을 대조하고 홍보 대상 외부 사이트는 직접 방문하지 않았습니다. 본문 수정·로그인·삭제 요청도 하지 않았습니다. 링크 깊이 0으로 헤더·수정/삭제 링크를 추가 탐색하지 않았으며, 브라우저의 자동 하위 리소스 로딩과 수집 대상 범위는 별개입니다.

| 입력 | 관찰 내용 | 실행 결과 |
|---|---|---|
| [게시물 107](https://gen.go.kr/child/xboard/board.php?mode=view&number=107&tbnum=6) | 도박/베팅 참여와 가입 혜택·특정 커뮤니티 이용을 유도하는 홍보 맥락 | 정적 수집 1컨텍스트·탐지 0, Edge 1.5초 대기 수집 3컨텍스트·탐지 0, 정적 API 200·0건 |
| [게시물 151](https://gen.go.kr/child/xboard/board.php?mode=view&number=151&tbnum=6) | 성인물 플랫폼 이용을 유도하는 홍보 맥락 | 정적 수집 1컨텍스트·탐지 0, 정적 API 200·0건. 성인 페이지 브라우저 렌더링은 실행하지 않음 |
| [목록](https://gen.go.kr/child/xboard/board.php?tbnum=6) | 위 게시판의 공개 게시물 목록과 홍보성 제목을 확인 | 정적 수집 1컨텍스트·탐지 0 |

게시물 107의 본문을 실제 Edge에서 관찰했습니다. 대상 p의 computed style은 display:block·visibility:visible·opacity:1·font-size:13px이고 너비 1116px, 높이 6864px였습니다. 본문으로 스크롤해 찍은 스크린샷에서도 홍보 내용이 정상 표시됐습니다. 즉 이 사례는 표시된 홍보성 텍스트가 4종 특징 규칙에 해당하지 않아 빠지는 내용 판별 공백입니다. 4종 특징 탐지의 오분류나 전체 페이지 정답 평가로 바꾸어 계산하지 않습니다. 0건은 광고가 없다는 근거가 아닙니다.

원본 HTML·설정·시각·해시는 로컬 .validation/gen-child-107-static-20261025, gen-child-107-browser-20261025, gen-child-151-static-20261025, gen-child-list-static-20261025에 보관했습니다. 정적 2건과 브라우저 107의 오프라인 evaluate도 실행했으며 미검수 전체 지표는 null입니다. 내용 존재 검토는 content-review.json에 별도로 기록해 특징 정답과 섞지 않았습니다. 107 브라우저 폴더에는 visual-review.json·visible-content.png가 있습니다. API 결과도 검증 폴더의 api-response.json·api-result.json으로 격리해 기존 result.json을 보존했습니다. 로컬 원본/스크린샷은 Git에서 제외합니다.

범위 제한에 따른 link_omissions와 정적 빈 iframe 제외 등의 경고가 있습니다. 페이지·프레임 전체의 광고 여부 검수를 끝내지 않았으므로 precision/recall·사이트 정확도를 산출하지 않습니다. 이번 결과는 실제 공개 페이지에서 확인한 두 광고 후보의 내용 탐지 누락 재현입니다. 법적 위반의 최종 판정이나 전체 교육청 사이트 검증 완료를 뜻하지 않습니다.

다음 작업은 일반 표시 도박·성인물 홍보의 내용 판별, 예방교육·보도 등 정상 문맥의 오탐 방지, 광고 후보와 필수 4종 기법의 독립적인 결과 표현입니다. 일반 광고에 임의로 기존 technique을 붙이지 않으며 제출 스키마 확장은 공식 원문과 대조해야 합니다.

## 20. 도박·성인물 내용 후보 판별·정상 문맥 제외

2026-10-25 사용자 승인으로 19절의 누락에 대응했습니다. 관련 항목은 FR-012~021·FR-027~033·FR-035~036·FR-039입니다. 판별은 content-rules-v1 규칙에 의한 검토 후보이며 법적 위반 확정이나 전체 정확도 통과가 아닙니다.

- backend/app/content.py 추가: 텍스트를 가장 가까운 블록으로 묶어 inline 조각은 합치고 다른 문단과는 섞지 않습니다. NFKC·일부 zero-width·공백 변형을 정리한 뒤 도박/성인물 표현과 가입·추천·홍보·무료시청 등 유도 표현이 가까이 있는지 확인합니다. 명시적인 예방교육·단속 보도·가입/접속 주의 문맥은 제외합니다. 다른 문단의 예방 문구로 광고 전체를 제외하지 않습니다.
- API는 content_candidates와 content_policy_version을 추가합니다. 후보는 category(GAMBLING/ADULT_CONTENT)·URL/위치·일치 표현·근거·policy_version·needs_review 상태를 가집니다. 같은 텍스트 블록에 해당하는 4종 기법만 연결하고 반복 iframe의 위치도 보존합니다. 위반 확정 Boolean과 고정 confidence는 새로 부여하지 않습니다.
- 4종 특징과 내용 판별이 모두 끝난 페이지 단위로 결과를 반영합니다. 중간 시간 초과는 해당 페이지의 두 결과를 함께 버리고 기존 504/부분 결과 정책을 적용합니다. 기존 시간 테스트의 ‘완료 시각’을 두 번째 단계 이후로 옮겼고 별도의 중간 만료 파일 보존 검사를 추가했습니다.
- 화면은 위장/은닉 수와 광고 후보 수를 따로 표시하며 도박/성인물 범주 필터를 추가했습니다. ‘광고 후보 다운로드’는 전체 후보·규칙 버전·분석 메타·수집 방식·warnings를 content-candidates.json으로 저장합니다. 기존 JSON 다운로드는 4종 result.json을 유지합니다. 두 다운로드 모두 필터와 독립적이며 실패·새 분석·빈 입력에 비활성화합니다.
- capture/evaluate도 내용 후보·규칙 버전·후보 수를 별도 기록합니다. 기존 labels와 precision/recall/F1은 4종 특징만 평가하므로 metrics_purpose=four_technique_features_only로 명시했습니다. 내용 후보 정확도를 기존 지표로 대체하지 않습니다.

실제 확인:

| 입력 | 이전 | 내용 판별 추가 후 |
|---|---|---|
| gen.go.kr 어린이 게시물 107 | 4종 0, 내용 검사 없음 | API 200·GAMBLING 2개(제목/본문), 4종 0 |
| gen.go.kr 어린이 게시물 151 | 4종 0, 내용 검사 없음 | API 200·ADULT_CONTENT 2개(제목/본문), 4종 0 |
| [교육청 예방 홍보 자료 454470](https://gen.go.kr/xboard/board.php?mode=view&number=454470&tbnum=520) | 비교 입력 추가 | 경찰청 제작 도박/성폭력 예방 안내 문맥 확인, 정적 내용 후보 0·4종 0 |

107의 저장된 Edge DOM과 두 정적 스냅샷의 오프라인 재분석도 각각 내용 후보 2개를 반환했습니다. 실제 API 재요청도 두 건 모두 2개로 확인했습니다. 이전 결과를 덮어쓰지 않고 로컬 각 run의 api-response-after-content-v1.json·api-result-after-content-v1.json으로 격리했습니다. 예방자료는 .validation/gen-prevention-454470-content-v1에 보관합니다. 경로 탐색 중 자료실 목록 454287도 수집했지만 본문 검증 대상은 링크를 확인한 454470입니다. 모든 수집은 링크 깊이 0이며 전체 사이트 검증이 아닙니다.

검증:

```text
.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
105 passed, 1 warning

node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
Frontend checks passed: API, modes, filters, partial results, failure reset, full JSON downloads, empty results, UTF-8, URL cleanup.

.venv\Scripts\python.exe -B scripts/test_browser.py
기존 위치·UI·동적 수집·다운로드 검사 통과
Content checks passed: promotion candidates, education exclusion, category filters, separate full download, original result schema
```

구현 전 내용 판별 모듈 누락으로 새 테스트 수집이 실패했습니다. 구현 후 새 24개를 포함한 전체 105개가 통과했습니다. 홍보/정상/단독 단어·inline/문단 경계·보이지 않는 문자·중첩/반복 프레임·다른 문단 특징 연결 방지·API와 시간 초과를 확인했습니다. 단순 동화 등장인물 이름인 토토와 가입 안내를 도박으로 연결하지 않는 사례도 추가했습니다. 실제 Edge는 로컬 합성 입력에서 후보 수·정상 문맥 제외·범주 필터·두 파일의 전체 결과·규칙 버전·실패 비활성화를 확인했습니다. 환경·TestClient 경고는 17절과 같습니다.

남은 한계: 제한된 어휘·근접 문맥의 규칙이므로 사전 밖 표현·문단 간 광고·이미지·의미적 위장·보호 문구를 섞은 홍보에서 누락/오탐이 생길 수 있습니다. 실제 양성 2건과 정상 1건은 전체 정확도 지표가 아닙니다. 기존 result.json의 is_violation 임시 기본값 true와 제출 스키마는 변경하지 않았으므로 위반 판정 정책은 별도 정리가 필요합니다. 내용 후보를 일반 광고에 임의의 기존 technique을 부여하는 방식으로 합치지 않았습니다.

README·wiki·진행 기록을 갱신했습니다. 의존성·기존 result.json은 보존했습니다. 커밋 메시지는 `feat: detect gambling and adult promotion candidates`이며 Git 상태·원격 조회로 업로드를 확인합니다. 다음은 내용 후보 정답 검수·평가 범위 확대와 위반 판정/제출 표현 정책 정리입니다.
## 21. 내용 후보 독립 정답 검수·오프라인 평가

2026-10-25 다음 작업 요청에 따라 내용 후보 정답과 평가를 4종 기법 평가에서 분리했습니다. 법적 위반 판정과 제출 형식 확정은 남아 있으며, 이번 작업은 검수 근거를 보관하고 내용 존재 탐지 결과를 평가하는 범위입니다.

- 새 capture는 content-labels.json도 생성합니다. 이전 저장본은 init-content-labels 명령으로 초안을 추가하며 기존 검수는 덮어쓰지 않습니다.
- evaluate RUN --kind content는 content-report.json을 생성합니다. 기본 4종 기법 정답·보고서는 유지합니다. 블록 위치·범주별 TP/FP/FN/TN과 범주별 지표를 계산하며 미탐·정상 블록은 수동 추가합니다.
- 부분 검수에서는 미검수 후보를 오탐으로 처리하지 않고 지표를 null로 유지합니다. 전체 저장 문서의 양성 블록·범주를 검수하고 policy를 기재해야 전체 지표를 계산합니다. 수집에서 누락된 페이지나 프레임까지 평가한 점수는 아닙니다.
- 동등한 선택자·중첩 프레임을 해석하고, 모호한 선택자·중복 정답·잘못된 Boolean·검수 근거 누락·해시 불일치를 거부합니다. 보고서는 원본 연결 해시와 정답·평가 코드 해시를 기록합니다.
- 선택적 violation_verdict는 기본 unreviewed입니다. 판단을 기입하려면 내용 항목 검수, reviewer와 verdict_reason이 필요합니다. 판단 메모는 내용 점수와 별도로 보존하며 법적 확정·API 판단·제출 JSON으로 자동 전환하지 않습니다.

저장된 실제 HTML에 네트워크 재요청 없이 적용했습니다. 앞서 수동 관찰한 본문과 대조해 107은 GAMBLING TP 1, 151은 ADULT_CONTENT TP 1, 454470의 예방교육 본문은 두 범주 TN 2입니다. 홍보 글 각각 제목 후보 1건은 미검수로 남겼습니다. 예방교육 글도 전체 문서 검수 완료로 표시하지 않았습니다. 세 저장본 모두 complete=false 및 metrics=null이며 전체 사이트의 정확도나 법적 위반 판정 결과가 아닙니다. 각 run의 content-labels.json·content-report.json은 .validation/에 보관하며 원본 HTML과 함께 Git에서 제외합니다.

검증: `.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider` → **124 passed, 1 warning**. 새 평가 관련 19개 테스트를 포함합니다. 합성 입력에서 TP/FP/FN/TN·부분 검수·범주 분리·지표 분모 0·위반 판단 근거·해시 변조·중첩 프레임·기존 파일 보존·실제 CLI의 보고서 분리를 확인했습니다. 합성 시험의 수치는 실제 광고 탐지 성능이 아닙니다. 경고는 기존 Starlette/TestClient의 httpx 사용 중단 예고입니다. API·UI·탐지 규칙·제출 result.json은 변경하지 않았습니다.

다음 작업은 검수 범위를 늘려 규칙의 미탐·오탐 사례를 축적하고, 공식 공모전 판정·제출 원문을 확인해 기존 is_violation 임시 기본값 및 일반 표시 광고의 제출 표현 정책을 정하는 것입니다. 이번 커밋 메시지는 `feat: add independent content candidate evaluation`입니다.

## 22. 문장 문맥 회귀 사례 확장·오탐/미탐 개선

2026-10-25 다음 작업 요청에 따라 합성 문장 문맥 검수 사례 22개와 사례별 선정 근거를 추가하고, 수정 전 실패를 재현한 뒤 내용 규칙을 content-rules-v2로 개선했습니다. 새 실제 사이트를 수집한 작업은 아니며, 기존 실제 저장본은 회귀 확인에 사용했습니다.

- tests/fixtures/content/cases.json: 일반 홍보·범주 혼합·예방 안내와 홍보의 공존·광고 신고/삭제 요청·다른 문장 일반 가입/무료 자료·인용 보도·도메인 마침표·단독 주제 사례입니다. 각 사례의 두 범주를 독립 채점합니다.
- 수정 전 동일 데이터에서 12/22 사례 통과, TP 6·FP 6·FN 4·TN 28이었습니다. 예방 문장이 독립 홍보 문장까지 지우는 미탐 4개와 신고/삭제 요청 및 다른 문장 연결 오탐 6개를 재현했습니다.
- content.py는 같은 텍스트 블록 내에서도 문장 경계를 적용합니다. 마침표/물음표/느낌표 뒤 공백·끝 및 전각 문장부호를 사용하며 도메인 내부 마침표는 유지합니다. 주제 앞 45/뒤 100자 검사 창은 같은 문장을 넘지 않습니다. 광고 신고·삭제 요청 표현을 정상 문맥에 추가했습니다. 위치 단위·범주별 블록당 후보 1개·4종 기법 연결은 유지합니다.
- 수정 후 22/22 사례 통과, TP 10·FP 0·FN 0·TN 34입니다. 규칙 수정에 사용한 합성 회귀 데이터이므로 실제 사이트 정확도나 독립 성능 평가로 해석하지 않습니다.
- scripts/benchmark_content.py로 같은 데이터의 집계와 사례별 결과·데이터/탐지 코드 해시·규칙 버전을 출력합니다. 선택적 출력 파일은 독점 생성으로 기존 파일 덮어쓰기를 거부합니다. 이전/이후 보고서는 .validation/content-benchmark-v1.json 및 content-benchmark-v2.json에 보관했습니다.

실제 저장 HTML의 동일 정답으로 재평가한 결과 107·151은 각각 내용 후보 2개·검수된 본문 TP 1개, 예방교육 454470은 후보 0개·두 범주 TN 2개로 유지됐습니다. 기존 보고서를 보존하고 각 run의 content-report-v2.json으로 기록했습니다. 모두 부분 검수이므로 metrics=null이며 신규 실제 데이터나 추가 법적 판단은 없습니다.

검증: `.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider` → **146 passed, 1 warning**. 기존 124개와 새 사례 22개가 통과했습니다. `.venv\Scripts\python.exe -B scripts/test_browser.py`도 Edge 156.0.4314.42에서 위치·UI·동적 수집·다운로드·내용 필터·규칙 v2 포함 통과했습니다. 경고는 기존 Starlette/TestClient httpx 사용 중단 예고입니다. 의존성·제출 스키마·is_violation 임시 기본값은 보존했습니다.

한계: 여러 문장에 분산된 홍보는 누락될 수 있고, 인용·보도 문맥이 이전 문장에만 있으면 오탐이 남을 수 있습니다. 구두점 없는 문장·줄바꿈·새 은어·이미지·동영상도 추가 검증이 필요합니다. 다음 단계는 실제 검수 사례 확대와 문장 간 문맥 검증, 공식 공모전 원문에 따른 위반 판정·제출 정책 확정입니다. 커밋 메시지는 `fix: refine promotional sentence context and report exclusions`입니다.

## 23. 업로드 PDF 대조·공식 출력 및 평가 규칙 반영

2026-10-25 사용자가 원문과 Markdown의 차이를 확인한 뒤 반영을 승인했습니다. 원문은 `공공 웹사이트 불법광고 탐지 도구 개발 공모전 모집요강.pdf` 18쪽이며 SHA-256은 `69d72dee6058d59f7799454a9460f190f9466e9dd991ce4980415919b84605b6`입니다. PDF가 프로젝트에 있었는데도 이전 작업에서 확인을 미룬 점을 바로잡았습니다. PDF의 표·예시를 대조한 것이며 별도 기계 판독용 공식 JSON Schema 파일이나 주최 측 정답셋을 받은 것은 아닙니다.

공식 확인 사항:

- 1·5쪽: 도박·성인물 등 게시/은닉 불법광고, 필수 4종·화면·결과 파일. 4종의 예시와 범위는 기존 방향과 일치하며 AI는 선택사항입니다.
- 6~7쪽: 적격평가 45점 검출 개수·35점 추출 정확도·20점 시간. 탐지 시작~완료 30분 초과는 시간 항목 0점이며 자동 전체 0점으로 해석하지 않습니다. 본심사는 적격평가 환산 50·실무 활용성 20·도입 가능성 10·창의성/독창성 20점입니다.
- 2·5·8~9·15~18쪽: Windows 11 구동 파일·전체 소스·실행/빌드 매뉴얼·사용설명서, 결과 생성 경로의 첫 장 안내, 외부 AI 키 교체 조건, 신청서·서약서·동의서·5~10매 기획서가 필요합니다. 실제 접수와 배포 검증을 완료한 것은 아닙니다.
- 10~14쪽: TOPIC 표기, 정규화 전 근거 원문, 필수 4종 파일과 ETC/extra_finding 추가 결과 파일, 실제 같은 요소의 선택자 인정, URL 동등성 규칙과 파싱/스키마 오류 처리 기준을 확인했습니다.

구현:

- detection.py는 판정 설명 evidence와 원문 source_text를 구분합니다. 원문은 직접 텍스트 노드를 원래 순서로 연결해 공백·줄바꿈·유사 문자·자모·zero-width를 보존합니다. 제출 evidence_text는 설명 접두사·정규화·500자 제한을 적용하지 않으며 원문 없는 제출 입력은 거부합니다. HTML 엔티티가 해석된 DOM 텍스트이지 HTML 마크업 문자열은 아닙니다. 동적 모드는 수집한 DOM 시점의 원문입니다.
- content.py도 블록에 귀속된 원래 텍스트 노드를 보존합니다. result.py는 meta.topic=TOPIC과 PDF 기반 결과 모델을 적용하고, 필수 결과와 별도로 result_extra.json을 구성합니다. 추가 결과는 ETC + GAMBLING_PROMOTION_CANDIDATE/ADULT_CONTENT_PROMOTION_CANDIDATE이며 PDF 13쪽 예시처럼 is_violation을 자동 추가하지 않습니다. 필수 4종의 기존 is_violation 임시 기본값 true는 아직 판정 정책 과제로 남깁니다.
- 성공 분석은 같은 실행 meta로 result.json·result_extra.json을 프로젝트 루트에 생성합니다. 0건도 빈 배열로 저장하고 수집 실패/분석 전 시간 초과는 두 파일을 보존합니다. 별도 result_extra_json API 응답과 화면 다운로드를 추가했습니다. 필터와 독립적이며 다른 요청이 서버 파일을 바꿔도 화면이 가진 응답을 다운로드합니다. 두 파일의 동시 요청·디스크 오류에 대한 트랜잭션 보장은 미구현입니다.
- comparison.py는 PDF 12쪽의 URL 동등성(http/https·끝 슬래시·fragment 무시, 쿼리 순서 무시/값 구분)을 제공합니다. 제출 중복 제거와 오프라인 정답 비교에 적용하되 HTTP 수집 주소는 변경하지 않습니다. 동등 URL이 서로 다른 저장 문서를 가리키면 모호성 오류로 평가를 거부합니다. 선택자 별칭·중첩 프레임의 요소 식별은 유지하며 비교 코드 해시도 보고서에 기록합니다.
- 요구사항정의서·wiki·README·project-guide의 현재 기준을 갱신하고 제출 서류 NFR-005를 추가했습니다. PDF를 문서의 근거 자료로 보존합니다. 과거 진행 기록과 기존 result.json 산출물은 역사 기록으로 남기며 새 실행 성공 증거로 취급하지 않습니다.

검증:

```text
.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
162 passed, 1 warning

node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
Frontend checks passed

.venv\Scripts\python.exe -B scripts/test_browser.py
Edge 156.0.4314.42: 위치·UI·동적 수집·다운로드·내용 후보 검사 통과
```

새 PDF 계약 검증 16개는 URL 동등/구분, 원문 장문·공백·Unicode 보존, 원문 누락 거부, 두 결과 파일·인코딩·0건·수집 실패 보존, 정답 URL/선택자 별칭과 충돌 문서 거부를 확인합니다. 기존 시간 초과 검증에도 추가 결과 보존을 포함했습니다. Edge에서는 필수/추가 결과의 기본·동적·부분·빈 결과·필터 독립성·다른 요청 뒤 이전 화면 응답 보존·실패 비활성을 확인했습니다. 초기 Edge 검사에서 이전 화면 응답을 다른 요청의 서버 파일과 비교한 검사 시점 오류가 있어, 서버 일치 확인은 해당 분석 응답 직후로 옮기고 다운로드는 화면 보관 응답과 비교하도록 수정했습니다. 최종 검증은 통과했습니다. 기존 TestClient/httpx 경고 1건은 유지합니다.

다음은 필수 4종 특징을 실제 광고 판단과 연결하는 정책·정확도 및 computed style 기반 은닉 판정 보강입니다. Windows 구동 파일 패키징·사용설명서 최종본·신청 서류·실제 접수 여부 확인도 남아 있습니다. 자체 계약 테스트는 주최 측 적격평가 통과를 뜻하지 않습니다. 커밋 메시지는 `feat: align contest outputs and evaluation with source PDF`입니다.

## 24. 계산 스타일·좌표 기반 은닉 특징 판별

2026-10-25 다음 단계 요청에 따라 필수 TRANSPARENT/OFFSCREEN의 브라우저 표시 상태 판별을 보강했습니다. 이전 동적 모드는 DOM만 수집하고 탐지는 inline 선언만 읽어 CSS 클래스·상속을 놓치거나 실제로 표시되는 요소를 오탐할 수 있었습니다. 실제 광고 여부의 판정 정책은 이번 기능과 별개입니다.

- rendered_snapshot.js: 문서별 단일 동기 JavaScript 호출에서 HTML과 직접 텍스트를 가진 HTML 요소의 구조 선택자·원문·계산 스타일·문서 좌표를 함께 수집합니다. 실제 DOM에 식별 속성을 추가하거나 수정하지 않습니다. 내부/외부 CSS와 변수·우선순위를 브라우저가 적용한 결과를 읽습니다. 문서 내 관찰은 순차적이며 프레임 트리 전체의 원자적 고정은 아닙니다. 반복 처리에 공유 Deadline 예산을 적용하되 브라우저 내부 연산을 즉시 강제 중단하지는 않습니다.
- rendered.py: 정책 rendered-style-rules-v1. 조상 opacity:0·계산 visibility·투명 글자·불투명 단색 배경과 같은 글자색은 TRANSPARENT, 조상 display:none·상속된 0~1px 글꼴·양의 크기인 요소 전체가 문서의 왼쪽/위쪽 음수 영역인 경우는 OFFSCREEN 후보입니다. 그림자·윤곽선이 있으면 색상만으로 투명 판정하지 않습니다. 이미지/그라데이션·반투명 합성·표준 RGB 이외 색상은 추측하지 않습니다.
- browser.py/crawler.py는 문서·프레임마다 관찰값을 전달합니다. detection.py는 구조 선택자의 단일 요소·원문 일치·중복 여부를 검증하고 CSS 기법에서는 관찰값을 inline 후보보다 우선합니다. 실제 !important 우선순위와 일부 보이는 음수 배치를 반영합니다. 새 관찰값이 없는 정적 모드·과거 캡처는 기존 규칙으로 처리합니다. HOMOGLYPH/JAMO·제출 스키마·is_violation 임시 기본값은 바꾸지 않았습니다.
- capture.json 문서별 rendered_style(schema_version=1)을 보존해 브라우저·네트워크 없이 재평가합니다. HTML 해시와 정답의 capture 해시는 유지하며 관찰 원문/경로가 불일치하면 거부합니다. 보고서에 rendered_policy_version·판정 코드 해시와 observation_basis(rendered_documents/static_documents)를 추가했습니다. 이전 browser 캡처에 관찰값이 없다면 정적 문서로 집계합니다.

실제 Edge 합성 검증:

- 내부 CSS 클래스 opacity·색상·display:none·상속 visibility/글꼴·음수 배치, 외부 CSS, 동일 단색 배경, 스타일이 적용된 iframe 자식에서 정답 특징 9개를 모두 확인했습니다.
- !important로 opacity가 복구된 요소, 일부 보이는 left:-1px 요소, 스크롤 아래 정상 요소, 같은 색이지만 그림자/윤곽선으로 읽을 수 있는 요소 5개는 정상 경계로 확인했습니다. 같은 입력을 기본 정적 모드로 분석하면 실제로 보이는 override·부분 음수 배치·윤곽선 요소에 특징 3개가 남는 차이를 검증했습니다. 정적 규칙을 실제 CSS 판정 완료로 표현하지 않습니다.
- 별도 프로세스의 실제 CLI로 browser capture를 생성하고 독립적으로 지정한 양성 9·음성 5 정답으로 오프라인 평가했습니다. TP 9·FP 0·FN 0·TN 5이며 이 수치는 합성 특징 회귀 검증입니다. 새 실제 사이트 수집·일반 정확도 측정은 아닙니다.

검증:

```text
.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
183 passed, 1 warning

node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
Frontend checks passed

.venv\Scripts\python.exe -B scripts/test_browser.py
기존 위치·UI·동적 수집·다운로드·내용 후보 검사 통과
Computed styles passed: CSS·상속·배경·좌표·정상 경계·프레임·CLI 저장본 재평가
```

새 21개 Python 검증은 계산 관찰값 판정, 정상 경계, inline 취소, 관찰 원문/경로 불일치·중복 거부 및 무브라우저/무네트워크 재평가를 포함합니다. 기존 TestClient/httpx 사용 중단 경고 1건은 유지합니다. 구현 중 브라우저 시험의 문자열 선택자 비교를 실제 요소 비교로 수정했고, Playwright 실행 중 같은 스레드에서 재시작할 수 없어 capture는 실제 CLI 별도 프로세스로 분리했습니다. 최종 검증은 통과했습니다.

README·wiki·정적 사례 설명과 현재 요약을 갱신했습니다. 의존성·기존 원본 캡처·루트 결과 산출물은 보존했습니다. 남은 범위는 광고 판정 연결·실제 정확도, 가림/clip·양의 방향 화면 밖·SVG/가상 요소/Shadow DOM·배경 합성·프레임 요소 자체의 은닉이 자식 프레임에 미치는 영향, 시간 강제 중단·패키징입니다. 다음 단계는 필수 4종과 홍보 내용의 연결 및 정상 숨김 UI/외국어/초성의 오탐 정책 정리입니다. 커밋 메시지는 `feat: detect rendered CSS hiding and replay saved styles`입니다.

## 25. 홍보 원문 구간과 특징 연결·제출 후보 정책

2026-10-25 다음 작업 요청에 따라 필수 4종 특징과 홍보 내용을 연결하고 정상 외국어·초성·숨김 UI가 자동 위반으로 제출되는 경로를 수정했습니다. 정책 도입 전 새 시험은 8개 통과·19개 실패였으며 초기 정상/무관 특징 사례 10개도 기본 true로 제출되는 문제를 재현했습니다. PDF는 필수 필드와 기법을 정하지만 상세 키워드·의심 사례 선택 정책은 지정하지 않으므로 아래는 구현 정책입니다.

- textnorm.py: 판별용 NFKC·casefold·한정 키릴 닮은꼴 매핑·현대 한글/호환 자모 재조합·공백/일부 zero-width 제거를 구현했습니다. 정규화된 문자마다 원문 범위를 추적하며 원문은 바꾸지 않습니다. 전체 Unicode 위장이나 모든 자모/은어를 처리한다는 의미는 아닙니다.
- content-rules-v3: 같은 블록·문장·근접 문맥의 주제와 유도 표현을 찾습니다. 기존 22개 내용 회귀 사례를 유지하고 PDF 예시의 자모 카지노/보너스, 전각 mega-BET, 먹튀검증/텔레그램 유도, 무료 슬롯 체험을 검증합니다. 피해상담 등 명시적 보호 문맥은 제외합니다.
- feature_links: 단순히 같은 블록이라는 이유로 특징을 연결하지 않습니다. HOMOGLYPH/JAMO의 실제 의심 문자 또는 CSS 특징 요소의 의미 있는 직접 텍스트가 홍보 주제/유도 표현의 원문 범위와 겹쳐야 합니다. 무관한 외국어·전각 인사말·숨김 메뉴·자모 사이 숨김 zero-width를 광고 기법으로 오인하지 않게 했습니다. URL/프레임/블록/문맥을 유지하며 링크는 location+technique로 기록합니다.
- feature-content-policy-v1: 관련 근거가 있는 특징만 included로 평가해 result.json에 규칙상 is_violation=true로 전달합니다. 나머지는 needs_review로 화면에 남기고 정상(false)이나 불법(true)으로 확정하지 않습니다. API는 모든 특징과 선택/검토 이유·관련 범주·정책 버전을 반환합니다. 결과 다운로드는 선택된 제출 후보만 담으며 화면에서 특징·제출·검토 건수를 구분합니다.
- Result Builder의 기본 true 호환 동작을 제거했습니다. source_text와 명시적 Boolean이 없는 내부 제출 입력은 거부하고 API는 선택된 후보만 전달합니다. 기존 합성 특징/직렬화 시험은 명시적 테스트 판정값을 사용하며 이를 실제 광고 정답으로 간주하지 않습니다. 공식 meta/findings 구조·원문 근거·추가 ETC 파일 규격은 유지했습니다.
- 한 페이지는 특징·내용·제출 후보 평가 세 단계가 완료돼야 반영합니다. 공유 시간 만료 시 해당 페이지의 중간 결과를 버리고 앞선 완료 페이지가 없으면 504와 두 파일 보존, 있으면 부분 결과를 반환합니다. 새 정책 단계의 시간 초과와 기존 부분 완료 시험을 확인했습니다.
- capture/evaluate는 제출 평가·선택 건수·정책 및 정규화 코드 해시를 별도로 기록합니다. 기존 feature/content 정답과 지표는 그대로 해당 목적에 사용하며 선택 건수를 제출 정책의 정확도라고 부르지 않습니다.

실행 검증:

```text
.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
219 passed, 1 warning

node --preserve-symlinks-main --preserve-symlinks scripts/test_frontend.cjs
Frontend checks passed

.venv\Scripts\python.exe -B scripts/test_browser.py
기존 위치·수집·CSS·내용·다운로드·저장본 재평가 검사 통과
Submission policy passed: 4 attributed feature promotions, 4 retained review findings
```

새 36개 Python 검증은 정규화/원문 범위·필수 4종 홍보 연결·무관한 특징 제외·원문 보존·한 요소의 복수 범주를 1건으로 제출·기본 true 제거·정책 시간 초과 보존·오프라인 feature/제출 평가 분리를 포함합니다. Edge에서는 자모·전각·투명 CSS·작은 글꼴 홍보 4건은 제출하고 외국어·초성·숨김 메뉴·같은 문단의 무관한 숨김 4건은 검토로 보존했습니다. 화면 집계·원문·필터·파일과 다운로드 일치도 확인했습니다. 경고 1건은 기존 Starlette/TestClient httpx 사용 중단 예고입니다.

기존 실제 저장본을 네트워크 재요청 없이 평가했습니다. gen.go.kr 107·151은 각각 내용 후보 2개·필수 4종 제출 0개, 예방교육 454470은 내용 후보 0개·필수 제출 0개입니다. 기존 본문 검수 TP 1개씩·예방교육 두 범주 TN 2개와 metrics=null은 유지됩니다. 일반 표시 홍보를 필수 기법으로 임의 분류하지 않으며 추가 파일의 후보로 유지합니다. .validation/의 각 run에 content-report-policy-v1-final.json을 별도로 저장했습니다. 합성 내용 22개도 통과하며 보고서는 content-benchmark-v3-final.json에 보관합니다. 이 자료들은 실제 전체 정확도나 법적 판정 결과가 아닙니다.

README·wiki·요구사항정의서·개발 지침과 현재 요약을 갱신했습니다. 의존성·기존 캡처/검수·루트 산출물은 보존했습니다. 한계: 관련 어휘나 정규화·문맥을 놓치면 실제 광고도 검토 상태에 남아 제출에서 누락될 수 있습니다. 인용·예방 문구를 섞은 홍보·이미지·문단 간 맥락 등 미탐/오탐과 실제 정확도 검증이 남아 있습니다. 규칙상 true는 법적 확정이 아니며 파일 0건도 광고 부재의 근거가 아닙니다. 다음은 실제 검수 범위 확대 및 검토 결과 확정/보존 흐름, Windows 구동 파일 패키징·설명서 준비입니다. 커밋 메시지는 `feat: select submissions from attributed promotional evidence`입니다.
