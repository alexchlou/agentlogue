"""Structured local test results, bounded source provenance and safe CI exports."""
import collections
import datetime
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import tempfile
import unittest

from privacy_checks import check_text, git_output

EXPECTED_REPOSITORY_ID = '1433716711'
SHA = re.compile(r'[0-9a-f]{40}(?:[0-9a-f]{24})?\Z')


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def safe_sha(value):
    return value if value and SHA.fullmatch(value) else None


def numeric(value):
    return str(value) if value and re.fullmatch(r'[0-9]+', str(value)) and int(value) > 0 else None


def provenance(root, environ=None):
    env = os.environ if environ is None else environ
    result = {'source_kind': 'source_export', 'commit_sha': None, 'tree_sha': None, 'dirty_state': 'unknown',
              'repository_id': numeric(env.get('GITHUB_REPOSITORY_ID')),
              'expected_repository_id': EXPECTED_REPOSITORY_ID,
              'ci_run_id': numeric(env.get('GITHUB_RUN_ID')), 'run_attempt': numeric(env.get('GITHUB_RUN_ATTEMPT')),
              'job_api_id': numeric(env.get('AFP_CI_JOB_ID')), 'job_key': None,
              'event_sha': safe_sha(env.get('GITHUB_SHA')), 'pr_head_sha': safe_sha(env.get('AFP_PR_HEAD_SHA')),
              'os': platform.system(), 'architecture': platform.machine(), 'python': platform.python_version()}
    job = env.get('GITHUB_JOB', '')
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_-]*', job):
        result['job_key'] = job
    result['repository_identity_match'] = (result['repository_id'] == EXPECTED_REPOSITORY_ID
                                            if result['repository_id'] else None)
    if (Path(root) / '.git').exists() and shutil.which('git'):
        try:
            commit = git_output(root, 'rev-parse', 'HEAD')
            tree = git_output(root, 'rev-parse', 'HEAD^{tree}')
            dirty = git_output(root, 'status', '--porcelain=v1', '--untracked-files=all')
            if not (commit.returncode or tree.returncode or dirty.returncode):
                result.update(source_kind='git_checkout', commit_sha=safe_sha(commit.stdout.decode().strip()),
                              tree_sha=safe_sha(tree.stdout.decode().strip()),
                              dirty_state='dirty' if dirty.stdout else 'clean')
        except (OSError, ValueError):
            pass
    # The checked-out commit/tree are base identity; inventory binds modified bytes.
    return result


class OutcomeResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = {}

    def startTest(self, test):
        self.outcomes[test.id()] = 'pending'
        super().startTest(test)

    def addSuccess(self, test):
        self.outcomes[test.id()] = 'passed'
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.outcomes[test.id()] = 'failed'
        super().addFailure(test, err)

    def addError(self, test, err):
        self.outcomes[test.id()] = 'error'
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.outcomes[test.id()] = 'skipped'
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self.outcomes[test.id()] = 'expected_failure'
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self.outcomes[test.id()] = 'unexpected_success'
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, err):
        if err:
            status = 'failed' if issubclass(err[0], test.failureException) else 'error'
            if self.outcomes.get(test.id()) != 'error':
                self.outcomes[test.id()] = status
        super().addSubTest(test, subtest, err)


def execute_suite(suite, stream=None):
    discovered = suite.countTestCases()
    started = utc_now()
    result = unittest.TextTestRunner(stream=stream or io.StringIO(), verbosity=2,
                                    resultclass=OutcomeResult).run(suite)
    counted = collections.Counter(result.outcomes.values())
    counts = {key: counted[key] for key in ('passed', 'failed', 'error', 'skipped',
                                           'expected_failure', 'unexpected_success')}
    counts.update(discovered=discovered, run=result.testsRun, not_run=max(0, discovered - result.testsRun))
    return {'layer': 'offline_checker', 'successful': result.wasSuccessful() and counts['not_run'] == 0,
            'counts': counts, 'events': {'failure_events': len(result.failures), 'error_events': len(result.errors)},
            'started_at_utc': started, 'completed_at_utc': utc_now(),
            'limits': 'Synthetic helper tests; no Agent runtime, native host or mail operation.'}


