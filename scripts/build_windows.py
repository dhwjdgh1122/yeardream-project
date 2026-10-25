"""Build a new Windows onedir bundle and ZIP without replacing previous releases."""

import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New release directory, e.g. dist/release-01')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if platform.system() != 'Windows' or platform.machine().lower() not in ('amd64', 'x86_64'):
        parser.error('Build on Windows x64 with the documented Python environment')
    if output.exists() or output.with_suffix('.zip').exists():
        parser.error('Output or ZIP already exists; choose a new release directory')
    output.mkdir(parents=True)
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onedir', '--console', '--noupx',
               '--name', 'YearDream', '--distpath', str(output),
               '--workpath', str(output / 'work'), '--specpath', str(output / 'spec'),
               '--paths', str(root),
               '--add-data', f'{root / "frontend/static"}:frontend/static',
               '--add-data', f'{root / "backend/app/rendered_snapshot.js"}:backend/app',
               '--collect-all', 'playwright',
               '--hidden-import', 'uvicorn.logging', '--hidden-import', 'uvicorn.loops.asyncio',
               '--hidden-import', 'uvicorn.protocols.http.h11_impl', '--hidden-import', 'uvicorn.lifespan.on',
               '--exclude-module', 'pytest', '--exclude-module', 'tkinter',
               str(root / 'run_app.py')]
    subprocess.run(command, cwd=root, check=True)
    bundle = output / 'YearDream'
    for name in ('USER_MANUAL.md', 'BUILD_MANUAL.md'):
        shutil.copy2(root / 'docs' / name, bundle / name)
    packages = ('pyinstaller', 'pyinstaller-hooks-contrib', 'playwright', 'fastapi', 'uvicorn',
                'httpx', 'beautifulsoup4', 'html5lib', 'pydantic')
    source_paths = [root / 'run_app.py', *sorted((root / 'backend/app').glob('*.py')),
                    root / 'backend/app/rendered_snapshot.js', *sorted((root / 'frontend/static').rglob('*')),
                    root / 'scripts/build_windows.py', root / 'requirements-build.txt',
                    root / 'constraints-windows-py314.txt', root / 'requirements.txt', root / 'requirements-browser.txt']
    manifest = {
        'built_at': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(),
        'platform': platform.platform(), 'packages': {name: version(name) for name in packages},
        'source_sha256': {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in source_paths if p.is_file()},
        'bundle_sha256': {p.relative_to(bundle).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(bundle.rglob('*')) if p.is_file()},
        'validation': 'Build completed; run scripts/test_packaged.py separately. Other-PC validation is pending.',
    }
    (bundle / 'build-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    archive = shutil.make_archive(str(output / 'YearDream-windows-x64'), 'zip', output, 'YearDream')
    print(json.dumps({'bundle': str(bundle), 'zip': archive}))


if __name__ == '__main__':
    run()
