"""Conservative public-text and reachable Git metadata checks; no network calls."""
import json
from pathlib import Path
import re
import shutil
import subprocess

EMAIL = re.compile(r"[\w.!#$%&*+/=?^`{|}~-]+@[\w.-]+\.[\w-]+", re.UNICODE)
PRIVATE_PATTERNS = [r"/Users/[\w.-]+/", r"[A-Z]:\\Users\\[\w.-]+\\",
                    r"AFPTEST-[A-Za-z0-9-]+", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]


def permitted_email(value):
    value = value.lower().strip('<> ')
    return (value.endswith('.invalid') or value.endswith('@users.noreply.github.com')
            or value in ('noreply@github.com', 'git@github.com'))


def decoded_text(text):
    # Also inspect JSON Unicode escapes without executing or fetching content.
    for _ in range(3):
        changed = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
        if changed == text:
            break
        text = changed
    return text


def check_text(text, label):
    text = decoded_text(text)
    if any(not permitted_email(v) for v in EMAIL.findall(text)):
        raise ValueError('Non-synthetic email candidate in ' + label)
    if any(re.search(pattern, text) for pattern in PRIVATE_PATTERNS):
        raise ValueError('Private-data candidate in ' + label)
    try:
        data = json.loads(text)
    except ValueError:
        return
    def inspect(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).lower().endswith('email') and isinstance(child, str) and '@' in child:
                    if not permitted_email(child):
                        raise ValueError('Non-synthetic structured email in ' + label)
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)
    inspect(data)


def git_output(root, *args):
    return subprocess.run(['git', '--no-pager', '-c', 'core.fsmonitor=false',
                           '-c', 'log.showSignature=false', '-C', str(root), *args],
                          capture_output=True, timeout=20)


def collect_git_metadata(root):
    root = Path(root)
    if not (root / '.git').exists() or not shutil.which('git'):
        return None
    rows = [git_output(root, 'log', '--all', '--format=%an%x00%ae%x00%cn%x00%ce%x00%B%x00'),
            git_output(root, 'for-each-ref', '--format=%(refname)%00%(taggername)%00%(taggeremail)%00%(contents)')]
    for row in rows:
        if row.returncode:
            raise ValueError('Git metadata inspection failed')
    return '\n'.join(row.stdout.decode('utf-8', 'strict').replace('\x00', '\n') for row in rows)


def check_git_metadata(root):
    text = collect_git_metadata(root)
    if text is None:
        return {'status': 'not_available', 'scope': 'reachable local Git metadata; no network or retained-object probe'}
    check_text(text, 'reachable Git metadata')
    return {'status': 'passed', 'scope': 'reachable local commit identities/messages and ref/tag metadata; not server erasure',
            'raw_values_exported': False}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = check_git_metadata(args.root)
        print(json.dumps(result))
        raise SystemExit(0 if result['status'] == 'passed' else 2)
    except (OSError, ValueError, subprocess.SubprocessError):
        print(json.dumps({'status': 'failed', 'code': 'METADATA_PRIVACY_CHECK_FAILED', 'raw_values_exported': False}))
        raise SystemExit(1)
