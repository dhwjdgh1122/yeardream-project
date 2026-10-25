# 프로젝트 개발 작업 지침

> 2026-10-23 정합성 갱신: 이 문서는 개발 진행·설명·검증 방식을 담당합니다. 요구사항은 [요구사항정의서.md](요구사항정의서.md), 설계·API·location·결과는 [wiki.md](wiki.md), 실행 명령은 [README.md](README.md), 현재 상태·다음 작업은 [project.md](project.md)를 참조합니다. 아래 초기 단계·예시는 현재 완료 기록이 아닙니다.
>
> 2026-10-25 업로드 PDF 원문 대조 완료: 필수 4종·Windows 11/GPU 없는 PC·결과 표/예시·배점·제출 서류는 요구사항정의서와 wiki에 반영했습니다. 30분 초과는 검출 시간 항목 0점이며 전체 자동 실격을 뜻하지 않습니다. Python 버전·프레임워크·탐색 한도는 구현 선택입니다. 아래 초기 예시는 현황이 아니며 최신 코드·검증은 project.md를 따릅니다.

---

# 0. 작업 체계

사용자 혼자 전체 프로젝트를 담당한다. 구현·통합뿐 아니라 탐지 기준·정답 데이터·오탐·미탐·정확도·위치 검증도 같은 사용자의 업무다. 개발과 분석은 업무 종류이며 별도 인력의 승인이나 검수를 기다리지 않는다. 코딩 에이전트는 구현 이유·변경 내용·검증 결과·남은 판단 사항을 설명하며 이 작업을 돕는다.

---

# 1. 프로젝트 목표

사용자가 웹사이트 URL을 입력하면 프로그램이 해당 웹사이트를 탐색하고 다음 영역에서 불법광고를 탐지한다.

```text
입력 URL
 ↓
하위 페이지
 ↓
게시글
 ↓
댓글
 ↓
iframe
 ↓
iframe 내부
 ↓
nested iframe
```

필수 탐지 유형은 다음 4개다.

```text
HOMOGLYPH
JAMO
TRANSPARENT
OFFSCREEN
```

탐지 결과는 반드시 정확한 위치와 함께 제공하고 공모전 요구 형식에 맞는 `result.json`을 생성한다.

최종 사용자에게는 탐지 결과를 확인할 수 있는 UI를 제공한다.

---

# 2. 절대로 잊지 말아야 할 프로젝트 우선순위

개발 중 기능을 추가하고 싶은 경우에도 아래 순서를 반드시 따른다.

```text
1. 공모전 필수 요구사항
        ↓
2. 웹사이트 탐색
        ↓
3. 필수 4종 탐지
        ↓
4. 정확한 Location
        ↓
5. result.json
        ↓
6. 결과 UI
        ↓
7. 정확도 / 안정성
        ↓
8. 추가 기능
```

핵심 기능이 완성되지 않은 상태에서 다음 기술을 먼저 도입하지 않는다.

```text
RAG
LangChain
LangGraph
DB
외부 LLM API
복잡한 AI Workflow
```

필요성이 명확해진 경우에만 검토한다.

---

# 3. 공모전 공식 요구사항과 팀의 개발 제안을 구분하라

개발 과정에서 다음 세 가지를 반드시 구분한다.

## 3.1 공식 요구사항

공모전 모집요강에 명시된 내용.

예:

- URL 입력
- 웹사이트 탐색
- 필수 4종 탐지
- 정확한 Location
- `result.json`
- 평가 환경
- 30분 제한

## 3.2 팀의 구현 제안

예:

- FastAPI
- Playwright
- 특정 폴더 구조
- API endpoint
- Queue
- 특정 MAX_DEPTH
- 특정 MAX_URLS

이것들은 공모전이 반드시 요구하는 기술이 아니다.

## 3.3 아직 결정되지 않은 사항

아직 실제 테스트를 하지 않은 기술이나 구조는 확정된 것처럼 말하지 않는다.

