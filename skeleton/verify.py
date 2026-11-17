"""Exercise a committed Skeleton against public dependencies, including real failures."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True)
parser.add_argument('--results', type=Path, required=True)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
args.results.mkdir(parents=True, exist_ok=True)
results = []
with tempfile.TemporaryDirectory(prefix='skeleton-') as temporary:
    root = Path(temporary)
    project = root / 'project'
    subprocess.run([sys.executable, str(repo / 'skeleton/create.py'), '--source', args.source,
                    '--output', str(project)], check=True)
    env = {**os.environ, 'GRADLE_USER_HOME': str(root / 'gradle-cache')}
    def run(stage, rejected=False):
        command = ['sh', 'gradlew', '--no-daemon', '--console=plain']
        if os.environ.get('BOUNDARY_JAVA_HOME'):
            command += ['-PruntimeJavaHome=' + os.environ['BOUNDARY_JAVA_HOME']]
        command += ['clean', 'check', 'run']
        completed = subprocess.run(command, cwd=project, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = completed.stdout.decode('utf-8', errors='replace')
        (args.results / (stage + '.log')).write_text(output, encoding='utf-8')
        if rejected:
            assert completed.returncode != 0, stage + ' unexpectedly passed'
            for expected in ['expected caller class', 'example.shipping.Client', 'Shipment.dispatch']:
                assert expected in output, stage + ' failed for an unrelated reason: ' + expected
        else:
            assert completed.returncode == 0, stage + ' failed; inspect log'
            assert 'H1 boundary passed' in output and 'dispatch: ready' in output
        results.append({'stage': stage, 'exitCode': completed.returncode, 'expectedRejection': rejected})
        print(stage + (': expected boundary rejection' if rejected else ': passed'), flush=True)
    run('allowed')
    client = project / 'src/main/java/example/shipping/Client.java'
    for scenario in ['direct', 'reference']:
        source = 'example/src/scenarios/' + scenario + '/java/example/shipping/Client.java'
        client.write_bytes(subprocess.check_output(['git', '-C', str(repo), 'show', args.source + ':' + source]))
        run(scenario, rejected=True)
    for name in ['Client.java', 'DispatchOperation.java']:
        source = 'example/src/scenarios/fixed/java/example/shipping/' + name
        (client.parent / name).write_bytes(subprocess.check_output(
            ['git', '-C', str(repo), 'show', args.source + ':' + source]))
    run('fixed')
    properties = project / 'gradle.properties'
    current = properties.read_text(encoding='utf-8')
    properties.write_text(current.replace('toolboxVersion=0.4.0', 'toolboxVersion=0.3.1'), encoding='utf-8')
    run('before-dependency-update')
    properties.write_text(current, encoding='utf-8')
    run('after-dependency-update')
    summary = {'sourceCommit': args.source, 'publicOnly': True, 'freshInitialCache': True,
               'runtimeJavaHome': os.environ.get('BOUNDARY_JAVA_HOME', 'build JVM'),
               'stages': results, 'templateCrossVersionUpdate': 'Not verified: no previous published Skeleton version',
               'independentConsumerCIHistory': 'Not produced by this local scenario runner'}
    (args.results / 'result.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
