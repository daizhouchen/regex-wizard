# regex-wizard

> Describe what you want to match in plain language. Get a regex, a railroad diagram, and a live tester.

A [Claude Code](https://claude.ai/code) skill that generates regular expressions from natural language descriptions, with color-coded SVG railroad diagrams and an interactive browser-based test page.

## Features

- **Natural Language → Regex** — Describe patterns in plain Chinese or English
- **SVG Railroad Diagrams** — Color-coded visualization of regex structure
  - Blue = Literals
  - Green = Character classes
  - Orange = Quantifiers
  - Purple = Groups
  - Red = Anchors
- **Interactive Test Page** — Real-time match highlighting with capture group details
- **Multi-Language Code Snippets** — Usage examples for JS/Python/Go/Java
- **Common Patterns Reference** — 15+ pre-built patterns (email, URL, phone, IP, date, etc.)

## Installation

```bash
claude skill add daizhouchen/regex-wizard
```

## How It Works

1. Claude interprets your natural language description
2. Generates the regex with strict and lenient variants
3. `scripts/railroad.py` renders an SVG railroad diagram
4. Generates an interactive HTML tester with pre-populated test cases
5. Provides code snippets in your target language

## Manual Usage

```bash
# Generate a railroad diagram for any regex
python3 scripts/railroad.py "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$" -o email.svg

# Run the test suite (5 common patterns)
python3 scripts/test_skill.py
```

## Trigger Phrases

- "正则" / "regex" / "匹配模式"
- "怎么找出所有邮箱地址"
- "文本提取" / "字符串匹配"

## Project Structure

```
regex-wizard/
├── SKILL.md                    # Skill definition with patterns reference table
├── scripts/
│   ├── railroad.py             # Regex → SVG railroad diagram generator
│   └── test_skill.py           # Test suite for 5 common patterns
├── assets/
│   └── tester_template.html    # Interactive regex tester template
├── test_output/                # Pre-generated SVG diagrams
│   ├── Email_address.svg
│   ├── Chinese_phone_number.svg
│   ├── URL.svg
│   ├── Date_(YYYY-MM-DD).svg
│   └── IPv4_address.svg
└── README.md
```

## Supported Regex Constructs

| Construct | Example | Railroad Element |
|-----------|---------|-----------------|
| Literals | `abc` | Blue boxes |
| Character classes | `[a-z]`, `\d`, `\w` | Green boxes |
| Quantifiers | `*`, `+`, `{2,4}` | Orange loops |
| Groups | `(...)`, `(?:...)` | Purple containers |
| Alternation | `a\|b` | Branching paths |
| Anchors | `^`, `$` | Red markers |

## Requirements

- Python 3.8+ (no external packages)

## Test Results

- 118/118 tests passed
- 5 regex patterns validated (email, phone, URL, date, IP)
- All SVGs verified as valid XML

## License

MIT
