# Windows 빌드·검증 설명서

대상: Windows 11 x64, CPython 3.14.6 x64. 다른 OS에서 Windows 실행 파일을 교차 빌드하지 않습니다. PyInstaller의 onedir 배포를 사용하며 `_internal` 전체를 함께 배포합니다.

## 소스에서 실행

저장소 전체 소스를 준비하고 프로젝트 루트에서 실행합니다.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements-build.txt
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -B run_app.py
```

개발 테스트도 실행하려면 requirements-dev.txt를 추가 설치합니다. 빌드 도구는 requirements-build.txt에서 고정하고 실행 의존성은 기존 constraints를 공유합니다. source 실행의 결과는 프로젝트 루트, frozen 실행의 결과는 exe 옆에 저장합니다. frontend HTML과 rendered_snapshot.js는 번들 내부의 읽기 전용 리소스로 취급합니다.

## 빌드

```powershell
.venv\Scripts\python.exe -B scripts/build_windows.py --output dist/release-01
```

새 출력 경로를 지정합니다. 이전 출력 경로는 덮어쓰지 않습니다. 실행 프로그램은 `dist/release-01/YearDream/YearDream.exe`, 전달할 압축 파일은 `dist/release-01/YearDream-windows-x64.zip`입니다. work/spec 폴더는 빌드 진단용이며 전달 ZIP에 포함되지 않습니다. ZIP에는 두 설명서와 build-manifest.json이 포함됩니다. 매니페스트는 빌드 시각·패키지 버전·소스/배포 파일 해시를 기록하며 테스트 성공 인증서는 아닙니다. 빌드는 비트 단위 재현성을 보장하지 않습니다. 실패 시 같은 경로를 재사용하지 말고 진단 로그를 확인한 뒤 새 경로로 실행합니다.

Playwright 드라이버를 포함하되 브라우저 엔진을 내려받지 않으며 대상 PC의 Microsoft Edge를 실행합니다. Python·가상환경·테스트·실제 수집 HTML·기존 result.json은 전달 패키지에 포함하지 않습니다. 실행 파일은 코드 서명되지 않았습니다.

## 패키지 검증

Microsoft Edge와 requirements-dev 환경이 있는 빌드 PC에서 실행합니다.

```powershell
.venv\Scripts\python.exe -B scripts/test_packaged.py dist/release-01/YearDream
.venv\Scripts\python.exe -B -m pytest tests -q -p no:cacheprovider
```

패키지 검사는 임시 경로에 번들을 복사하고 프로젝트와 다른 작업 폴더 및 Python 경로가 제거된 환경에서 exe를 실행합니다. 로컬 합성 페이지로 health·UI·정적 분석·동적 CSS/JS·파일 위치·빈 결과·실패 보존·포트 충돌을 확인합니다. 기본 브라우저 자동 열기는 단위 검증하며 실제 패키지 검사는 --no-browser로 수행합니다. 원본 패키지·프로젝트 결과 파일은 변경하지 않습니다. 실제 사이트 정확도 검사와 다른 PC의 독립 실행 검증은 별도로 해야 합니다.

다른 Windows 11 x64 PC에서는 Python 없이 전체 ZIP을 해제하여 기본 분석을 실행하고, Edge 설치 후 동적 분석도 확인합니다. 실행 환경·결과 파일 위치·분석 시각·경고를 기록합니다. 이 단계가 끝나기 전 별도 PC 배포 검증 완료로 표시하지 않습니다. 공모전 소스·계획서·서약/동의 등 별도 제출 서류와 접수 확인은 별도로 준비합니다.

도구 참고: [PyInstaller 배포 옵션](https://www.pyinstaller.org/en/stable/usage.html), [실행 시 경로](https://www.pyinstaller.org/en/stable/runtime-information.html).
