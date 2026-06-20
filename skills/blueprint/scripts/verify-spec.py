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

    # Plan layout, in resolution order:
    #   directory form (v0.7.0 default): <spec-stem>/tasks.md + <spec-stem>/reference.md
    #   legacy sibling form:             <base>.md      + <base>.reference.md
    #   single-file:                     <spec>.md      (reference sections folded in)
    base = spec_path[:-3] if spec_path.endswith(".md") else spec_path
    spec_dir = os.path.dirname(spec_path)
    spec_name = os.path.basename(spec_path)

    # If handed the reference file directly, validate it as context-only and stop.
    if spec_name == "reference.md" or spec_path.endswith(".reference.md"):
        if "## Overview" not in content:
            print("FAIL: reference file missing ## Overview")
            sys.exit(1)
        print("PASS: reference file (context) looks well-formed")
        sys.exit(0)

    ref_candidates = []
    if spec_name == "tasks.md":                       # directory form
        ref_candidates.append(os.path.join(spec_dir, "reference.md"))
    ref_candidates.append(base + ".reference.md")     # legacy sibling form
    ref_path = next((p for p in ref_candidates if os.path.exists(p)), ref_candidates[0])
    two_file = os.path.exists(ref_path)

    ref_content = ""
    if two_file:
        with open(ref_path) as rf:
            ref_content = rf.read()

    # --- Required sections (structural) ---
    #   two-file mode: Overview/Requirements live in the reference → require only ## Tasks here
    #   single-file mode: require both
    required = ["## Tasks"] if two_file else ["## Overview", "## Tasks"]
    for section in required:
        if section not in content:
            errors.append(f"Missing required section: {section}")
    if two_file and "## Overview" not in ref_content:
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

    # --- Navigation layer: `## Needs your attention` + `## Task index` (v0.8.0) ---
    real_task_nums = {m.group(1) for _, tid in task_starts
                      if (m := re.search(r'TASK-(\d+)', tid))}

    # Blocking `→ blocks: TASK-n` references must point at a real task (dangling = FAIL:
    # a builder acting on a phantom blocker is a real defect). `→ blocks: all` is allowed.
    if "## Needs your attention" in content:
        for i, line in enumerate(lines, 1):
            m = re.search(r'(?:→|->)\s*blocks:\s*(.+)', line, re.IGNORECASE)
            if not m or re.search(r'\ball\b', m.group(1)):
                continue
            for num in re.findall(r'TASK-(\d+)', m.group(1)):
                if num not in real_task_nums:
                    errors.append(f"Line {i}: '## Needs your attention' blocks a non-existent TASK-{num}")

    # Task index rows (`- [ ] TASK-n`) should resolve, and every block should be indexed (WARN — drift).
    if "## Task index" in content:
        index_nums, in_index = set(), False
        index_row = re.compile(r'\s*[-*]\s*\[[ xX]\]\s*\*{0,2}TASK-(\d+)')
        for i, line in enumerate(lines, 1):
            if line.startswith("## Task index"):
                in_index = True
                continue
            if in_index and line.startswith("## "):
                in_index = False
            if in_index and (m := index_row.match(line)):
                index_nums.add(m.group(1))
                if m.group(1) not in real_task_nums:
                    warnings.append(f"Line {i}: task index lists TASK-{m.group(1)} with no '### TASK-{m.group(1)}' block")
        for num in sorted(real_task_nums - index_nums, key=int):
            warnings.append(f"TASK-{num} has a block but is missing from the '## Task index'")

    # Each `▸ AREA-n` / `▸ US-n` group header should appear once within ## Tasks (WARN — split-area bug).
    if "## Tasks" in content:
        in_tasks, seen_groups = False, {}
        group_re = re.compile(r'▸\s*((?:AREA|US)-\d+)')
        for line in lines:
            if line.startswith("## Tasks"):
                in_tasks = True
                continue
            if in_tasks and line.startswith("## ") and not line.startswith("## Tasks"):
                in_tasks = False
            if in_tasks and (m := group_re.search(line)):
                seen_groups[m.group(1)] = seen_groups.get(m.group(1), 0) + 1
        for key, n in sorted(seen_groups.items()):
            if n > 1:
                warnings.append(f"group header '▸ {key}' appears {n}× within ## Tasks — each area/story "
                                "group should appear exactly once (split-area bug)")

    # One attention surface: blocking items must NOT be duplicated into the reference (WARN).
    if two_file:
        if re.search(r'❓\s*\*{0,2}\s*NEEDS YOU', ref_content):
            warnings.append(f"{os.path.basename(ref_path)} carries a blocking '❓ NEEDS YOU' — move it to "
                            "tasks.md '## Needs your attention' (one attention surface, no duplication)")
        if "## Assumptions & open questions" in ref_content:
            warnings.append(f"{os.path.basename(ref_path)} uses old heading '## Assumptions & open questions' "
                            "— rename to '## Assumptions' (ranked, non-blocking only)")

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
