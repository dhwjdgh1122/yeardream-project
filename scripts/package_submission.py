"""Assemble an auditable submission candidate from clean source and a tested bundle."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile

OFFLINE_MODULES = {
    'backend/app/evaluation.py', 'backend/app/review.py',
    'backend/app/validation_suite.py', 'backend/app/review_inventory.py',
}
REQUIRED_SOURCE = {'run_app.py', 'backend/app/main.py', 'frontend/static/index.html',
                   'requirements.txt', 'requirements-browser.txt', 'requirements-build.txt',
                   'requirements-dev.txt', 'constraints-windows-py314.txt',
                   'scripts/build_windows.py', 'docs/USER_MANUAL.md', 'docs/BUILD_MANUAL.md',
                   'docs/SUBMISSION_CHECKLIST.md', 'docs/OTHER_PC_CHECKLIST.md'}
REQUIRED_RUNTIME = {'YearDream.exe', '_internal/frontend/static/index.html',
                    '_internal/backend/app/rendered_snapshot.js'}
REFERENCE_PDF = '공공 웹사이트 불법광고 탐지 도구 개발 공모전 모집요강.pdf'
REFERENCE_SHA256 = '69d72dee6058d59f7799454a9460f190f9466e9dd991ce4980415919b84605b6'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_file(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
        raise ValueError(f'Invalid relative path: {name}')
    path = (root / Path(*relative.parts)).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'Missing file or path outside its root: {name}')
    return path


def include_source(name):
    parts = PurePosixPath(name).parts
    if not parts or any(part.startswith('.') for part in parts):
        return name == '.gitignore'
    if any(part.lower() in {'__pycache__', 'node_modules', 'build', 'dist', 'venv'} for part in parts):
        return False
    if PurePosixPath(name).name.lower() in {'result.json', 'result_extra.json'}:
        return False
    if len(parts) == 1:
        return name == 'run_app.py' or name.endswith('.md') or (
            name.startswith(('requirements', 'constraints')) and name.endswith('.txt'))
    return parts[0] in {'backend', 'frontend', 'scripts', 'tests', 'docs'} and PurePosixPath(name).suffix.lower() in {
        '.py', '.js', '.cjs', '.html', '.css', '.json', '.md', '.txt', '.svg', '.png', '.jpg', '.jpeg', '.webp',
    }


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')


def assemble(root, bundle, validation_path, output, source_names, revision):
    """Validate every input before creating a new output directory."""
    root, bundle, output = Path(root).resolve(), Path(bundle).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('Submission output already exists; choose a new directory')
    if root.is_relative_to(output) or bundle.is_relative_to(output):
        raise ValueError('Output must not contain the input source or bundle')
    source = {name: safe_file(root, name).read_bytes() for name in source_names if include_source(name)}
    missing = REQUIRED_SOURCE - source.keys()
    if missing:
        raise ValueError(f'Missing required source/manuals: {sorted(missing)}')
    manifest_raw = (bundle / 'build-manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    validation_raw = Path(validation_path).read_bytes()
    validation = json.loads(validation_raw)
    if validation.get('status') != 'passed' or validation.get('manifest_sha256') != digest(manifest_raw):
        raise ValueError('Validation report is not a passed report for this build manifest')
    expected = manifest['bundle_sha256']
    if not REQUIRED_RUNTIME <= expected.keys():
        raise ValueError('Runtime executable or bundled UI/style assets are missing')
    runtime = {}
    for name, sha in expected.items():
        raw = safe_file(bundle, name).read_bytes()
        if digest(raw) != sha:
            raise ValueError(f'Bundle file hash mismatch: {name}')
        runtime[name] = raw
    if validation.get('executable_sha256') != expected['YearDream.exe']:
        raise ValueError('Validation executable hash mismatch')
    # Changes to explicitly offline tools can accompany an unchanged executable.
    # Every other recorded build input, and newly introduced runtime modules,
    # must match the actual source bytes supplied for rebuilding.
    build_source = manifest['source_sha256']
    must_match = {name for name in build_source if name not in OFFLINE_MODULES}
    must_match |= {name for name in source if (
        name.startswith('backend/app/') and PurePosixPath(name).suffix in {'.py', '.js', '.json'}
        and name not in OFFLINE_MODULES) or name.startswith('frontend/static/')}
    must_match |= {'run_app.py', 'frontend/static/index.html', 'backend/app/rendered_snapshot.js'}
    for name in must_match:
        if name not in source or name not in build_source or digest(source[name]) != build_source[name]:
            raise ValueError(f'Source differs from the executable build; rebuild and test first: {name}')
    offline_changes = sorted(name for name in OFFLINE_MODULES if name in source
                             and digest(source[name]) != build_source.get(name))
    reference = safe_file(root, REFERENCE_PDF).read_bytes() if REFERENCE_PDF in source_names else None
    if reference is not None and digest(reference) != REFERENCE_SHA256:
        raise ValueError('Reference PDF differs from the previously verified contest document')
    package = output / 'YearDream-submission'
    runtime_dir = package / '01_run' / 'YearDream'
    runtime_dir.mkdir(parents=True)
    for name, raw in runtime.items():
        target = runtime_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (runtime_dir / 'build-manifest.json').write_bytes(manifest_raw)
    source_dir = package / '02_source'
    source_dir.mkdir()
    source_zip = source_dir / 'YearDream-source.zip'
    with zipfile.ZipFile(source_zip, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(source.items()):
            archive.writestr('YearDream-source/' + name, raw)
    docs = package / '03_docs'
    docs.mkdir()
    for name in ('USER_MANUAL.md', 'BUILD_MANUAL.md', 'SUBMISSION_CHECKLIST.md', 'OTHER_PC_CHECKLIST.md'):
        (docs / name).write_bytes(source['docs/' + name])
    forms = package / '04_forms'
    forms.mkdir()
    if reference is not None:
        (forms / 'original_contest.pdf').write_bytes(reference)
    (forms / 'REQUIRED_FORMS.md').write_text(
        '# 별도 작성·서명할 서류\n\n이 폴더의 안내는 공식 서류를 대체하지 않습니다.\n\n'
        '- 참가신청서\n- 서약서\n- 개인정보 수집·이용 동의서(팀 전원)\n'
        '- 기획서 5~10매(이미지 문서 내 포함)\n\n'
        '참가자 정보·서명·최종 기획서는 이 묶음에 작성되지 않았습니다. 공식 양식을 사용해 별도로 완성하세요.\n'
        'original_contest.pdf가 있으면 원문의 붙임 양식(15~18쪽)을 확인하세요. 원문 자체는 작성된 서류가 아닙니다.\n',
        encoding='utf-8', newline='\n')
    evidence = package / '05_verification'
    evidence.mkdir()
    (evidence / 'build-manifest.json').write_bytes(manifest_raw)
    (evidence / 'packaged-validation.json').write_bytes(validation_raw)
    (package / 'START_HERE.md').write_text(
        '# YearDream 제출 후보 묶음\n\n'
        '**실행: `01_run/YearDream/YearDream.exe`. 결과: 같은 폴더의 `result.json`, `result_extra.json`.**\n\n'
        'ZIP 전체를 압축 해제하고 실행 폴더의 `_internal`도 함께 유지하세요. 동적 분석은 설치된 Edge가 필요합니다.\n\n'
        '- `02_source/YearDream-source.zip`: 전체 소스·테스트·빌드 스크립트·문서\n'
        '- `03_docs`: 사용/빌드 설명서와 제출·다른 PC 점검표\n'
        '- `04_forms`: 별도 작성해야 할 서류 안내\n'
        '- `05_verification`: 해당 빌드와 현재 PC의 패키지 검사 근거\n\n'
        '**최종 제출 완료본이 아닙니다.** 서류 작성/서명, 별도 Windows PC 검증, 실제 접수 가능 여부 확인이 남아 있습니다. '
        '현재 PC의 합성 검사 통과는 실제 사이트 전체 정확도나 공모전 통과를 뜻하지 않습니다.\n'
        '실제 수집 HTML·검수 자료·기존 결과 파일·가상환경·Git 이력은 포함하지 않았습니다.\n',
        encoding='utf-8', newline='\n')
    record = {
        'schema_version': 1, 'purpose': 'submission_candidate', 'ready_to_submit': False,
        'created_at': datetime.now(timezone.utc).isoformat(), 'source_revision': revision,
        'source_sha256': {name: digest(raw) for name, raw in sorted(source.items())},
        'verified_build_inputs': sorted(must_match), 'offline_source_changes': offline_changes,
        'build_manifest_sha256': digest(manifest_raw), 'validation_report_sha256': digest(validation_raw),
        'reference_pdf_sha256': digest(reference) if reference is not None else None,
        'validation_scope': validation.get('scope'),
        'pending': ['Completed official forms and signatures', 'Independent Windows 11 PC execution',
                    'Submission schedule/amendments and actual receipt', 'Broader independent detection evaluation'],
        'files_sha256': {p.relative_to(package).as_posix(): digest(p.read_bytes())
                         for p in sorted(package.rglob('*')) if p.is_file()},
    }
    write_json(package / 'submission-manifest.json', record)
    archive_path = output / 'YearDream-submission.zip'
    with zipfile.ZipFile(archive_path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                archive.write(path, 'YearDream-submission/' + path.relative_to(package).as_posix())
    checksum = digest(archive_path.read_bytes())
    (output / 'YearDream-submission.zip.sha256').write_text(
        checksum + '  YearDream-submission.zip\n', encoding='ascii')
    return {'package': str(package), 'zip': str(archive_path), 'zip_sha256': checksum,
            'source_files': len(source), 'runtime_files': len(runtime), 'ready_to_submit': False}


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--validation-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    git = ['git', '-c', f'safe.directory={root.as_posix()}']
    try:
        status = subprocess.run([*git, 'status', '--porcelain', '--untracked-files=normal'], cwd=root,
                                capture_output=True, check=True).stdout
        if status.strip():
            raise ValueError('Commit the source/manuals first; package only a clean working tree')
        revision = subprocess.run([*git, 'rev-parse', 'HEAD'], cwd=root, capture_output=True, check=True).stdout.decode().strip()
        names = subprocess.run([*git, 'ls-files', '-z'], cwd=root, capture_output=True, check=True).stdout.decode('utf-8').split('\0')
        result = assemble(root, args.bundle, args.validation_report, args.output,
                          [name for name in names if name], revision)
        print(json.dumps(result))
        return 0
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print(f'Submission assembly failed: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(run())
