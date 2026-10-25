import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/package_submission.py'
spec = importlib.util.spec_from_file_location('package_submission', SCRIPT)
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


@pytest.fixture
def inputs(tmp_path):
    root, bundle = tmp_path / 'source', tmp_path / 'bundle'
    names = sorted(package.REQUIRED_SOURCE | {'backend/app/rendered_snapshot.js',
                    'backend/app/evaluation.py', '.gitignore', '.env', 'result.json',
                    '.validation/private.html', 'tests/fixtures/example.json'})
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('fixture ' + name, encoding='utf-8')
    files = {name: ('bundle ' + name).encode() for name in package.REQUIRED_RUNTIME}
    files['_internal/support.dll'] = b'support'
    for name, raw in files.items():
        path = bundle / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    # A previous user analysis must not enter a clean distribution.
    (bundle / 'result.json').write_text('previous user result', encoding='utf-8')
    manifest = dict(bundle_sha256={name: package.digest(raw) for name, raw in files.items()},
        source_sha256={name: package.digest((root / name).read_bytes()) for name in
                       ['run_app.py', 'backend/app/main.py', 'frontend/static/index.html',
                        'backend/app/rendered_snapshot.js', 'requirements.txt', 'backend/app/evaluation.py']})
    package.write_json(bundle / 'build-manifest.json', manifest)
    validation = tmp_path / 'validated.json'
    package.write_json(validation, dict(status='passed', scope='synthetic package test',
        manifest_sha256=package.digest((bundle / 'build-manifest.json').read_bytes()),
        executable_sha256=manifest['bundle_sha256']['YearDream.exe']))
    return root, bundle, validation, tmp_path / 'output', names


def assemble(inputs):
    return package.assemble(*inputs, revision='synthetic-revision')


def test_candidate_contains_runtime_source_docs_and_pending_status(inputs):
    root, bundle, validation, output, names = inputs
    result = assemble(inputs)
    folder = output / 'YearDream-submission'
    record = json.loads((folder / 'submission-manifest.json').read_bytes())
    assert result['ready_to_submit'] is record['ready_to_submit'] is False
    assert len(record['pending']) == 4
    assert record['source_revision'] == 'synthetic-revision'
    for name, expected in record['files_sha256'].items():
        assert package.digest((folder / name).read_bytes()) == expected
    assert (folder / '01_run/YearDream/YearDream.exe').exists()
    assert not (folder / '01_run/YearDream/result.json').exists()
    with zipfile.ZipFile(folder / '02_source/YearDream-source.zip') as archive:
        paths = archive.namelist()
        assert 'YearDream-source/backend/app/main.py' in paths
        assert 'YearDream-source/tests/fixtures/example.json' in paths
        assert not any('.env' in name or '.validation' in name or name.endswith('result.json') for name in paths)
        assert archive.read('YearDream-source/run_app.py') == (root / 'run_app.py').read_bytes()
    with zipfile.ZipFile(result['zip']) as archive:
        assert archive.testzip() is None
        assert 'YearDream-submission/START_HERE.md' in archive.namelist()
    assert hashlib.sha256(Path(result['zip']).read_bytes()).hexdigest() == result['zip_sha256']
    assert '결과' in (folder / 'START_HERE.md').read_text(encoding='utf-8')
    with pytest.raises(ValueError, match='already exists'):
        assemble(inputs)


@pytest.mark.parametrize('name', ['run_app.py', 'frontend/static/index.html', 'backend/app/main.py'])
def test_stale_runtime_source_is_rejected_before_output(inputs, name):
    (inputs[0] / name).write_text('changed', encoding='utf-8')
    with pytest.raises(ValueError, match='rebuild and test'):
        assemble(inputs)
    assert not inputs[3].exists()


def test_new_runtime_module_requires_new_build(inputs):
    root, bundle, validation, output, names = inputs
    (root / 'backend/app/new_runtime.py').write_text('new code', encoding='utf-8')
    names.append('backend/app/new_runtime.py')
    with pytest.raises(ValueError, match='rebuild and test'):
        assemble(inputs)


def test_later_offline_tools_are_recorded_separately(inputs):
    (inputs[0] / 'backend/app/evaluation.py').write_text('offline-only update', encoding='utf-8')
    result = assemble(inputs)
    record = json.loads((Path(result['package']) / 'submission-manifest.json').read_bytes())
    assert record['offline_source_changes'] == ['backend/app/evaluation.py']


@pytest.mark.parametrize('corrupt', ['runtime', 'report', 'exe_hash', 'traversal', 'missing'])
def test_corrupt_or_wrong_build_evidence_is_rejected(inputs, corrupt):
    root, bundle, validation, output, names = inputs
    if corrupt == 'runtime':
        (bundle / 'YearDream.exe').write_bytes(b'tampered')
    elif corrupt == 'report':
        package.write_json(validation, {'status': 'failed'})
    elif corrupt == 'exe_hash':
        data = json.loads(validation.read_bytes())
        data['executable_sha256'] = '0' * 64
        package.write_json(validation, data)
    elif corrupt == 'missing':
        names.remove('docs/USER_MANUAL.md')
    else:
        data = json.loads((bundle / 'build-manifest.json').read_bytes())
        data['bundle_sha256']['../escape.dll'] = '0' * 64
        package.write_json(bundle / 'build-manifest.json', data)
        report = json.loads(validation.read_bytes())
        report['manifest_sha256'] = package.digest((bundle / 'build-manifest.json').read_bytes())
        package.write_json(validation, report)
    with pytest.raises(ValueError):
        assemble(inputs)
    assert not output.exists()
