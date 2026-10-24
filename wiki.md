# 공공 웹사이트 불법광고 탐지 도구 — 설계·규격

## 1. 문서 역할과 목표

공통 목표는 URL에서 시작해 하위 페이지·게시글·댓글·iframe·중첩 iframe을 탐색하고 HOMOGLYPH·JAMO·TRANSPARENT·OFFSCREEN을 탐지하여 정확한 위치·근거·result.json·결과 UI를 제공하는 것입니다.

이 문서는 목표 설계이며 현재 구현 완료를 뜻하지 않습니다. 공모전 공식 모집요강·출력 스키마는 원문 대조 전입니다. 기존 문서의 평가·제출 조건은 요구사항정의서의 NFR로 관리하고 원문 확보 후 우선 적용합니다.

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

현재 기술은 Python·FastAPI·Uvicorn·httpx·BeautifulSoup4·html5lib·HTML/JavaScript입니다. 수집과 탐지는 HTML5 파서로 동일한 DOM을 구성해 암시적 tbody 등 브라우저의 구조 보정을 반영합니다. 검증에는 Playwright와 설치된 Edge를 사용하며 제품의 동적 수집 도구는 미확정입니다. 특정 프레임워크는 팀의 선택이며 공모전 지정 기술이 아닙니다.

현재 파일 배치는 다음과 같습니다. 파일 존재와 정상 동작은 구분합니다.

