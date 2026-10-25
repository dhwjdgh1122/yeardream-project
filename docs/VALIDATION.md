# 저장본 검수·일괄 평가 기록

## 2026-10-25 실제 내용 판별 회귀 검수

이 검수는 **단일 교육청 도메인의 정적 HTML 7개에서 제목/본문 × 두 범주 28개 항목**만 대상으로 합니다. 개발 중 이미 사용한 사례를 포함하고, 발견한 미탐을 수정하는 데도 사용했으므로 독립 성능평가가 아닙니다. Codex가 저장 원문을 읽고 내용 존재 여부를 표시했으며 사용자의 법적 위반 확정 판단을 대신하지 않습니다. 전체 페이지·사이트·동적 내용·첨부 파일을 검수한 것도 아닙니다.

| 저장본 | 검수한 제목/본문의 내용 | v4 → v5 |
|---|---|---|
| [107](https://gen.go.kr/child/xboard/board.php?mode=view&number=107&tbnum=6) | 도박 관련 커뮤니티·가입 혜택 홍보 | 검출 유지 |
| [151](https://gen.go.kr/child/xboard/board.php?mode=view&number=151&tbnum=6) | 성인물 서비스 검색·시청 유도 | 검출 유지 |
| [150](https://gen.go.kr/child/xboard/board.php?mode=view&number=150&tbnum=6) | 자막 성인물 서비스 검색·무료 감상 유도 | 검출 유지 |
| [148](https://gen.go.kr/child/xboard/board.php?mode=view&number=148&tbnum=6) | 특정 검증 커뮤니티·제휴 베팅 업체 홍보 | 제목/본문 미탐 2개 → 검출 |
| [141](https://gen.go.kr/child/xboard/board.php?mode=view&number=141&tbnum=6) | 토토 커뮤니티 추천·가입 유도 | 검출 유지 |
| [454470](https://gen.go.kr/xboard/board.php?mode=view&number=454470&tbnum=520) | 학교 예방교육용 경찰청 영상 안내 | 두 범주 정상 유지 |
| [453891](https://gen.go.kr/xboard/board.php?mode=view&number=453891&tbnum=520) | 학교폭력 실태조사 결과 안내 | 두 범주 정상 유지 |

검수한 항목의 다른 범주도 음성으로 확인했습니다. 예를 들어 도박 홍보 제목/본문에 성인물 홍보가 없는지 별도로 표시했습니다. 양성은 특정 도박/성인물 서비스의 추천·검색·접속·가입·시청 유도이며, 예방교육·조사 결과 안내는 음성입니다. 특징 검출·제출 정책·법적 위반 여부의 정답과 혼용하지 않습니다.

| 개발용 검수 범위 28항목 | TP | FP | FN | TN |
|---|---:|---:|---:|---:|
| content-rules-v4 | 8 | 0 | 2 | 18 |
| content-rules-v5 | 10 | 0 | 0 | 18 |

v5는 같은 문장/근접 범위의 주제와 ‘구글검색’ 유도도 연결합니다. 검색 금지·하지 말라는 안내와 기존 예방/차단/보도 문맥은 제외하도록 보완하고 합성 반대 사례를 확인했습니다. 모든 일반 검색·인용 문맥을 해결한 것은 아닙니다.

**위 표의 FP 0은 검수한 28항목에 한정됩니다.** v5에서 함께 검출된 게시물 목록 후보 40개는 미검수이며 FP/TP로 단정하지 않습니다. 따라서 두 보고서 모두 complete=false, 전체 precision/recall/F1은 null입니다. 미검토 후보를 오탐으로 바꾸거나 검수되지 않은 페이지를 정상으로 세지 않습니다. 7개 저장본의 4종 제출 후보는 모두 0개이며 일반 표시 홍보에 임의 기법을 부여하지 않습니다.

원본 캡처/이전 검토를 수정하지 않고 `.validation/real-content-review-20261025-01/cases`에 사본과 새 정답을 만들었습니다. manifest.json은 capture/정답 SHA-256에 연결하며 report-v4.json과 report-v5.json을 각각 보존합니다. 실제 HTML·정답·상세 보고서는 Git에서 제외합니다. 새 수집 4개와 이전 수집 3개를 사용했으며 수집의 링크/프레임 제외 경고도 보고서에 포함합니다.

## 재현 명령

현재 PC의 저장 자료가 있으면 소스 환경에서 실행합니다. 실행 파일에는 이 평가 CLI를 포함하지 않습니다.

```powershell
.venv\Scripts\python.exe -B scripts/evaluate_suite.py .validation/real-content-review-20261025-01/manifest.json --output .validation/real-content-review-20261025-01/report-next.json
```

출력은 반드시 새 경로여야 합니다. 과거 보고서 파일을 갱신하지 않습니다. 코드 수정 후 같은 입력으로 새 보고서를 만들어 비교합니다. v4 보고서는 당시 코드를 실행해 보존한 기준선이며 현재 명령을 실행하면 현재 코드의 결과가 나옵니다. manifest 자체/평가 코드와 케이스별 탐지 코드 해시도 기록합니다.

다른 데이터셋을 만들 때는 README의 capture/정답 검수 절차로 저장본을 준비하고, suite JSON을 작성합니다. 각 directory는 manifest가 있는 폴더 안의 상대 경로여야 합니다. kind는 content 또는 feature, dataset_type은 real_saved_pages 또는 synthetic입니다. dataset_type은 작성자의 분류이지 실제 데이터나 독립성 인증이 아닙니다. scope에 수집/검수 범위·제약을 적고 cases에 id/directory/capture_sha256/labels_sha256을 지정합니다. labels 해시는 content이면 content-labels.json, feature이면 labels.json 파일의 실제 바이트 SHA-256입니다.

중복 ID/폴더·같은 페이지의 반복 수집/동등 URL·다른 케이스와 겹치는 페이지는 거부해 건수를 부풀리지 않습니다. 서로 다른 게시물 화면에 반복되는 목록은 별도 요소로 남으므로 데이터 다양성이 높아진 것으로 해석하지 않습니다. 입력 해시·HTML 해시·경로·선택자 검증도 적용합니다. 모든 저장 페이지의 해당 정답을 완전히 검수한 경우에만 complete=true를 쓰고, 일부 케이스라도 부분 검수면 집계 지표는 null로 유지합니다.

다음 검증은 미검수 목록 후보와 독립적인 다른 도메인/표현·4종 은닉 사례를 늘리고 별도 Windows PC에서 실행하는 것입니다. 이 기록으로 실제 사이트 전체 정확도나 공모전 통과를 주장하지 않습니다.