모르면:

> "아직 결정되지 않음"

이라고 명시한다.

추측으로 구현하지 않는다.

---

# 4. 문서 기준과 역할

업로드된 공모전 PDF를 최우선으로 적용한다. PDF 페이지별 근거와 채점·제출 조건은 요구사항정의서, 출력 표/예시의 구현은 wiki를 기준으로 한다. 별도 JSON Schema 파일의 제공과 PDF 표 기반 검증을 혼동하지 않는다. 팀 문서는 주제별로 기준을 나눈다.

- 요구 범위·담당·통과 기준: 요구사항정의서.md
- 구조·탐지·API·데이터·location: wiki.md
- 설치·실행·테스트: README.md
- 현재 상태·검증·문제·다음 작업: project.md
- 개발 진행·설명·보고: 이 문서

규격은 기준 문서에서 관리하고 나머지는 참조한다. 현재 코드는 현황의 근거이며 목표 요구사항을 대체하지 않는다. 충돌 시 관련 문서·코드·테스트 영향을 검토하고 수정한다.

---

# 5. GitHub Repository에 대한 전제

사용자가 관리하는 저장소를 기준으로 한다. 2026-10-24 사용자 지정 저장소 `https://github.com/dhwjdgh1122/yeardream-project.git`를 `origin`으로 연결하고 로컬 `main` 브랜치를 초기화했다. 최신 연결·검증 기록은 project.md 13절을 참조한다. 예전 팀 구성이나 저장소 소유권을 현재 상태로 가정하지 않는다. 기존 코드는 검토 후 재사용한다.

---

# 6. 기존 코드 인수 원칙

기존 프로젝트에서 이미 작성된 코드가 있다면 다음 순서로 판단한다.

```text
기존 파일 발견
 ↓
무슨 역할인지 확인
 ↓
실제 실행
 ↓
테스트
 ↓
최신 WIKI와 비교
 ↓
공모전 요구사항과 비교
 ↓
재사용 / 수정 / 폐기
```

절대로 다음 행동을 하지 않는다.

```text
기존 코드 전부 삭제
새 프로젝트 처음부터 생성
기존 코드를 검토하지 않고 대규모 덮어쓰기
```

기존 코드가 잘 만들어져 있다면 적극적으로 재사용한다.

---

# 7. 개발자의 작업 방식

나는 이 프로젝트의 유일한 AI Service Developer다.

나는 모든 코드를 직접 처음부터 작성하는 방식보다 **AI 코딩 도구를 활용한 Vibe Coding 방식**으로 개발한다.

따라서 너는 나에게 다음을 제공해야 한다.

```text
무엇을 만드는지
↓
왜 필요한지
↓
어떤 파일을 수정하는지
↓
코드를 어떻게 작성하는지
↓
어떻게 실행하는지
↓
무엇이 나오면 성공인지
↓
오류가 나면 어떻게 확인하는지
```

---

# 8. 절대로 한 번에 전체 프로젝트를 만들지 마라

다음과 같은 요청에 대해 전체 코드를 한 번에 생성하지 않는다.

```text
"크롤러부터 프론트까지 전부 만들어줘"
```

대신 기능을 작게 나눈다.

예:

```text
URL 입력
 ↓
HTTP 요청
 ↓
HTML 확인
 ↓
링크 하나 수집
 ↓
여러 링크 수집
 ↓
중복 제거
 ↓
하위 페이지 탐색
 ↓
iframe 탐색
 ↓
DOM 분석
```

각 단계마다 실행하고 확인한다.

---

# 9. 모든 개발 단계에서 사용하는 설명 형식

각 작업은 반드시 다음 형식으로 설명한다.

## ① 이번 단계의 목표

무엇을 만들 것인지 설명한다.

## ② 왜 필요한가

전체 프로젝트에서 어떤 역할인지 설명한다.

## ③ 현재 상태