```text
backend/app/
  __init__.py
  main.py          # API·저장·화면 연결
  crawler.py       # 정적 HTTP 수집·링크·iframe 탐색
  detection.py     # 탐지 로직
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

일반 링크와 프레임 문서를 구분합니다. 현재 top_url·parent_url·frame_path를 보존하며 같은 iframe URL도 삽입 위치마다 별도 컨텍스트로 처리합니다. 성공/실패 응답은 실행 중 URL별 캐시로 재사용합니다. 상대 src와 정적 srcdoc을 처리하고 순환·깊이 초과·외부/미지원 src를 기록합니다. srcdoc의 링크 기준은 부모 문서 URL입니다. HTML base 요소·동적 프레임·about:blank의 런타임 DOM은 미지원입니다.

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

HTML에 존재하는 게시글·댓글과 JS 실행·추가 요청이 필요한 콘텐츠를 구분해 검증합니다. 정적 HTTP 수집만으로 동적 콘텐츠 지원을 보장하지 않습니다. 개별 프레임 실패가 전체 탐색을 중단시키지 않게 하되 전체 수집 실패는 정상 0건과 구분합니다.

## 5. 탐지 기준

4종은 독립적으로 판정하고 결과를 통합합니다. 같은 요소의 복수 기법은 기법별 finding으로, 같은 유형의 서로 다른 요소도 각각 보존합니다.

| 유형 | 분석 대상 | 정상·경계 사례 |
|---|---|---|
| HOMOGLYPH | Unicode·code point·정규화·유사 문자 위장 | 정상 외국어·전각 문자 |
| JAMO | 음절·초중종성·분리 자모·정규화 | 정상 자모·초성 표현 |
| TRANSPARENT | 텍스트·색상·opacity·배경·상속·computed style | 숨김 UI·접근성 텍스트 |
| OFFSCREEN | 위치·크기·font-size·display·layout·표시 상태 | 정상 absolute·overflow·접근성 텍스트 |

기존 문서는 font-size 0~1px, left:-9999px, display:none을 OFFSCREEN 예시로 인계했습니다. 공식 분류와 대조하고 TRANSPARENT와 겹치는 조건은 사용자가 정답 사례로 기준을 정합니다. 겹치는 속성만으로 두 유형을 모두 확정하지 않습니다.

위장·은닉 특징 발견과 불법광고 위반 판정은 구분합니다. 실제 텍스트·맥락·정답 기준을 함께 검토하며 CSS 속성 하나로 is_violation=true를 확정하지 않습니다. 광고 판정 조건·키워드·임계값·정확도 목표는 사용자의 기준 확정 전입니다. 고정 confidence를 측정 정확도로 설명하지 않습니다.

근거는 원문 텍스트·의심 문자·스타일·판정 이유를 가능한 한 포함합니다. 내부 분석 정보와 제출 필드는 Result Builder에서 명시적으로 변환합니다.

현재 정적 탐지에서는 직접 텍스트를 가진 요소를 대상으로 하고 script·style·head·template·noscript·주석·속성 문자열은 텍스트 판정에서 제외합니다. 유형별 첫 일치에서 멈추지 않고 모든 일치를 반환합니다. 근거에 해당 요소의 원문을 포함합니다.

단순 inline 선언의 중복·!important 우선순위를 처리하며 opacity는 정확히 0인 경우와 조상 opacity:0을 확인합니다. 클래스 이름만으로 투명 여부를 판정하지 않습니다. OFFSCREEN 후보는 display:none, 0~1px 글꼴, absolute/fixed와 음수 left/top(px) 조합입니다. 단독 absolute·overflow:hidden은 제외합니다. 음수 좌표의 실제 화면 이탈 여부와 유형 분류는 추가 검증이 필요합니다.

스타일시트·computed style·전체 상속·조상 display:none 전파·뷰포트 계산·노드 간 문자 조합은 아직 지원 범위로 검증하지 않았습니다. 사례·정답·한계는 [테스트 사례 설명](tests/fixtures/detection/README.md)에 기록합니다. 이는 개발자 합성 데이터의 특징 검증이며 광고 여부를 확정한 정답이 아닙니다.

## 6. URL·location 규격

다음은 팀의 목표 규격이며 공식 출력 규격 대조 전입니다.

- url: 일반 요소는 분석 페이지 URL. iframe 결과는 프레임 경로를 다시 따라갈 수 있는 최상위 페이지 URL을 기준으로 합니다. 내부 프레임 URL은 별도 내부 정보로 보존합니다.
- location: 해당 url에서 시작하는 CSS selector 경로. URL 접두사를 붙이지 않습니다.
- iframe 경계는 `>>>`로 구분합니다. 이는 경로 표기이며 표준 CSS selector 하나가 아닙니다. 각 문서에서 selector를 따로 평가합니다.

```text
일반: div.notice-board > span.visually-hidden
반복 요소: table > tbody > tr:nth-of-type(7) > td:nth-of-type(2)
iframe: iframe#widget >>> div.wrap > span.hidden-link
중첩: iframe#outer >>> iframe#inner >>> span.ad
```

각 selector는 해당 문서에서 대상 하나를 식별해야 합니다. 특수문자 escaping·중복 ID·반복 요소를 검증합니다. iframe src를 쓰면 원본 DOM 속성값에 맞추며 상대 src를 임의의 절대 URL로 바꾼 selector를 만들지 않습니다.

기존 `URL::selector`는 폐기한 과거 형식입니다. 현재 일반 요소는 selector, 프레임 요소는 frame_path와 내부 selector를 ` >>> `로 연결한 location을 사용합니다. API·JSON 중복 제거는 location을 기준으로 하며 공식 규격이 다르면 이 절부터 갱신합니다.

Detection Unit은 `(url + location + technique)`입니다. 같은 조합은 중복 제거하고 서로 다른 요소·프레임 삽입 위치·기법은 유지합니다.

## 7. 결과 규격

다음은 기존 팀 문서를 통합한 목표 출력입니다. 공식 JSON Schema 원본은 아직 확인하지 않았습니다.

```json
{
  "meta": {
    "topic": "illegal-ad-detection",
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
      "evidence_text": "광고 원문과 은닉 스타일 등 판정 근거",
      "technique": "OFFSCREEN"
    }
  ]
}
```

| 필드 | 자료형·의미 |
|---|---|
| meta.topic | 문자열, 분석 주제 |
| meta.entry_url | 문자열, 시작 URL |
| meta.started_at / finished_at | 시간대 포함 ISO 8601 문자열 |
| meta.elapsed_sec | 0 이상 숫자, 실행 경과 시간 |
| meta.tool_version | 선택 문자열 |
| findings | 배열, 정상 분석 후 0건이면 빈 배열 |
| finding.id | 결과 안에서 고유한 문자열 |
| finding.url / location | 문자열, 6절의 페이지·요소 경로 |
| finding.is_violation | Boolean, 정의한 기준에 따른 위반 여부 |
| finding.evidence_text | 문자열, 검출 근거 |
| finding.technique | HOMOGLYPH / JAMO / TRANSPARENT / OFFSCREEN |

is_violation=false 포함 여부와 의심 사례 표현은 공식 규격·분석 기준 대조 후 확정합니다. 기존 테스트가 true를 기대한다는 사실만으로 판정 정책이 확정된 것은 아닙니다.

실행 흐름 복구 단계의 Result Builder는 기존 계약을 유지해 내부 판정값이 없으면 true로 변환하고, 명시적 Boolean 판정은 보존합니다. 이는 임시 호환 동작이며 광고 판정 정확도가 검증됐다는 뜻이 아닙니다. location은 6절의 경로 형식으로 전환했습니다. 광고 판정 정책은 추가 검증이 필요합니다.

필수 필드·자료형·허용 기법·ID·중복·시간·빈 배열을 검증합니다. 파일은 UTF-8 BOM 없이 저장하고 JSON으로 다시 읽을 수 있어야 합니다. 기본 위치는 프로젝트 루트 result.json이며 동시 요청 저장 정책은 추후 검토합니다. 추가 유형은 필요할 때 ETC·extra_finding·result_extra.json의 형식을 별도로 결정합니다.

## 8. API와 UI

현재 복구 대상으로 유지할 경로입니다. 정상 실행 여부는 project.md에서 관리합니다.

| 경로 | 역할 |
|---|---|
| GET / | UI 제공 |
| GET /api/health | 서버 생존 확인 |
| POST /api/analyze | URL 분석·결과 반환 |

요청의 필수값은 `{"url": "https://example.com"}`입니다. 선택값 max_depth는 0~20 정수(기본 2), total_timeout_sec는 0 초과~1800 이하 유한 숫자(기본 60)입니다. 이 상한은 API의 개발 기준이며 공모전 요구값이 아닙니다. 잘못된 한도 입력은 HTTP 422로 거부합니다. 현재 응답 모델은 url, page_title, crawled_pages, findings, result_json, warnings이며 API finding은 technique, selector, location, url, evidence, confidence를 갖습니다. 제출용 finding과는 다릅니다. evidence → evidence_text 등의 변환은 Result Builder가 맡으며 변경 시 모델·UI를 함께 수정합니다.

crawled_pages는 수집 성공한 문서 URL의 중복 없는 목록입니다. srcdoc과 동일 URL의 여러 프레임은 위치별 finding으로 구분됩니다. 전체 수집 실패는 HTTP 502로 반환하고 기존 결과 파일을 덮어쓰지 않습니다. 일부 실패·프레임 제외·컨텍스트 한도 도달은 warnings로 반환하며 UI에도 표시합니다. warnings는 API 안내 필드이고 제출 JSON에 추가하지 않습니다. 따라서 파일만으로 분석 범위 완전성을 확인하는 정책은 추후 검토합니다.

링크 깊이·시간 제한도 warnings로 안내합니다. 수집·탐지 중 시간 초과로 분석을 끝낸 페이지가 하나도 없으면 HTTP 504이고 기존 파일을 보존합니다. 완료한 페이지가 있으면 그 결과를 반환하되 나머지 미분석을 명시합니다. 분석 도중 중단된 페이지의 중간 finding은 포함하지 않습니다. crawled_pages는 수집 성공 목록이며 모든 문서의 탐지 완료를 뜻하지 않습니다.

포트와 실행 명령은 README를 따릅니다. UI는 같은 서버의 `/api/analyze`를 상대 경로로 호출합니다.

UI 목표는 URL 입력·실행·상태 안내·전체/유형별 건수·URL·location·근거·필터·JSON 다운로드입니다. 응답 원본을 보존해 필터링합니다. Frontend에 수집·탐지 로직을 넣지 않습니다.

Job 기반 `/api/detection`, `/api/detection/{id}`, `/api/detection/{id}/status`, `/api/detection/{id}/result`, `/api/detection/{id}/download`는 이전 문서의 향후 제안이며 도입 미확정입니다. 현재 API가 아닙니다. queued/running/completed/failed/timeout은 목표 상태 의미이며 기본 안내가 반드시 상태 API를 요구하지는 않습니다.

## 9. 검증·변경 원칙

요구사항 ID에 대응하는 정답 사례로 검증합니다.

- 수집: URL·중복·실패·시간·한도·프레임 관계·동적 콘텐츠.
- 탐지: 유형별 정상·탐지·경계 사례, 복수 요소·기법, 오탐·미탐.
- 위치: 실제 원본 요소 재식별, selector 고유성, 중첩 iframe, 동일 src 복수 삽입.
- 결과: 필드·자료형·중복·빈 결과·실패 구분·UTF-8 BOM 없음.
- 통합/UI: URL부터 파일·화면·필터 전체 복귀·다운로드 일치.
- 평가: 요구사항정의서 NFR의 원문 대조와 실제 대상 환경 검증.

작은 기능 → 실행 → 예상 결과·회귀 확인 → 진행 기록 갱신 순으로 개발합니다. 기존 코드를 검토 없이 삭제하거나 프로젝트 전체를 재생성하지 않습니다. Git 기록 여부와 기능 검증은 구분합니다.

## 10. 미확정 사항·선택 기능

공식 원문·출력 스키마, 판정 기준·정확도 목표, 동적 렌더링 도구, 호스트/iframe 정책, 탐색 한도, Python 버전, 실행 파일·배포 방식은 추가 확인이 필요합니다.

추가 탐지·RAG·LLM·LangChain·LangGraph·DB·이력·고급 UI는 핵심 안정화 이후 검토합니다. 필요성이 확인되지 않은 기술을 먼저 도입하지 않습니다.
