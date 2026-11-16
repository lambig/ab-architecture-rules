"""Export an independent project from an exact committed template revision."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if not re.fullmatch(r'[0-9a-f]{40}', args.source):
    parser.error('--source must be a full commit SHA')
repo = Path(__file__).resolve().parents[1]

def git(*argv):
    return subprocess.check_output(['git', '-C', str(repo), *argv])

if git('rev-parse', 'HEAD').decode().strip() != args.source:
    parser.error('Check out the requested source revision before running its exporter')
if args.output.exists() and any(args.output.iterdir()):
    parser.error('Output must be absent or empty; existing projects are never overwritten')
files = {}
for name in ['gradlew', 'gradlew.bat', 'gradle/wrapper/gradle-wrapper.jar',
             'gradle/wrapper/gradle-wrapper.properties']:
    files[name] = 'example/' + name
for prefix in ['example/src/main/', 'example/src/test/', 'example/src/scenarios/allowed/']:
    for name in git('ls-tree', '-r', '--name-only', args.source, prefix).decode().splitlines():
        target = name.removeprefix('example/').replace('src/scenarios/allowed/', 'src/main/')
        files[target] = name
for name in git('ls-tree', '-r', '--name-only', args.source, 'skeleton/template/').decode().splitlines():
    files[name.removeprefix('skeleton/template/')] = name
if 'build.gradle' not in files:
    parser.error('This revision does not contain a Skeleton template')
manifest = {'format': 1, 'repository': 'https://github.com/lambig/ab-architecture-rules',
            'sourceCommit': args.source, 'files': {}}
for target, source in sorted(files.items()):
    content = git('show', args.source + ':' + source)
    dest = args.output / target
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    manifest['files'][target] = hashlib.sha256(content).hexdigest()
(args.output / 'skeleton-source.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print('Exported committed Skeleton ' + args.source)