현재 프로젝트에서 이미 구현된 부분과 구현되지 않은 부분을 확인한다.

## ④ 수정할 파일

정확한 경로를 알려준다.

예:

```text
app/crawler/scan.py
```

## ⑤ 코드

필요한 최소 코드만 제공한다.

## ⑥ 코드 설명

초보 개발자가 이해할 수 있도록 설명한다.

## ⑦ 실행 방법

VS Code 터미널에서 실행할 명령어를 정확하게 제공한다.

## ⑧ 예상 결과

정상적으로 실행되면 무엇이 보여야 하는지 설명한다.

## ⑨ 오류 발생 시 확인

자주 발생할 수 있는 오류와 확인 방법을 설명한다.

## ⑩ 완료 체크

```text
[ ] 실행 성공
[ ] 예상 결과 확인
[ ] 테스트 성공
[ ] Git commit
```

---

# 10. 승인 범위 안에서 단계별로 진행하라

기능을 작은 단위로 나누고 각 단위를 실행·검증한 뒤 다음으로 넘어간다. 기본적으로 결과를 보고하고 다음 범위를 사용자와 정한다.

사용자가 여러 작업의 연속 진행을 미리 승인한 경우에는 승인된 범위 안에서 중간 확인을 반복하지 않고 구현·검증·문서 갱신을 이어간다. 연속 승인 범위와 종료 여부는 project.md에서 관리한다. 새로운 판단이 필요한 항목은 기록하고 독립적으로 가능한 승인 작업부터 마친다. 별도 승인 없는 파괴적 작업·외부 게시로 범위를 넓히지 않는다.

---

# 11. 프로젝트 전체 개발 순서

다음 순서로 개발한다.

```text
STEP 0
새 Repository 확인

STEP 1
프로젝트 구조 확인

STEP 2
Python 환경 확인

STEP 3
가상환경 구성

STEP 4
기존 코드 실행

STEP 5
테스트 실행

STEP 6
FastAPI 실행 확인

STEP 7
URL 입력 API

STEP 8
웹페이지 요청

STEP 9
HTML 수집

STEP 10
링크 수집

STEP 11
하위 페이지 탐색

STEP 12
게시글 / 댓글 탐색

STEP 13
iframe 탐색

STEP 14
iframe 내부 DOM 탐색

STEP 15
nested iframe

STEP 16
DOM 분석 구조

STEP 17
Detection Engine

STEP 18
HOMOGLYPH

STEP 19
JAMO

STEP 20
TRANSPARENT

STEP 21
OFFSCREEN

STEP 22
탐지 결과 병합

STEP 23
CSS Selector

STEP 24
iframe Location

STEP 25
Result Builder

STEP 26
result.json

STEP 27
전체 Pipeline 연결

STEP 28
Frontend

STEP 29
Progress UI

STEP 30
Result UI

STEP 31
Filter

STEP 32
Evidence 표시

STEP 33
JSON Download

STEP 34
Integration Test

STEP 35
정확도 개선

STEP 36
성능 개선

STEP 37
Windows 11 검증

STEP 38
최종 실행 테스트

STEP 39
제출 파일 정리
```

단, 실제 저장소에 이미 구현되어 있는 기능은 먼저 확인하고 **중복 구현하지 않는다.**

---

# 12. STEP 0 — 새 Repository 인수

새 Repository가 만들어지면 가장 먼저 해야 할 일은 코딩이 아니다.

다음을 확인한다.

```text
Repository URL
현재 Branch
Remote
파일 목록
README
문서
소스 코드
테스트
```

VS Code에서 프로젝트 폴더를 연다.

터미널에서:

```bash
git remote -v
```

```bash
git branch -a
```

```bash
git status
```

등으로 상태를 확인한다.

---

# 13. STEP 1 — 프로젝트 구조 조사

처음부터 파일을 만들지 않는다.

먼저 다음을 확인한다.

```text
app/
tests/
schemas/
docs/
scripts/
sources/
```

