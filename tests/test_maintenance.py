"""Bounded maintenance regressions using only synthetic local material."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'scripts'))
import conformance
import privacy_checks as privacy
import release_evidence as evidence
import validate_release as release


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='agentlogue-maintenance-tests-')
        self.area = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def source_copy(self):
        root = self.area / 'source'
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('.git', '__pycache__'))
        return root

    def test_copyright_quote_tamper_fails_without_changing_license(self):
        root = self.source_copy()
        before = (root / 'LICENSE').read_bytes()
        p = root / 'README.md'
        p.write_text(p.read_text().replace('Copyright (c) 2026 Alexander C. H. Lou', 'Copyright (c) 2026 Example Contributor'))
        with self.assertRaisesRegex(ValueError, 'copyright quotation'):
            release.check_source(root)
        self.assertEqual(before, (root / 'LICENSE').read_bytes())

    def test_display_author_can_differ_from_exact_license_notice(self):
        root = self.source_copy(); p = root / 'README.md'
        p.write_text(p.read_text().replace('**Alexander C. H. Lou**', '**Example Display Author**'))
        release.check_source(root)

    def test_unicode_escaped_md_and_checkout_email_candidates_rejected(self):
        values = [chr(0x7528) + chr(0x6237) + '@' + chr(0x4f8b) + chr(0x5b50) + '.' + chr(0x516c) + chr(0x53f8),
                  'person' + '@' + 'privacy.md', 'person_checkout' + '@' + 'privacy.example',
                  '{"email":"person' + r'\u0040' + 'privacy' + r'\u002e' + 'example"}']
        for value in values:
            with self.subTest(kind=values.index(value)), self.assertRaises(ValueError):
                privacy.check_text(value, 'synthetic fixture')

    def test_only_bounded_noreply_service_and_invalid_examples_allowed(self):
        for value in ['ledger@example.invalid', '123+example@users.noreply.github.com', 'noreply@github.com']:
            privacy.check_text(value, 'synthetic fixture')
        with self.assertRaises(ValueError):
            privacy.check_text('noreply' + '@' + 'privacy.example', 'synthetic fixture')

    def test_source_export_provenance_and_job_key_are_not_fabricated_ids(self):
        env = {'GITHUB_REPOSITORY_ID': '1433716711', 'GITHUB_JOB': 'release-checks', 'GITHUB_RUN_ID': '123',
               'GITHUB_RUN_ATTEMPT': '2', 'GITHUB_SHA': 'a' * 40, 'AFP_PR_HEAD_SHA': 'b' * 40,
               'PRIVATE_ENV': 'synthetic-hidden-value'}
        value = evidence.provenance(self.area, env)
        self.assertIsNone(value['commit_sha']); self.assertEqual(value['dirty_state'], 'unknown')
        self.assertEqual(value['job_key'], 'release-checks'); self.assertIsNone(value['job_api_id'])
        self.assertNotEqual(value['event_sha'], value['pr_head_sha'])
        self.assertNotIn('synthetic-hidden-value', json.dumps(value))

    def git(self, root, *args):
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
        result = subprocess.run(['git', '-c', 'core.hooksPath=' + os.devnull, '-c', 'commit.gpgsign=false',
                                 '-c', 'user.name=Example Author', '-c', 'user.email=123+demo@users.noreply.github.com',
                                 '-C', str(root), *args], capture_output=True, env=env)
        self.assertEqual(result.returncode, 0, 'Synthetic Git fixture operation failed')

    @unittest.skipUnless(shutil.which('git'), 'Git metadata fixture requires Git')
    def test_git_commit_and_tag_private_identity_are_rejected(self):
        self.git(self.area, 'init', '--quiet')
        self.git(self.area, 'commit', '--allow-empty', '-m', 'Synthetic baseline')
        self.assertEqual(privacy.check_git_metadata(self.area)['status'], 'passed')
        env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_COMMITTER_NAME='Example Author', GIT_COMMITTER_EMAIL='person' + '@' + 'privacy.example')
        result = subprocess.run(['git', '-c', 'tag.gpgsign=false', '-C', str(self.area),
                                 'tag', '-a', 'synthetic-tag', '-m', 'Synthetic tag'], env=env, capture_output=True)
        self.assertEqual(result.returncode, 0)
        with self.assertRaises(ValueError):
            privacy.check_git_metadata(self.area)
        self.git(self.area, 'tag', '-d', 'synthetic-tag')
        self.git(self.area, '-c', 'user.email=' + 'person' + '@' + 'privacy.example',
                 'commit', '--allow-empty', '-m', 'Synthetic private identity')
        with self.assertRaises(ValueError):
            privacy.check_git_metadata(self.area)

    @unittest.skipUnless(shutil.which('git'), 'Git provenance fixture requires Git')
    def test_dirty_checkout_provenance_never_exports_file_paths(self):
        self.git(self.area, 'init', '--quiet'); self.git(self.area, 'commit', '--allow-empty', '-m', 'Synthetic baseline')
        (self.area / 'private-fixture-name.txt').write_text('Synthetic')
        value = evidence.provenance(self.area, {})
        self.assertEqual(value['dirty_state'], 'dirty'); self.assertIsNotNone(value['tree_sha'])
        self.assertNotIn('private-fixture-name', json.dumps(value)); self.assertNotIn(str(self.area), json.dumps(value))

    def test_structured_outcomes_include_skips_failures_errors_and_subtests(self):
        class Cases(unittest.TestCase):
            def test_ok(self): pass
            @unittest.skip('Synthetic skip')
            def test_skip(self): pass
            def test_fail(self): self.fail('Synthetic failure')
            def test_error(self): raise ValueError('Synthetic error')
            @unittest.expectedFailure
            def test_expected(self): self.fail('Synthetic expected failure')
            @unittest.expectedFailure
            def test_unexpected(self): pass
            def test_subtests(self):
                for i in (1, 2):
                    with self.subTest(i=i): self.assertEqual(i, 0)
        result = evidence.execute_suite(unittest.defaultTestLoader.loadTestsFromTestCase(Cases), io.StringIO())
        self.assertEqual(result['counts'], dict(discovered=7, run=7, passed=1, failed=2, error=1,
                                                skipped=1, expected_failure=1, unexpected_success=1, not_run=0))
        self.assertEqual(result['events']['failure_events'], 3)
        self.assertFalse(result['successful'])

    def test_interrupted_suite_cannot_claim_complete_success(self):
        class Halt(unittest.TestSuite):
            def run(self, result, debug=False): result.stop(); return result
        suite = Halt([unittest.FunctionTestCase(lambda: None)])
        result = evidence.execute_suite(suite)
        self.assertEqual(result['counts']['not_run'], 1); self.assertFalse(result['successful'])

    def report(self):
        return {'status': 'passed', 'candidate_only': True, 'inventory': [], 'archives': [],
                'provenance': {'source_kind': 'source_export'}, 'tests': {'successful': True,
                'counts': dict(discovered=1, run=1, passed=1, failed=0, error=0, skipped=0,
                               expected_failure=0, unexpected_success=0, not_run=0)},
                'checks': {key: 'passed' for key in ('source', 'tests', 'schema', 'privacy', 'conformance', 'archives')}}

    def test_inconsistent_success_marker_cannot_export_failed_checks(self):
        for key in ('failed', 'error', 'unexpected_success', 'not_run'):
            value = self.report(); value['tests']['counts'][key] = 1
            with self.assertRaises(ValueError): evidence.ci_export(value, None, self.area / ('export-' + key))
        value = self.report(); value['checks']['privacy'] = 'failed'
        with self.assertRaises(ValueError): evidence.ci_export(value, None, self.area / 'export-privacy')

    def test_ci_export_ignores_unapproved_root_and_nested_fields(self):
        value = self.report(); value['raw_environment'] = 'synthetic-secret-marker'
        value['provenance']['raw_environment'] = 'synthetic-secret-marker'
        value['tests']['raw_log'] = 'synthetic-secret-marker'
        with mock.patch.object(Path, 'write_text', side_effect=AssertionError('CI JSON must use explicit UTF-8/LF bytes')):
            evidence.ci_export(value, None, self.area / 'export')
        files = {p.relative_to(self.area / 'export').as_posix() for p in (self.area / 'export').rglob('*') if p.is_file()}
        self.assertEqual(files, {'validation-evidence/VALIDATION-REPORT.json', 'validation-evidence/SOURCE-MANIFEST.json'})
        self.assertNotIn('synthetic-secret-marker', (self.area / 'export/validation-evidence/VALIDATION-REPORT.json').read_text())
        exported = json.loads((self.area / 'export/validation-evidence/VALIDATION-REPORT.json').read_text())
        self.assertEqual(exported['source_manifest_sha256'], hashlib.sha256(
            (self.area / 'export/validation-evidence/SOURCE-MANIFEST.json').read_bytes()).hexdigest())

    def test_failed_validation_has_only_safe_summary_and_no_archives(self):
        evidence.failure_export(self.area / 'export', 'privacy')
        files = [p for p in (self.area / 'export').rglob('*') if p.is_file()]
        self.assertEqual(len(files), 1); self.assertEqual(files[0].name, 'FAILURE.json')
        self.assertFalse(json.loads(files[0].read_text())['candidate_archives_exported'])
        before = files[0].read_bytes(); self.assertFalse(evidence.failure_export(self.area / 'export', 'tests'))
        self.assertEqual(before, files[0].read_bytes())
        value = self.report(); value['status'] = 'failed'
        with self.assertRaises(ValueError): evidence.ci_export(value, None, self.area / 'other')
        self.assertFalse((self.area / 'other').exists())

    def test_changed_archive_cannot_reach_public_export(self):
        packages = self.area / 'packages'; packages.mkdir()
        name = 'agentlogue-v1.4.3-en-github.zip'
        with zipfile.ZipFile(packages / name, 'w') as z: z.writestr('README.md', 'Synthetic archive')
        value = self.report(); value['archives'] = [{'file': name, 'sha256': '0' * 64, 'files': 1, 'bytes': 1}]
        with self.assertRaises(ValueError): evidence.ci_export(value, packages, self.area / 'export')
        self.assertFalse((self.area / 'export').exists())

    def test_success_export_contains_only_verified_declared_archives(self):
        packages = self.area / 'packages'; packages.mkdir(); name = 'agentlogue-v1.4.3-en-github.zip'
        with zipfile.ZipFile(packages / name, 'w') as z: z.writestr('README.md', 'Synthetic archive')
        (packages / 'private-config.json').write_text('{}'); (packages / 'raw.log').write_text('Synthetic private log')
        value = self.report(); data = (packages / name).read_bytes()
        value['archives'] = [{'file': name, 'sha256': hashlib.sha256(data).hexdigest(), 'files': 1, 'bytes': len(data)}]
        evidence.ci_export(value, packages, self.area / 'export')
        files = {p.name for p in (self.area / 'export').rglob('*') if p.is_file()}
        self.assertEqual(files, {name, 'SHA256SUMS.txt', 'SOURCE-MANIFEST.json', 'VALIDATION-REPORT.json'})

    def test_workflow_uploads_are_pinned_and_do_not_include_raw_workspace(self):
        text = (ROOT / '.github/workflows/validate.yml').read_text()
        self.assertNotIn('github.workspace', text)
        self.assertNotIn('path: ${{ runner.temp }}\n', text)
        self.assertIn('persist-credentials: false', text); self.assertIn('needs: tests', text)
        self.assertIn('upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9', text)
        self.assertNotIn('path: ${{ runner.temp }}/tests-private.log', text)

    def test_corpus_has_meaningful_paired_controls_without_live_passes(self):
        corpus = json.loads((ROOT / 'examples/conformance/cases.json').read_text())
        result = conformance.check_corpus(corpus)
        self.assertEqual(result['fixtures_checked'], 26); self.assertEqual(result['evaluated_trace_pairs'], 12)
        for row in result['cases']:
            for execution in row['executions']:
                if execution['layer'] != 'offline_checker': self.assertEqual(execution['status'], 'not_run')
        for broken in (lambda trace: [], lambda trace: ['synthetic_reject_everything']):
            with self.assertRaises(ValueError): conformance.check_corpus(corpus, broken)
        altered = copy.deepcopy(corpus)
        altered['cases'][3]['trace_pair']['invalid'] = copy.deepcopy(altered['cases'][3]['trace_pair']['valid'])
        with self.assertRaises(ValueError): conformance.check_corpus(altered)


if __name__ == '__main__':
    unittest.main()
