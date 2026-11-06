#!/usr/bin/env python3
"""Port the vale-cli/Microsoft rule pack to Weir.

Reads the Vale YAML rules and writes a weirpack directory plus a TOML
fragment for the checks Weir cannot express.

    python3 make_weirpack.py <vale-styles-dir> <output-repo-dir>
"""
import collections
import json
import pathlib
import re
import sys

import yaml

# Terms harper already has a rule for, measured two ways: a rule named after
# the phrase, and a probe sentence it already flags. Skipped so the pack does
# not report the same fault twice alongside harper's own.
ALREADY_IN_HARPER = {
    'cannot', 'did not', '24/7', 'double-click on', 'keypress',
    'all of a sudden', 'except when', 'in lieu of', 'some of the',
    'a ISP', 'anti-malware', 'anti-virus', 'gb', 'matrixes',
    'this day and age',
}

KIND = {
    'BiasFree': 'Usage',
    'Contractions': 'Style',
    'Foreign': 'Style',
    'GenderBias': 'Usage',
    'Jargon': 'Style',
    'Militaristic': 'Usage',
    'Terms': 'Usage',
    'URLFormat': 'Usage',
    'Wordiness': 'Style',
}

LEVEL = {'error': 'error', 'warning': 'warning', 'suggestion': 'hint'}


def is_regex(s):
    return bool(re.search(r'[\\\[\]()?*+|^$]', s))


def camel(s):
    return ''.join(p[:1].upper() + p[1:]
                   for p in re.findall(r'[A-Za-z0-9]+', s)) or 'Rule'


def main(styles_dir, out_dir):
    styles = pathlib.Path(styles_dir)
    out = pathlib.Path(out_dir)
    rules_dir = out / 'rules'
    rules_dir.mkdir(parents=True, exist_ok=True)

    weir, house, skipped = {}, [], []

    for f in sorted(styles.glob('*.yml')):
        d = yaml.safe_load(f.read_text())
        name, kind = f.stem, d.get('extends')
        level = LEVEL.get(d.get('level', 'warning'), 'warning')
        msg = d.get('message', '')
        desc = d.get('description') or f'Microsoft Writing Style Guide: {name}.'
        exceptions = d.get('exceptions') or []
        ignorecase = bool(d.get('ignorecase'))

        if kind == 'substitution':
            groups = collections.defaultdict(list)
            for k, v in (d.get('swap') or {}).items():
                if k.lower() in ALREADY_IN_HARPER:
                    skipped.append((name, k, 'harper has it'))
                    continue
                # Weir expressions are words, punctuation and tags. A
                # numeral is none of those -- `12:00 noon` fails to parse
                # with `UnsupportedToken("12")` -- so it falls back to a
                # pattern, which can still carry the correction.
                if is_regex(k) or re.search(r'\d', k):
                    house.append(dict(name=f'{name}-{camel(k)[:18]}', level=level,
                                      message=msg.replace('%s', '%r', 1),
                                      patterns=[k], exceptions=exceptions,
                                      ignore_case=ignorecase,
                                      becomes=str(v).split('|')[0]))
                    skipped.append((name, k, 'regex, not expressible as words'))
                    continue
                groups[str(v)].append(k)
            for repl, froms in sorted(groups.items()):
                alts = sorted(set(froms), key=str.lower)
                expr = (f'({alts[0]})' if len(alts) == 1
                        else '[' + ', '.join(f'({a})' for a in alts) + ']')
                becomes = repl.split('|')
                line = (f'let becomes "{becomes[0]}"' if len(becomes) == 1
                        else 'let becomes [' + ', '.join(f'"{b}"' for b in becomes) + ']')
                # One rule can cover several wordings, so the message must
                # not name one of them: it would name the wrong one whenever
                # a different alternative matched. The reader is told what
                # was found separately.
                if len(alts) == 1:
                    message = msg.replace('%s', becomes[0], 1).replace('%s', alts[0])
                else:
                    head = msg.split('%s')[0].rstrip().rstrip("'\"` ")
                    message = f"{head} '{becomes[0]}' here." if head \
                        else f"Use '{becomes[0]}' here."
                rule = f'{name}{camel(becomes[0])}'
                weir[rule] = '\n'.join([
                    f'# Ported from vale-cli/Microsoft {f.name} (MIT).',
                    '# Generated -- see the README.',
                    '',
                    f'expr main {expr}',
                    '',
                    f'let message "{message}"',
                    f'let description "{desc}"',
                    f'let kind "{KIND.get(name, "Style")}"',
                    line,
                    '',
                    f'test "We should {alts[0]} today." "We should {becomes[0]} today."',
                ]) + '\n'
        elif kind == 'existence':
            tokens = [str(t) for t in (d.get('tokens') or [])]
            if not tokens:
                skipped.append((name, '', 'no tokens'))
                continue
            house.append(dict(name=name, level=level, message=msg,
                              patterns=tokens, exceptions=exceptions,
                              ignore_case=ignorecase, becomes=None))
        else:
            skipped.append((name, '', f'extends: {kind}'))

    for rule, body in weir.items():
        (rules_dir / f'{rule}.weir').write_text(body)
    (rules_dir / 'manifest.json').write_text(json.dumps({
        'author': 'markdoc-tools contributors, after vale-cli/Microsoft',
        'version': '0.1.0',
        'description': 'Microsoft Writing Style Guide corrections, as Weir rules.',
        'license': 'MIT',
        'website': 'https://github.com/vale-cli/Microsoft',
    }, indent=2) + '\n')

    def tq(s):
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

    def lq(s):
        return "'" + s + "'" if "'" not in s else tq(s)

    frag = ['''# The checks from the Microsoft pack that Weir cannot express, because
# Weir requires a `becomes` and these cannot say what to write instead.
#
# Paste into your markdoc-prose.toml. `%s` is the matched text, `%r` is
# `becomes`.
''']
    for r in sorted(house, key=lambda r: r['name']):
        frag += ['', '[[rule]]', f'name = {tq(r["name"])}',
                 f'level = {tq(r["level"])}', f'message = {tq(r["message"])}',
                 'patterns = [' + ', '.join(lq(p) for p in r['patterns']) + ']']
        if r.get('ignore_case'):
            frag.append('ignore_case = true')
        if r.get('exceptions'):
            frag.append('exceptions = [' + ', '.join(tq(e) for e in r['exceptions']) + ']')
        if r.get('becomes'):
            frag.append(f'becomes = {tq(r["becomes"])}')
    (out / 'house-rules.toml').write_text('\n'.join(frag) + '\n')

    print(f'{len(weir)} .weir rules')
    print(f'{len(house)} house rules')
    print(f'{len(skipped)} skipped')
    for n, t, why in skipped[:12]:
        print(f'  {n}: {t!r} -- {why}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