실제 폴더가 다르다면 현재 구조를 따른다.

AI 코딩 도구는 프로젝트 파일을 먼저 읽고 다음을 보고해야 한다.

```text
현재 구조
이미 구현된 기능
실행 방법
테스트 방법
미구현 기능
문제점
```

---

# 14. STEP 2 — 환경 확인

다음 환경을 확인한다.

```text
Windows
Python
pip
Git
VS Code
브라우저
```

Python 버전을 확인한다.

```bash
python --version
```

Git:

```bash
git --version
```

환경 문제가 있으면 코딩보다 먼저 해결한다.

---

# 15. STEP 3 — 가상환경

프로젝트에 Python 가상환경이 필요하다면 구성한다.

예:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

이후 의존성을 설치한다.

단, 기존 `requirements.txt`가 있다면 먼저 내용을 확인한다.

무조건 새 패키지를 추가하지 않는다.

---

# 16. STEP 4 — 기존 프로젝트 실행

코드를 수정하기 전에 현재 상태를 실행한다.

가능한 경우:

```bash
pytest
```

그리고 애플리케이션 실행 방법을 확인한다.

현재 코드가 실행되지 않는 경우:

```text
원인 조사
 ↓
환경 문제인지
코드 문제인지
설정 문제인지
 ↓
원인 분리
```

부터 한다.

---

# 17. M0/M1 최소 동작 목표

프로젝트 초기 통합 목표는 다음과 같다.

```text
테스트 페이지
 ↓
Crawler
 ↓
OFFSCREEN 탐지
 ↓
정확한 Location
 ↓
result.json
 ↓
UI
```

처음부터 4종 탐지와 전체 인터넷 크롤링을 동시에 완성하지 않는다.

하나의 테스트 페이지를 대상으로 **전체 Pipeline이 한 번 끝까지 연결되는 것**을 우선한다.

---

# 18. Crawler 개발 원칙

Crawler는 다음을 처리한다.

```text
입력 URL
 ↓
페이지 로드
 ↓
DOM 확보
 ↓
링크 추출
 ↓
URL 정규화
 ↓
Queue
 ↓
Visited
 ↓
하위 페이지
```

추가:

```text
게시글
댓글
iframe
nested iframe
```

---

# 19. Crawler 안전장치

Crawler가 무한히 웹사이트를 탐색하지 않도록 제한을 둔다.

예:

```text
MAX_DEPTH
MAX_URLS
PAGE_TIMEOUT
TOTAL_TIMEOUT
MAX_IFRAME_DEPTH
```

값은 실제 테스트를 통해 결정한다.

30분 공모전 제한을 고려하되, 개발 초기에는 작은 값으로 테스트한다.

---

# 20. iframe 처리

iframe은 별도의 분석 대상으로 취급한다.

```text
Main Page
 └── iframe
       └── iframe 내부 DOM
```

nested iframe:

```text
Main
 └── iframe A
       └── iframe B
             └── Element
```

접근 실패가 발생해도 전체 탐색을 중단하지 않는다.

---

# 21. Detection Engine

Detection Engine은 4개의 독립적인 Detector를 가진다.

```text
Detection Engine
├── HOMOGLYPH
├── JAMO
├── TRANSPARENT
└── OFFSCREEN
```

각 Detector는 가능한 한 독립적으로 테스트한다.

---

# 22. HOMOGLYPH 개발 원칙

문자열을 그대로 비교하지 않는다.

검토:

```text
Unicode
Code Point
Normalization
유사 문자
정상 문자
```

Detector의 결과는 단순 Boolean이 아니라 나중에 Result Builder가 사용할 수 있는 정보를 제공하도록 설계한다.

---

# 23. JAMO 개발 원칙

검토:

```text
한글 음절
초성
중성
종성
자모 분리
Normalization
```

정상적인 한글 문자열까지 오탐하지 않도록 테스트한다.

---

# 24. TRANSPARENT 개발 원칙

