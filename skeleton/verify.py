"""Exercise a committed Skeleton against public dependencies, including real failures."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

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
        reports = sorted((project / 'build/test-results/test').glob('*.xml'))
        assert reports, stage + ' produced no JUnit XML; inspect log'
        report_dir = args.results / stage
        (report_dir / 'test-results').mkdir(parents=True, exist_ok=True)
        for report in reports:
            shutil.copy2(report, report_dir / 'test-results' / report.name)
        shutil.copytree(project / 'build/reports/tests/test', report_dir / 'html', dirs_exist_ok=True)
        suites = [ET.parse(report).getroot() for report in reports]
        counts = {key: sum(int(suite.get(key, '0')) for suite in suites)
                  for key in ['tests', 'failures', 'errors', 'skipped']}
        assert counts['tests'] > 0 and counts['errors'] == 0 and counts['skipped'] == 0, (stage, counts)
        if rejected:
            assert completed.returncode != 0, stage + ' unexpectedly passed'
            assert counts['failures'] > 0, stage + ' has no failed test in XML'
            failures = '\n'.join(node.text or '' for suite in suites for node in suite.iter('failure'))
            for expected in ['expected caller class', 'example.shipping.Client', 'Shipment.dispatch']:
                assert expected in output, stage + ' failed for an unrelated reason: ' + expected
                assert expected in failures, stage + ' XML lacks boundary diagnosis: ' + expected
            access_kind = 'calls method' if stage == 'direct' else 'references method'
            assert access_kind in failures, stage + ' XML lacks ' + access_kind
        else:
            assert completed.returncode == 0, stage + ' failed; inspect log'
            assert 'H1 boundary passed' in output and 'dispatch: ready' in output
            assert counts['failures'] == 0, stage + ' has failed tests in XML'
        results.append({'stage': stage, 'exitCode': completed.returncode, 'expectedRejection': rejected,
                        'junit': counts, 'reports': stage + '/'})
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
