#!/usr/bin/env python3
"""Run the offline suite and export counts, never raw diagnostics, for CI."""
import argparse
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from release_evidence import execute_suite, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--log', type=Path, required=True)
    args = parser.parse_args()
    for path in (args.output, args.log):
        if path.exists() or path.resolve() == ROOT or ROOT in path.resolve().parents:
            parser.error('Use new output/log paths outside source')
        path.parent.mkdir(parents=True, exist_ok=True)
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    with args.log.open('x') as stream:
        report = execute_suite(suite, stream)
    report['provenance'] = provenance(ROOT)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps({'successful': report['successful'], 'counts': report['counts']}))
    return 0 if report['successful'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