def tool_versions():
    versions = {}
    for name in ('jsonschema', 'referencing', 'attrs', 'rpds-py', 'jsonschema-specifications', 'typing-extensions'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = 'not_available'
    return versions


def safe_public_report(report):
    # Select known fields; never copy arbitrary environment/log/error dictionaries.
    def pick(value, keys):
        return {key: value[key] for key in keys if key in value}
    value = pick(report, ('status', 'started_at_utc', 'completed_at_utc', 'python', 'zlib', 'candidate_only'))
    value['provenance'] = pick(report.get('provenance', {}), (
        'source_kind', 'commit_sha', 'tree_sha', 'dirty_state', 'repository_id', 'expected_repository_id',
        'repository_identity_match', 'ci_run_id', 'run_attempt', 'job_api_id', 'job_key', 'event_sha',
        'pr_head_sha', 'os', 'architecture', 'python'))
    tests = report.get('tests', {})
    value['tests'] = pick(tests, ('layer', 'successful', 'started_at_utc', 'completed_at_utc'))
    value['tests']['counts'] = pick(tests.get('counts', {}), ('discovered', 'run', 'passed', 'failed', 'error',
                                                          'skipped', 'expected_failure', 'unexpected_success', 'not_run'))
    value['tests']['events'] = pick(tests.get('events', {}), ('failure_events', 'error_events'))
    value['checks'] = pick(report.get('checks', {}), ('source', 'tests', 'schema', 'privacy', 'git_metadata', 'conformance', 'archives'))
    value['schema'] = pick(report.get('schema', {}), ('draft', 'example_valid', 'negative_controls_rejected', 'external_retrieval'))
    value['secrets'] = pick(report.get('secrets', {}), ('gitleaks_version', 'public_findings', 'synthetic_control_findings',
                                                     'reachable_git_metadata_included'))
    value['conformance'] = pick(report.get('conformance', {}), ('layer', 'fixtures_checked', 'evaluated_trace_pairs',
                                                             'valid_traces_accepted', 'invalid_traces_rejected'))
    value['tools'] = pick(report.get('tools', {}), ('jsonschema', 'referencing', 'attrs', 'rpds-py',
                                                  'jsonschema-specifications', 'typing-extensions'))
    value['archives'] = [pick(row, ('file', 'sha256', 'files', 'bytes')) for row in report.get('archives', [])]
    value['limits'] = 'Synthetic offline checks only; no live-host, mail, identity or legal-compliance certification.'
    value['source_manifest_sha256'] = hashlib.sha256((json.dumps(report['inventory'], indent=2) + '\n').encode()).hexdigest()
    for archive in value.get('archives', []):
        if not re.fullmatch(r'agentlogue-v[0-9]+\.[0-9]+\.[0-9]+-en-(github|skill)\.zip', archive['file']) or not re.fullmatch(r'[0-9a-f]{64}', archive['sha256']):
            raise ValueError('Unsafe archive evidence')
    check_text(json.dumps(value, ensure_ascii=False), 'public evidence')
    check_text(json.dumps(report['inventory'], ensure_ascii=False), 'public inventory')
    return value


def ci_export(report, artifacts, destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('CI export destination must be new')
    counts = report.get('tests', {}).get('counts', {})
    required = ('source', 'tests', 'schema', 'privacy', 'conformance')
    if (report.get('status') != 'passed' or report.get('tests', {}).get('successful') is not True
            or any(report.get('checks', {}).get(key) != 'passed' for key in required)
            or not isinstance(counts.get('run'), int) or counts['run'] <= 0
            or counts.get('discovered') != counts['run']
            or any(counts.get(key) != 0 for key in ('failed', 'error', 'unexpected_success', 'not_run'))
            or (report.get('archives') and report['checks'].get('archives') != 'passed')):
        raise ValueError('Only complete validation may export candidate archives')
    value = safe_public_report(report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.ci-export-', dir=str(destination.parent)) as temp:
        stage = Path(temp) / 'ready'; stage.mkdir()
        evidence = stage / 'validation-evidence'; evidence.mkdir()
        (evidence / 'VALIDATION-REPORT.json').write_bytes((json.dumps(value, indent=2) + '\n').encode('utf-8'))
        (evidence / 'SOURCE-MANIFEST.json').write_bytes((json.dumps(report['inventory'], indent=2) + '\n').encode('utf-8'))
        if report['archives']:
            packages = stage / 'candidate-archives'; packages.mkdir()
            for row in report['archives']:
                source = Path(artifacts) / row['file']
                if source.is_symlink() or hashlib.sha256(source.read_bytes()).hexdigest() != row['sha256']:
                    raise ValueError('Archive changed before evidence export')
                shutil.copyfile(source, packages / row['file'])
            (packages / 'SHA256SUMS.txt').write_bytes(''.join(row['sha256'] + '  ' + row['file'] + '\n' for row in report['archives']).encode('utf-8'))
        stage.rename(destination)


def failure_export(destination, stage):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        return False
    destination.mkdir(parents=True)
    evidence = destination / 'validation-evidence'; evidence.mkdir()
    allowed = ('source', 'tests', 'schema', 'privacy', 'conformance', 'archives', 'report_export', 'setup')
    value = {'status': 'failed', 'stage': stage if stage in allowed else 'unknown',
             'code': 'VALIDATION_NOT_COMPLETED', 'candidate_archives_exported': False}
    (evidence / 'FAILURE.json').write_bytes((json.dumps(value, indent=2) + '\n').encode('utf-8'))
    return True
