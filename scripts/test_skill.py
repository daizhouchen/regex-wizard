#!/usr/bin/env python3
"""
Test the regex-wizard skill with 5 common scenarios.
Validates SVG output (valid XML) and HTML structure.
"""

import os
import sys
import xml.etree.ElementTree as ET

# Add parent dir so we can import railroad
sys.path.insert(0, os.path.dirname(__file__))
from railroad import generate_svg, _parse_alternation

SCENARIOS = [
    {
        "name": "Email address",
        "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "positive": ["user@example.com", "a.b+c@domain.co.uk", "test123@sub.domain.org",
                      "x@y.cc", "user%name@company.io"],
        "negative": ["@nouser.com", "user@.com", "user@com", "plaintext", "user@d.c"],
    },
    {
        "name": "Chinese phone number",
        "pattern": r"1[3-9]\d{9}",
        "positive": ["13812345678", "15900001111", "18699998888", "17012345678", "19911112222"],
        "negative": ["12345678901", "1381234567", "138123456789", "02812345678", "abcdefghijk"],
    },
    {
        "name": "URL",
        "pattern": r"https?://[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})(?:/[^\s]*)?",
        "positive": ["https://www.example.com", "http://sub.domain.org/path",
                      "https://a.io/x?q=1", "http://localhost.dev/foo/bar",
                      "https://example.com/path/to/page.html"],
        "negative": ["ftp://files.example.com", "not-a-url", "http://", "://missing.com",
                      "www.example.com"],
    },
    {
        "name": "Date (YYYY-MM-DD)",
        "pattern": r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])",
        "positive": ["2024-01-15", "2000-12-31", "1999-06-01", "2023-09-30", "2026-03-31"],
        "negative": ["2024-13-01", "2024-00-15", "24-01-15", "2024/01/15", "2024-01-32"],
    },
    {
        "name": "IPv4 address",
        "pattern": r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)(?:\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)){3}",
        "positive": ["192.168.1.1", "0.0.0.0", "255.255.255.255", "10.0.0.1", "172.16.254.100"],
        "negative": ["256.1.1.1", "1.2.3", "1.2.3.4.5", "abc.def.ghi.jkl", "999.999.999.999"],
    },
]

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test_output")
os.makedirs(OUT_DIR, exist_ok=True)

import re

passed = 0
failed = 0
errors = []


def check(condition, msg):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {msg}")
    else:
        failed += 1
        errors.append(msg)
        print(f"  FAIL: {msg}")


print("=" * 60)
print("regex-wizard skill tests")
print("=" * 60)

for sc in SCENARIOS:
    print(f"\n--- {sc['name']} ---")
    pattern = sc["pattern"]

    # 1. Parse the regex into AST (should not crash)
    try:
        ast = _parse_alternation(pattern)
        check(ast is not None, f"AST parse succeeds for {sc['name']}")
    except Exception as e:
        check(False, f"AST parse for {sc['name']}: {e}")
        continue

    # 2. Generate SVG
    try:
        svg_str = generate_svg(pattern)
        check(len(svg_str) > 100, f"SVG generated ({len(svg_str)} bytes)")
    except Exception as e:
        check(False, f"SVG generation for {sc['name']}: {e}")
        continue

    # 3. Validate SVG is valid XML
    try:
        ET.fromstring(svg_str)
        check(True, "SVG is valid XML")
    except ET.ParseError as e:
        check(False, f"SVG XML parse error: {e}")
        # Write to file for debugging
        debug_path = os.path.join(OUT_DIR, f"{sc['name'].replace(' ', '_')}_debug.svg")
        with open(debug_path, "w") as f:
            f.write(svg_str)
        print(f"    Debug SVG written to: {debug_path}")

    # 4. Check SVG has expected elements
    check("<svg" in svg_str, "SVG has <svg> root")
    check("xmlns" in svg_str, "SVG has xmlns attribute")
    check("<rect" in svg_str, "SVG contains rect elements")
    check("<text" in svg_str, "SVG contains text elements")

    # 5. Write SVG to file
    svg_path = os.path.join(OUT_DIR, f"{sc['name'].replace(' ', '_')}.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_str)
    check(os.path.exists(svg_path), f"SVG file written: {svg_path}")

    # 6. Validate regex against test cases
    compiled = re.compile(pattern)
    for pos in sc["positive"]:
        match = compiled.search(pos)
        check(match is not None, f"Positive match: '{pos}'")
    for neg in sc["negative"]:
        match = compiled.fullmatch(neg)
        check(match is None, f"Negative reject: '{neg}'")


# Test HTML template
print("\n--- HTML Template Validation ---")
html_path = os.path.join(os.path.dirname(__file__), "..", "assets", "tester_template.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

check("<!DOCTYPE html>" in html_content, "HTML has doctype")
check("<html" in html_content, "HTML has root element")
check('id="regexInput"' in html_content, "Has regex input field")
check('id="testInput"' in html_content, "Has test text area")
check('id="matchCount"' in html_content, "Has match count display")
check('id="matchList"' in html_content, "Has match list display")
check('id="testCases"' in html_content, "Has test cases container")
check("flag-btn" in html_content, "Has flag toggle buttons")
check('data-flag="g"' in html_content, "Has global flag")
check('data-flag="i"' in html_content, "Has case-insensitive flag")
check('data-flag="m"' in html_content, "Has multiline flag")
check('data-flag="s"' in html_content, "Has dotAll flag")
check("dark" in html_content.lower() or "#1a1a2e" in html_content, "Has dark theme")
check("@media" in html_content, "Has responsive design")
check("DEFAULT_TEST_CASES" in html_content, "Has pre-populated test cases")
check(html_content.count("expect: true") >= 5, "Has 5+ positive test cases")
check(html_content.count("expect: false") >= 5, "Has 5+ negative test cases")
check("matchAll" in html_content, "Uses matchAll for highlighting")
check("<mark>" in html_content, "Uses mark element for highlighting")
check("groups" in html_content, "Shows capture group details")

# Test SKILL.md
print("\n--- SKILL.md Validation ---")
skill_path = os.path.join(os.path.dirname(__file__), "..", "SKILL.md")
with open(skill_path, "r", encoding="utf-8") as f:
    skill_content = f.read()

check("---" in skill_content, "SKILL.md has frontmatter delimiters")
check("name: regex-wizard" in skill_content, "Has skill name in frontmatter")
check("description:" in skill_content, "Has description in frontmatter")
check("邮箱" in skill_content or "email" in skill_content.lower(), "Pattern table: email")
check("URL" in skill_content or "url" in skill_content, "Pattern table: URL")
check("手机" in skill_content or "phone" in skill_content.lower(), "Pattern table: phone")
check("IP" in skill_content, "Pattern table: IP")
check("日期" in skill_content or "date" in skill_content.lower(), "Pattern table: date")

print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed")
if errors:
    print("Failures:")
    for e in errors:
        print(f"  - {e}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
