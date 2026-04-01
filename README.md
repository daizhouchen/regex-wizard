# regex-wizard

> Turn plain language into battle-tested regular expressions -- with railroad diagrams and a live tester in your browser.

## Description

**regex-wizard** is an [OpenClaw](https://openclawskill.ai) skill that converts natural language descriptions into production-ready regular expressions. It goes beyond simple pattern generation: every regex comes with a color-coded SVG railroad diagram for visual comprehension, an interactive HTML test page for instant validation, and copy-paste code snippets for your target programming language. The skill ships with a curated library of 15 common patterns covering email addresses, URLs, phone numbers, dates, IP addresses, and more.

## Features

- **Natural Language to Regex** -- describe what you want to match in Chinese or English and receive a complete regex with engine compatibility annotations and flag explanations.
- **SVG Railroad Diagrams** -- `scripts/railroad.py` parses any regex into an AST and renders a color-coded SVG diagram with a built-in legend, start/end markers, and arrow connectors.
- **Interactive HTML Test Page** -- `assets/tester_template.html` provides a dark-themed, responsive browser app with real-time match highlighting, capture group inspection, flag toggles (g/i/m/s), and a pass/fail test-case runner.
- **Multi-Language Code Snippets** -- ready-to-use examples in Python and JavaScript by default, with additional languages (Go, Java, Rust) on request.
- **Common Pattern Library** -- 15 pre-built, validated patterns for frequent matching tasks, embedded directly in `SKILL.md`.

## Installation

```bash
npx @anthropic-ai/claw@latest skill add daizhouchen/regex-wizard
```

## Quick Start

Ask in natural language -- the skill triggers automatically:

```
"Help me write a regex to extract all email addresses from a log file"

"写一个匹配中国手机号的正则表达式"

"I need a pattern for YYYY-MM-DD dates"
```

Generate a railroad diagram from the command line:

```bash
python3 scripts/railroad.py "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" -o email.svg
```

Run the full test suite:

```bash
python3 scripts/test_skill.py
```

## Railroad Diagrams

The diagram generator (`scripts/railroad.py`) parses a regex string into an AST, then renders each node as a colored SVG element. A legend is included at the bottom of every diagram.

### Color Coding

| Color  | Hex       | Represents        | Example               |
|--------|-----------|--------------------|------------------------|
| Blue   | `#4A90D9` | Literals           | `abc`, `@`, `.`        |
| Green  | `#27AE60` | Character classes  | `[a-z]`, `\d`, `\w`, `.` (any char) |
| Orange | `#E67E22` | Quantifiers        | `*`, `+`, `?`, `{2,4}` |
| Purple | `#8E44AD` | Groups             | `(...)`, `(?:...)`, `(?P<name>...)` |
| Red    | `#E74C3C` | Anchors            | `^`, `$`, `\b`        |
| Grey   | `#95A5A6` | Alternation        | `a\|b` branch paths   |

Diagrams include a filled start circle, directional arrows between nodes, and a double-ring end circle, following standard railroad notation.

## Interactive Tester

The HTML test page (`assets/tester_template.html`) is a self-contained, zero-dependency browser app with the following capabilities:

- **Real-time highlighting** -- matches are underlined with `<mark>` elements as you type, using a synchronized backdrop overlay.
- **Flag toggles** -- click buttons to enable/disable `g` (global), `i` (case-insensitive), `m` (multiline), and `s` (dotAll) flags.
- **Match list with groups** -- each match displays its index, value, numbered capture groups, and named groups.
- **Test-case runner** -- pre-populated with 5 positive and 5 negative cases; each shows a green (pass) or red (fail) indicator. Click any case to load it into the test area.
- **Error feedback** -- invalid regex patterns surface the browser engine error message inline.
- **Dark theme** -- gradient-accented dark UI (`#1a1a2e` background) with responsive layout via `@media` queries for mobile screens.

## Common Patterns Reference

These patterns are built into `SKILL.md` and can be used directly or adapted:

| Pattern            | Regex                                                                 | Notes                          |
|--------------------|-----------------------------------------------------------------------|--------------------------------|
| Email address      | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`                    | General-purpose email          |
| URL                | `https?://[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})(?:/[^\s]*)?`              | HTTP/HTTPS links               |
| Chinese mobile     | `1[3-9]\d{9}`                                                         | Mainland China 11-digit        |
| Landline phone     | `(?:0\d{2,3}-?)?\d{7,8}`                                             | Optional area code             |
| IPv4 address       | `(?:25[0-5]\|2[0-4]\d\|[01]?\d\d?)(?:\.(...)){3}`                    | 0.0.0.0 -- 255.255.255.255    |
| Date (YYYY-MM-DD)  | `\d{4}-(?:0[1-9]\|1[0-2])-(?:0[1-9]\|[12]\d\|3[01])`                | ISO 8601                       |
| Date (DD/MM/YYYY)  | `(?:0[1-9]\|[12]\d\|3[01])/(?:0[1-9]\|1[0-2])/\d{4}`                | European format                |
| Time (HH:MM:SS)    | `(?:[01]\d\|2[0-3]):[0-5]\d:[0-5]\d`                                 | 24-hour clock                  |
| Chinese characters | `[\u4e00-\u9fa5]+`                                                    | Contiguous CJK block           |
| National ID (CN)   | `[1-9]\d{5}(?:19\|20)\d{2}(?:0[1-9]\|1[0-2])(?:0[1-9]\|[12]\d\|3[01])\d{3}[\dXx]` | 18-digit second-gen ID |
| Postal code (CN)   | `[1-9]\d{5}`                                                          | 6-digit                       |
| Hex color          | `#(?:[0-9a-fA-F]{3}){1,2}`                                           | #RGB or #RRGGBB               |
| HTML tag pair      | `<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>.*?</\1>`                            | Simple matched tags            |
| Username           | `[a-zA-Z][a-zA-Z0-9_-]{2,15}`                                        | 3--16 chars, letter start      |
| Strong password    | `(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*]).{8,}`                | Mixed case + digit + symbol    |

## Supported Regex Constructs

| Construct          | Syntax Examples                    | Diagram Element     |
|--------------------|------------------------------------|---------------------|
| Literals           | `abc`, `@`                         | Blue box            |
| Character classes  | `[a-z]`, `\d`, `\w`, `\s`, `.`    | Green box           |
| Quantifiers        | `*`, `+`, `?`, `{n}`, `{n,m}`     | Orange badge        |
| Capture groups     | `(...)`, `(?P<name>...)`           | Purple dashed rect  |
| Non-capture groups | `(?:...)`                          | Purple dashed rect  |
| Lookahead          | `(?=...)`, `(?!...)`               | Purple dashed rect  |
| Lookbehind         | `(?<=...)`, `(?<!...)`             | Purple dashed rect  |
| Alternation        | `a\|b`                             | Branching paths     |
| Anchors            | `^`, `$`, `\b`, `\B`              | Red box             |

## Trigger Phrases

The skill activates when the user mentions any of these terms or describes a text-matching task:

| Language | Phrases                                              |
|----------|------------------------------------------------------|
| Chinese  | 正则, 匹配模式, 文本提取, 字符串匹配                 |
| English  | regex, regular expression, text extraction, string matching |
| Implicit | "怎么找出所有邮箱地址", "extract all dates from this file" |

## Project Structure

```
regex-wizard/
├── SKILL.md                      # Skill definition, workflow, and pattern library
├── README.md                     # This file
├── scripts/
│   ├── railroad.py               # Regex parser + SVG railroad diagram renderer
│   └── test_skill.py             # Automated test suite (5 scenarios, 118 assertions)
├── assets/
│   └── tester_template.html      # Interactive browser-based regex tester
└── test_output/                  # Pre-generated SVG diagrams
    ├── Email_address.svg
    ├── Chinese_phone_number.svg
    ├── URL.svg
    ├── Date_(YYYY-MM-DD).svg
    └── IPv4_address.svg
```

## Test Results

The test suite (`scripts/test_skill.py`) validates five common scenarios end-to-end:

- **118 / 118** assertions passed
- AST parsing, SVG generation, XML validity, regex positive/negative matching, and HTML template structure are all covered
- Test scenarios: Email, Chinese phone number, URL, Date (YYYY-MM-DD), IPv4

## Requirements

- Python 3.8+ (standard library only -- no external packages)

## Limitations

- The railroad diagram parser covers common regex syntax but does not handle every PCRE extension (e.g., recursive patterns, conditional sub-patterns).
- Engine differences exist: the interactive tester runs on the JavaScript (ECMAScript) engine, which may behave differently from PCRE, RE2, or Python's `re` module.
- The HTML test page is designed for single-pattern testing; it does not support multi-pattern batch validation.
- Unicode property escapes (`\p{...}`) are not visualized in railroad diagrams.

## Contributing

Contributions are welcome. Please open an issue or pull request on GitHub. When adding new built-in patterns, include positive and negative test cases in `scripts/test_skill.py`.

## License

MIT
