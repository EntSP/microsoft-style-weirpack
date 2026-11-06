# microsoft-style-weirpack

The [Microsoft Writing Style Guide][guide] rules, as [Weir][weir] rules that
[harper][harper] can run.

```
rules/            195 .weir rules + manifest.json — load as a weirpack
house-rules.toml  115 checks Weir cannot express, as patterns
port.py           regenerates both from the Vale pack
```

## Why

[harper][harper] ships around a thousand rules and none of them is this
guide. That is not an oversight — harper checks English, and a house style
guide is a different thing — but it leaves a gap for anyone moving a
documentation set off [Vale][vale], where the Microsoft pack is the usual
starting point.

**Measured, not assumed.** Of the 224 literal substitution terms in the Vale
pack, harper already handles **9** — counted two ways, by looking for a
harper rule named after the phrase and by feeding harper a sentence
containing it. The overlap is: `cannot`, `did not`, `24/7`,
`double-click on`, `keypress`, `all of a sudden`, `except when`,
`in lieu of`, `some of the`, plus the indefinite-article and prefix rules
that catch `a ISP` and `anti-virus`. Those are skipped here so the two do
not report the same fault twice.

## Two kinds of rule, because Weir requires a `becomes`

That requirement is right: a correction a tool cannot apply is one a writer
has to work out. It also means a check that only says "don't" cannot be a
Weir rule.

**`rules/`** — everything that can say what to write instead. 195 rules,
grouped by replacement, from `BiasFree`, `Contractions`, `Foreign`,
`GenderBias`, `Jargon`, `Militaristic`, `Terms`, `URLFormat` and
`Wordiness`.

**`house-rules.toml`** — the 35 existence checks (`Passive`, `Adverbs`,
`HeadingPunctuation`, `ExclamationPoints` …) plus the swaps whose left-hand
side is a regular expression or contains a numeral, which Weir expressions
cannot hold. `12:00 noon` fails to parse as `UnsupportedToken("12")`.

## Using it

With [markdoc-prose][tools]:

```toml
[engine]
weirpack = "path/to/microsoft-style-weirpack/rules"
```

and paste `house-rules.toml` into your own config. With `harper-cli`, zip
`rules/` into a `.weirpack` and pass `--weirpack`.

## Regenerating

```
python3 port.py <vale-Microsoft-styles-dir> .
```

Point it at a checkout of [vale-cli/Microsoft][pack]. The rules are
generated, so fix `port.py` rather than a `.weir` file.

## Quality, honestly

The rules are a mechanical port and their tests are generated — one
`test` per rule, of the form the phrase appears in. That is enough to prove
the rule parses and fires, and it is not the hand-written corpus of `test`
and `allows` cases harper's own rules carry. Treat this as a working
starting point rather than a finished rule set: a rule that matters to you
is worth hand-editing, and the good ones are worth proposing upstream to
harper where everybody gets them.

A grouped rule names only its replacement — "Consider using 'to' here." —
because one rule covers several wordings and naming one of them would name
the wrong one whenever a different alternative matched. What was actually
found is reported alongside.

## Licence

MIT. A port of [vale-cli/Microsoft][pack], also MIT, which is itself
"neither maintained nor endorsed by Microsoft". No affiliation with or
endorsement by Microsoft is claimed. See [LICENSE](LICENSE).

[guide]: https://learn.microsoft.com/en-us/style-guide/welcome/
[weir]: https://writewithharper.com/docs/weir
[harper]: https://writewithharper.com
[vale]: https://vale.sh
[pack]: https://github.com/vale-cli/Microsoft
[tools]: https://github.com/markdoc-tools/markdoc-tools