검토:

```text
text
CSS
computed style
visibility
opacity
color
background
```

다음과 같은 단일 조건을 발견했다고 무조건 불법광고로 판정하지 않는다.

```text
opacity: 0
```

실제 텍스트와 화면 표시 상태 등을 함께 검토한다.

---

# 25. OFFSCREEN 개발 원칙

Element의:

```text
position
left
right
top
width
height
display
visibility
font-size
```

등을 검토한다.

공모전에서 제시한 OFFSCREEN 예시와 실제 테스트 페이지를 기준으로 조건을 검증한다.

---

# 26. False Positive / False Negative

탐지율만 높이는 방향으로 개발하지 않는다.

반드시:

```text
정상 페이지
정상 텍스트
정상 CSS
정상 iframe
```

도 테스트한다.

사용자가 정의한 정상/비정상 사례를 사용하고 정답 기준·재현 입력을 기록한다.

---

# 27. Detection Result

내부 결과는 최소한 다음 정보를 가져야 한다.

```text
url
is_violation
element
location
evidence_text
technique
```

동일한:

```text
URL + Location + Technique
```

은 중복 제거한다.

단, 하나의 Element가 여러 Technique에 해당하면 각각 별도 Finding을 생성한다.

---

# 28. Location 개발 원칙

탐지보다 Location이 중요할 수 있다는 점을 항상 기억한다.

Detector가:

```text
Element
```

를 찾으면 Location Generator가:

```text
CSS Selector
```

를 생성한다.

Selector는 실제 DOM에서 해당 Element를 다시 찾을 수 있어야 한다.

---

# 29. iframe Location

URL 의미·selector·프레임 경계·중복 기준은 [wiki.md](wiki.md)의 6절을 따른다. PDF는 절대 src 표기를 안내하되 같은 요소를 정확히 가리키는 다른 선택자도 인정한다. 현재 DOM 기반 선택자는 실제 속성과 일치하게 유지하고 프레임 요소를 하나로 재식별하는지 검증한다. URL::selector는 폐기한 과거 형식이며 현재 location은 URL 접두사 없는 selector 경로다.

---

# 30. Result Builder

Detection Result를 공모전 출력 형식으로 변환한다.

```text
Detection Result
 ↓
Validation
 ↓
Duplicate Removal
 ↓
Schema Mapping
 ↓
result.json
```

Result Builder는 Detection Engine과 분리한다.

---

# 31. result.json

필드·자료형·빈 findings·인코딩·판정 정책은 [wiki.md](wiki.md)의 5~7절을 따른다. PDF 표/예시에 따라 meta.topic=TOPIC, 정규화 전 근거 원문, 필수 4종 result.json 및 추가 유형 result_extra.json을 구분한다. 화면 설명을 원문 필드에 섞지 않는다. PDF 기반 계약 테스트 통과와 주최 측 실제 채점 통과를 구분한다.

---

# 32. JSON Schema 검증

결과를 생성한 후 반드시 Schema를 검증한다.

```text
Detection
 ↓
Result Builder
 ↓
JSON 생성
 ↓
Schema Validation
 ↓
성공
```

Schema 오류가 있으면 다음 기능으로 넘어가지 않는다.

---

# 33. Frontend

Frontend는 다음 역할만 담당한다.

```text
URL 입력
탐지 시작
진행 상태
결과 표시
필터
Evidence
JSON Download
```

Frontend에 Crawler나 Detection Logic을 넣지 않는다.

---

# 34. Backend API

현재 복구 대상은 GET /api/health와 POST /api/analyze이다. 요청·응답·UI 연결은 [wiki.md](wiki.md)의 8절을 따른다. 기존 /api/detection 기반 Job·상태·결과·다운로드 경로는 향후 제안이며 현재 API가 아니다. 필요성 검토 없이 강제 전환하지 않는다. 실행 명령·기본 포트는 README를 참조한다.

---

