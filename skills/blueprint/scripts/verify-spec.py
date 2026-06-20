#!/usr/bin/env python3
"""Verify a blueprint spec: required sections, every task has Files + a `Done when:`
shell proof, no unresolved markers, and no leftover old-pipeline ceremony.

FAIL (exit 1) on structural problems. WARN (still exit 0) on style regressions
toward the old RFC-2119 / AC-N.N / Given-When-Then format the skill moved away from.
"""
import sys
import re
import os


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <spec-file>")
        sys.exit(2)

    spec_path = sys.argv[1]
    with open(spec_path) as f:
        content = f.read()
        lines = content.splitlines()

    errors = []
    warnings = []

    # Two-file layout (Part D): tasks file <base>.md + a sibling <base>.reference.md.
    base = spec_path[:-3] if spec_path.endswith(".md") else spec_path
    ref_path = base + ".reference.md"

    # If handed the reference file directly, validate it as context-only and stop.
    if spec_path.endswith(".reference.md"):
        if "## Overview" not in content:
            print("FAIL: reference file missing ## Overview")
            sys.exit(1)
        print("PASS: reference file (context) looks well-formed")
        sys.exit(0)

    two_file = os.path.exists(ref_path)

    # --- Required sections (structural) ---
    #   two-file mode: Overview/Requirements live in the reference → require only ## Tasks here
    #   single-file mode: require both
    required = ["## Tasks"] if two_file else ["## Overview", "## Tasks"]
    for section in required:
        if section not in content:
            errors.append(f"Missing required section: {section}")
    if two_file:
        with open(ref_path) as rf:
            if "## Overview" not in rf.read():
                errors.append(f"reference file {os.path.basename(ref_path)} missing ## Overview")

    # Product specs (user stories or a Requirements section) — recommend linkage
    is_product = bool(re.search(r'^## User Stories', content, re.MULTILINE))
    has_requirements = "## Requirements" in content or "## Contracts" in content

    # --- No unresolved clarification markers (structural) ---
    for i, line in enumerate(lines, 1):
        for marker in ("[NEEDS CLARIFICATION]", "TBD", "<insert here>"):
            if marker in line:
                errors.append(f"Line {i}: unresolved placeholder {marker!r}: {line.strip()[:80]}")

    # --- Dead old-pipeline constructs (structural — execute orchestration is gone) ---
    if "## Execution Order" in content:
        errors.append("Dead section '## Execution Order' present (execute pipeline removed in v2.0)")
    for i, line in enumerate(lines, 1):
        if re.search(r'\[P\]', line):
            errors.append(f"Line {i}: stray [P] parallel marker (execute pipeline removed)")

    # --- Tasks: each block needs **Files** and a `Done when:` with a shell command ---
    task_pattern = re.compile(r'^### TASK-(\d+)')
    task_starts = [(i, m.group(0)) for i, line in enumerate(lines)
                   if (m := task_pattern.match(line))]

    if not task_starts:
        errors.append("No '### TASK-{N}' blocks found")

    for idx, (start_line, task_id) in enumerate(task_starts):
        end_line = task_starts[idx + 1][0] if idx + 1 < len(task_starts) else len(lines)
        block = "\n".join(lines[start_line:end_line])

        if "**Files**:" not in block and "**Files:**" not in block:
            errors.append(f"{task_id} (line {start_line + 1}): missing **Files:** field")

        # The proof: a `Done when:` line containing a backticked command.
        done_when = re.search(r'Done when:.*`[^`]+`', block, re.IGNORECASE | re.DOTALL)
        if not done_when:
            errors.append(f"{task_id} (line {start_line + 1}): missing a `Done when:` line with a "
                          "backticked shell command")

        if is_product and "**Covers**:" not in block and "**Covers:**" not in block:
            warnings.append(f"{task_id} (line {start_line + 1}): product task has no **Covers:** "
                            "link to a requirement")

    if is_product and not has_requirements:
        warnings.append("Product spec has '## User Stories' but no '## Requirements' section")

    # --- Style regressions toward the old ceremony (warn, don't fail) ---
    style = [
        (r'\bMUST\b|\bSHOULD\b|\bMAY\b', "RFC-2119 keyword (use [must]/[nice]/[later] tags)"),
        (r'\bAC-\d', "AC-N.N numbering (use a plain `Done when:` line)"),
        (r'^\s*(Given|When|Then):', "Given/When/Then scaffolding (collapse into `Done when:`)"),
        (r'^\s*Proof:', "`Proof:` label (fold the command into `Done when:`)"),
        (r'\bFR-\d{3}\b', "FR-NNN id (optional now — plain requirements + [tags] preferred)"),
    ]
    for i, line in enumerate(lines, 1):
        for pat, msg in style:
            if re.search(pat, line):
                warnings.append(f"Line {i}: old-format {msg}: {line.strip()[:70]}")
                break

    # --- Report ---
    if warnings:
        print(f"{len(warnings)} style warning(s) (non-blocking):")
        for w in warnings:
            print(f"  ~ {w}")
        print()

    if not errors:
        mode = "product" if is_product else "technical/small"
        print(f"PASS: {len(task_starts)} tasks verified, all have Files + a Done-when proof "
              f"({mode} mode)")
        sys.exit(0)

    print(f"FAIL: {len(errors)} issue(s) found:\n")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)


if __name__ == "__main__":
    main()