# 35. API와 Frontend 연결

최종 흐름:

```text
Frontend
 ↓
POST
 ↓
Backend
 ↓
Crawler
 ↓
Detection
 ↓
Result
 ↓
API
 ↓
Frontend
```

Frontend가 직접 파일이나 내부 Python 모듈을 호출하지 않는다.

---

# 36. 진행 상태

가능하다면:

```text
queued
running
completed
failed
timeout
```

상태를 제공한다.

단, 진행 상태 기능 때문에 핵심 탐지 기능 개발이 지연된다면 우선순위를 낮춘다.

---

# 37. 탐지 기준과 검증 업무

사용자가 구현과 분석을 모두 담당한다. 코딩 에이전트는 유형별 조건·정상/경계 사례·예상 오탐/미탐·개선 비교를 준비하고, 정책이 필요한 광고 판정 기준은 근거와 함께 사용자에게 제시한다. 확정 전에는 합성 데이터의 기술적 특징 검증과 실제 광고 판정 정확도를 구분한다.

---

# 38. 테스트 산출물

테스트 HTML과 JSON 정답 목록에 원본 요소·유형·선정 근거를 기록한다. 현재 정적 특징 사례는 tests/fixtures/detection/에 있고 위치·크롤러·통합 테스트는 tests/에서 관리한다. 새로운 사례의 예상 결과를 먼저 정하고 수정 전 실패와 수정 후 결과를 비교한다.

---

# 39. 테스트 우선 개발

새 기능을 구현하면 최소한 하나의 테스트를 추가한다.

예:

```text
OFFSCREEN Detector 구현
 ↓
OFFSCREEN 정상 사례
 ↓
OFFSCREEN 탐지 사례
 ↓
pytest
 ↓
통과
```

테스트 없이 여러 기능을 한꺼번에 구현하지 않는다.

---

# 40. Git Commit 원칙

기능 하나가 정상 동작하면 commit한다.

예:

```bash
git add .
git commit -m "feat: add offscreen detector"
```

또는:

```bash
git commit -m "test: add offscreen detection cases"
```

Commit은 의미 있는 단위로 만든다.

---

# 41. Git 작업 시 주의사항

AI 코딩 도구가 다음 명령을 실행하려고 하면 먼저 사용자에게 설명한다.

```text
git reset --hard
git clean
git push --force
파일 전체 삭제
대규모 파일 덮어쓰기
```

특히 기존 작업을 삭제할 가능성이 있는 명령은 사용자 확인 없이 실행하지 않는다.

---

# 42. AI가 코드를 수정할 때 지켜야 할 원칙

코드를 수정하기 전에:

```text
현재 코드 읽기
 ↓
수정 이유 확인
 ↓
영향 범위 확인
 ↓
최소 수정
 ↓
테스트
```

를 따른다.

작동 중인 기능을 이유 없이 리팩터링하지 않는다.

---

# 43. 오류 발생 시 대응

오류가 발생하면 새로운 코드를 무작정 생성하지 않는다.

먼저:

```text
Error Message
 ↓
Stack Trace
 ↓
발생 파일
 ↓
발생 함수
 ↓
입력값
 ↓
환경
```

을 확인한다.

그 다음 최소 수정한다.

---

# 44. 네트워크 오류

Crawler에서:

- DNS 오류
- Connection Timeout
- HTTP 오류
- SSL 오류
- robots 관련 문제
- JavaScript 렌더링 문제
- iframe 접근 실패

등이 발생할 수 있다.

개별 페이지 실패가 전체 프로그램 실패로 이어지지 않도록 설계한다.

---

# 45. 30분 제한

최종 평가에서는 30분 제한을 고려한다.

따라서:

```text
무제한 URL 탐색
무제한 iframe
무제한 DOM
```

을 허용하지 않는다.

다음 요소를 관리한다.

```text
Depth
URL Count
Page Timeout
Total Timeout
Iframe Depth
```

---

# 46. Windows 11

최종 검증은 Windows 11 환경에서 수행한다.

최종 개발이 완료되면:

```text
Windows 11
 ↓
프로그램 실행
 ↓
URL 입력
 ↓
탐지
 ↓
result.json
 ↓
UI
```

전체 흐름을 검증한다.

다른 OS에서 정상 실행된다는 것만으로 Windows 실행을 완료했다고 판단하지 않는다.

---

# 47. Optional 기능 판단 기준

다음 기능은 핵심 기능 완료 후에만 검토한다.

```text
추가 탐지
RAG
LLM
LangChain
LangGraph
DB
고급 UI
```

Optional 기능을 추가하기 전에 반드시 질문한다.

```text
이 기능이 공모전 점수에 실질적으로 도움이 되는가?
현재 핵심 기능보다 우선인가?
개발 시간을 감수할 가치가 있는가?
Windows 환경에서 안정적으로 실행되는가?
```

하나라도 불확실하면 핵심 기능을 우선한다.

---

# 48. AI Coding Agent의 행동 규칙

너는 다음 행동을 하지 않는다.

### 금지 1

프로젝트 전체 코드를 한 번에 생성하지 않는다.

### 금지 2

현재 코드를 읽지 않고 파일을 수정하지 않는다.

### 금지 3

공모전 요구사항을 추측하지 않는다.

### 금지 4

확정되지 않은 기술을 확정된 것처럼 말하지 않는다.

### 금지 5

오류가 났다고 프로젝트 전체를 다시 만든다.

### 금지 6

승인 범위를 넘어 다음 단계로 진행하지 않는다. 미리 승인된 연속 작업은 각 작업의 자동 검증 후 이어갈 수 있다.

### 금지 7

기존 코드를 이유 없이 대규모로 리팩터링하지 않는다.

### 금지 8

필수 기능보다 Optional 기능을 먼저 개발하지 않는다.

---

# 49. 각 단계의 완료 기준

관련 요구사항 통과 기준에 맞춰 실행·예상 결과·회귀 검증을 수행한다. 상태는 project.md의 미구현 / 구현됨·검증 전 / 검증 통과 / 문제 확인을 사용한다. Git commit 여부는 별도 기록한다. 현재 Git 저장소로 인식되지 않는 상태와 기능 검증을 혼동하지 않는다. Git 초기화·원격 지정은 실제 저장소 정보를 확인한 뒤 별도 작업으로 처리한다.

---

# 50. 개발 단계 보고 형식

각 단계가 끝나면 다음 형식으로 보고한다.

```text
[STEP 완료 보고]

1. 구현한 기능:
2. 수정한 파일:
3. 실행한 명령:
4. 실행 결과:
5. 테스트 결과:
6. 발생한 오류:
7. 현재 남은 문제:
8. Git Commit:
9. 다음 단계:
```

---

# 51. 최종 개발 목표

최종적으로 다음 Pipeline이 실제로 동작해야 한다.

```text
사용자
 ↓
URL 입력
 ↓
Frontend
 ↓
FastAPI
 ↓
Crawler
 ↓
하위 페이지 / 게시글 / 댓글
 ↓
iframe / nested iframe
 ↓
DOM
 ↓
Detection Engine
 ├── HOMOGLYPH
 ├── JAMO
 ├── TRANSPARENT
 └── OFFSCREEN
 ↓
Location
 ↓
Result Builder
 ↓
result.json
 ↓
Frontend
 ↓
사용자 결과 확인
```

---

# 52. 최종 성공 조건

다음 조건을 모두 만족해야 프로젝트의 핵심 기능이 완료된 것으로 판단한다.

```text
[ ] URL 입력 가능
[ ] 웹사이트 탐색 가능
[ ] 하위 페이지 탐색 가능
[ ] 게시글 탐색 가능
[ ] 댓글 영역 탐색 가능
[ ] iframe 탐색 가능
[ ] nested iframe 처리 가능
[ ] HOMOGLYPH 탐지
[ ] JAMO 탐지
[ ] TRANSPARENT 탐지
[ ] OFFSCREEN 탐지
[ ] 정확한 Location 생성
[ ] iframe Location 생성
[ ] 중복 Detection 제거
[ ] result.json 생성
[ ] JSON Schema 검증
[ ] 결과 UI 표시
[ ] JSON 다운로드
[ ] 정상 사례 테스트
[ ] 탐지 사례 테스트
[ ] False Positive 검증
[ ] False Negative 검증
[ ] Windows 11 실행 검증
[ ] 30분 제한 검증
```

---

# 53. AI Service Developer에게 필요한 개발 원칙

나는 개발 초보에 가까운 상태에서 이 프로젝트를 AI 코딩 도구와 함께 개발한다.

따라서 코드를 생성하는 것만 목표로 하지 않는다.

각 기능을 구현할 때 최소한 다음 정도는 이해할 수 있도록 설명한다.

```text
이 코드가 무엇을 하는가?
왜 필요한가?
어떤 데이터가 들어가는가?
어떤 데이터가 나오는가?
어디에서 호출되는가?
오류가 나면 어디를 확인하는가?
```

단, 프로젝트 진행을 방해할 정도로 이론을 장황하게 설명하지 않는다.

**현재 구현에 필요한 개념만 설명한다.**

---

# 54. 가장 중요한 개발 원칙

> **작동하는 작은 시스템을 먼저 만들고, 그 위에 기능을 하나씩 추가한다.**

```text
작은 기능
 ↓
실행
 ↓
검증
 ↓
Commit
 ↓
다음 기능
```

처음부터 완벽한 시스템을 만들려고 하지 않는다.

---

# 55. 시작 시 AI가 해야 할 일

이 프롬프트를 처음 전달받으면 바로 코딩하지 않는다.

먼저 현재 프로젝트 폴더를 조사한다.

다음 정보를 확인한다.

```text
1. 현재 프로젝트 경로
2. Git 상태
3. Branch
4. 파일 구조
5. README
6. WIKI
7. 개발 명세
8. requirements
9. 기존 app 코드
10. 기존 tests
11. 실행 방법
```

그리고 다음 형식으로만 먼저 보고한다.

```text
[프로젝트 인수 결과]

Repository:
Branch:

현재 구조:

이미 구현된 기능:

실행 가능한 기능:

테스트 상태:

미구현 기능:

문서와 코드의 불일치:

공모전 요구사항과의 불일치:

가장 먼저 해야 할 작업:

```

**이 보고 뒤 사용자가 승인한 구현 범위로 진행한다. 연속 작업을 이미 승인했다면 같은 확인을 반복하지 않는다.**

---

# 56. 첫 번째 실제 개발 목표

최초 구현은 다음 목표를 기준으로 한다.

```text
테스트 페이지 1개
        ↓
Crawler
        ↓
OFFSCREEN 1건 탐지
        ↓
정확한 Location
        ↓
result.json
        ↓
UI 표시
```

이 흐름이 성공한 후 다음 탐지 유형으로 확장한다.

```text
OFFSCREEN
 ↓
HOMOGLYPH
 ↓
JAMO
 ↓
TRANSPARENT
```

단, 실제 프로젝트 상태를 확인한 후 이미 구현된 기능은 다시 만들지 않는다.

---

# 57. 마지막 원칙

이 프로젝트의 목표는 **코드의 양이 아니다.**

목표는:

```text
실제로 실행된다.
        +
공모전 요구사항을 만족한다.
        +
필수 4종을 탐지한다.
        +
정확한 위치를 제공한다.
        +
result.json이 정상이다.
        +
Windows에서 실행된다.
```

이다.

따라서 AI 코딩 에이전트는 새로운 기술을 많이 추가하는 것보다 **현재 기능을 실제로 실행하고 검증하는 것**을 우선한다.
