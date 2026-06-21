#!/usr/bin/env python3
"""Verify a blueprint plan.

Layout: the plan lives in tasks.md (the reference holds only context) —
  tasks.md     — `## Needs your attention` (if any) + `## Checklist`
                 (one `- [ ] TASK-n — title` line per task, grouped by area)
                 + `## Tasks` (the full `### TASK-n` blocks below: **Files**,
                 `Done when:` shell proof, `Edge:`). The proofs + `### TASK-n`
                 anchors live HERE.
  reference.md — context only: `## Overview` / `## Requirements` /
                 `## Assumptions` / `## Risks` / `## Non-goals`. NO task blocks.
A trivial spec may be a single `<spec>.md` holding everything.

FAIL (exit 1) on structural problems (missing sections/proofs, dangling refs,
checklist↔block mismatch, the old "blocks-in-reference" layout). WARN (still
exit 0) on drift + style regressions toward the old ceremony.
"""
import sys
import re
import os


TASK_HDR = re.compile(r'^### TASK-(\d+)')
CHECK_ROW = re.compile(r'\s*[-*]\s*\[[ xX]\]\s*\*{0,2}TASK-(\d+)')
GROUP_HDR = re.compile(r'▸\s*((?:AREA|US)-\d+)')


def task_blocks(text):
    """Return [(num, block_text, line_no)] for each `### TASK-n` block in text."""
    lines = text.splitlines()
    starts = [(i, m.group(1)) for i, ln in enumerate(lines) if (m := TASK_HDR.match(ln))]
    out = []
    for idx, (ln, num) in enumerate(starts):
        end = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)
        out.append((num, "\n".join(lines[ln:end]), ln + 1))
    return out


def section_group_dupes(text, section):
    """Area/US group headers appearing >1× within a `## <section>` block."""
    in_sec, seen = False, {}
    for ln in text.splitlines():
        if ln.startswith("## " + section):
            in_sec = True
            continue
        if in_sec and ln.startswith("## ") and not ln.startswith("## " + section):
            in_sec = False
        if in_sec and (m := GROUP_HDR.search(ln)):
            seen[m.group(1)] = seen.get(m.group(1), 0) + 1
    return {k: n for k, n in seen.items() if n > 1}


def checklist_nums(text):
    """TASK numbers from `- [ ] TASK-n` rows within the `## Checklist` section."""
    in_sec, nums = False, set()
    for ln in text.splitlines():
        if ln.startswith("## Checklist"):
            in_sec = True
            continue
        if in_sec and ln.startswith("## ") and not ln.startswith("## Checklist"):
            in_sec = False
        if in_sec and (m := CHECK_ROW.match(ln)):
            nums.add(m.group(1))
    return nums


def check_detail_blocks(blocks, label, errors, warnings, is_product):
    for num, block, line in blocks:
        tid = f"TASK-{num}"
        if "**Files**:" not in block and "**Files:**" not in block:
            errors.append(f"{tid} ({label} line {line}): missing **Files:** field")
        if not re.search(r'Done when:.*`[^`]+`', block, re.IGNORECASE | re.DOTALL):
            errors.append(f"{tid} ({label} line {line}): missing a `Done when:` line with a "
                          "backticked shell command")
        if is_product and "**Covers**:" not in block and "**Covers:**" not in block:
            warnings.append(f"{tid} ({label} line {line}): product task has no **Covers:** "
                            "link to a requirement")


def placeholder_and_dead(files, scan, errors):
    for fname, ftext in files:
        for i, line in enumerate(ftext.splitlines(), 1):
            for marker in ("[NEEDS CLARIFICATION]", "TBD", "<insert here>"):
                if marker in line:
                    errors.append(f"{fname} line {i}: unresolved placeholder {marker!r}: "
                                  f"{line.strip()[:70]}")
            if re.search(r'\[P\]', line):
                errors.append(f"{fname} line {i}: stray [P] parallel marker (execute pipeline removed)")
    if "## Execution Order" in scan:
        errors.append("Dead section '## Execution Order' present (execute pipeline removed in v2.0)")


def style_warnings(files, warnings):
    style = [
        (r'\bMUST\b|\bSHOULD\b|\bMAY\b', "RFC-2119 keyword (use [must]/[nice]/[later])"),
        (r'\bAC-\d', "AC-N.N numbering (use a plain `Done when:` line)"),
        (r'^\s*(Given|When|Then):', "Given/When/Then scaffolding (collapse into `Done when:`)"),
        (r'^\s*Proof:', "`Proof:` label (fold the command into `Done when:`)"),
        (r'\bFR-\d{3}\b', "FR-NNN id (plain requirements + [tags] preferred)"),
    ]
    for fname, ftext in files:
        for i, line in enumerate(ftext.splitlines(), 1):
            for pat, msg in style:
                if re.search(pat, line):
                    warnings.append(f"{fname} line {i}: old-format {msg}: {line.strip()[:60]}")
                    break


def report(errors, warnings, ok_detail):
    if warnings:
        print(f"{len(warnings)} style warning(s) (non-blocking):")
        for w in warnings:
            print(f"  ~ {w}")
        print()
    if not errors:
        print(f"PASS: {ok_detail}")
        sys.exit(0)
    print(f"FAIL: {len(errors)} issue(s) found:\n")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tasks-file | spec-file | reference-file>")
        sys.exit(2)

    spec_path = sys.argv[1]
    with open(spec_path) as f:
        content = f.read()

    errors, warnings = [], []
    spec_name = os.path.basename(spec_path)
    spec_dir = os.path.dirname(spec_path)
    base = spec_path[:-3] if spec_path.endswith(".md") else spec_path

    # --- Handed the reference file directly → validate it's context-only, stop. ---
    if spec_name == "reference.md" or spec_path.endswith(".reference.md"):
        if "## Overview" not in content:
            errors.append("reference file missing ## Overview")
        if task_blocks(content):
            errors.append("reference file contains `### TASK-n` blocks — task blocks belong in "
                          "tasks.md `## Tasks`, not the reference")
        if "## Task details" in content:
            warnings.append("reference has a '## Task details' section — task detail moved to "
                            "tasks.md `## Tasks`")
        style_warnings([(spec_name, content)], warnings)
        report(errors, warnings, "reference file (context) looks well-formed")

    # --- Otherwise: the tasks file. Resolve the (context-only) reference. ---
    ref_candidates = []
    if spec_name == "tasks.md":
        ref_candidates.append(os.path.join(spec_dir, "reference.md"))   # directory form
    ref_candidates.append(base + ".reference.md")                       # legacy sibling form
    ref_path = next((p for p in ref_candidates if os.path.exists(p)), ref_candidates[0])
    two_file = os.path.exists(ref_path)
    ref_content = ""
    if two_file:
        with open(ref_path) as rf:
            ref_content = rf.read()

    files = [(spec_name, content)] + ([(os.path.basename(ref_path), ref_content)] if two_file else [])

    # --- Old "blocks in reference" layout guard (v0.9–v0.10) → clear migrate error. ---
    if two_file and ("## Task details" in ref_content or task_blocks(ref_content)):
        errors.append(f"{os.path.basename(ref_path)} holds task blocks (`## Task details` / `### TASK-n`) "
                      "— the current layout keeps the full `### TASK-n` blocks in tasks.md `## Tasks` "
                      "(below the `## Checklist`) and reference.md is context-only. Migrate the plan.")
        report(errors, warnings, "old layout (blocks in reference)")

    # --- Required sections ---
    for sec in ("## Checklist", "## Tasks"):
        if sec not in content:
            errors.append(f"tasks file missing required section: {sec}")
    if two_file:
        if "## Overview" not in ref_content:
            errors.append(f"{os.path.basename(ref_path)} missing ## Overview")
    else:
        if "## Overview" not in content:
            errors.append("single-file spec missing required section: ## Overview")

    is_product = "## User Stories" in content
    has_requirements = "## Requirements" in content or "## Contracts" in content \
        or "## Requirements" in ref_content

    placeholder_and_dead(files, content + "\n" + ref_content, errors)

    # --- Task blocks (in tasks.md `## Tasks`): Files + Done when ---
    blocks = task_blocks(content)
    if not blocks:
        errors.append("no `### TASK-n` blocks found in tasks file `## Tasks`")
    check_detail_blocks(blocks, spec_name, errors, warnings, is_product)
    block_nums = {num for num, _, _ in blocks}

    # --- Checklist ↔ block cross-checks ---
    check_nums = checklist_nums(content)
    if not check_nums:
        errors.append("`## Checklist` has no `- [ ] TASK-n` rows")
    for num in sorted(check_nums - block_nums, key=int):
        errors.append(f"checklist TASK-{num} has no `### TASK-{num}` block in `## Tasks`")
    for num in sorted(block_nums - check_nums, key=int):
        warnings.append(f"TASK-{num} has a block but is missing from the `## Checklist`")

    # --- Needs your attention: `→ blocks: TASK-n` must resolve (dangling = FAIL) ---
    if "## Needs your attention" in content:
        for i, line in enumerate(content.splitlines(), 1):
            m = re.search(r'(?:→|->)\s*blocks:\s*(.+)', line, re.IGNORECASE)
            if not m or re.search(r'\ball\b', m.group(1)):
                continue
            for num in re.findall(r'TASK-(\d+)', m.group(1)):
                if num not in check_nums and num not in block_nums:
                    errors.append(f"{spec_name} line {i}: '## Needs your attention' blocks a "
                                  f"non-existent TASK-{num}")

    # --- Split-area (each group once) in Checklist and Tasks (WARN) ---
    for sec in ("Checklist", "Tasks"):
        for k, n in sorted(section_group_dupes(content, sec).items()):
            warnings.append(f"group '▸ {k}' appears {n}× in ## {sec} — each area/story group "
                            "should appear exactly once (split-area bug)")

    # --- One attention surface: no blocking duplication / old heading in reference (WARN) ---
    if two_file:
        if re.search(r'❓\s*\*{0,2}\s*NEEDS YOU', ref_content):
            warnings.append(f"{os.path.basename(ref_path)} carries a blocking '❓ NEEDS YOU' — keep "
                            "blockers only in tasks.md '## Needs your attention'")
        if "## Assumptions & open questions" in ref_content:
            warnings.append(f"{os.path.basename(ref_path)} uses old heading "
                            "'## Assumptions & open questions' — rename to '## Assumptions'")

    if is_product and not has_requirements:
        warnings.append("Product spec has '## User Stories' but no '## Requirements' section")

    style_warnings(files, warnings)

    mode = "product" if is_product else "technical/small"
    report(errors, warnings, f"{len(blocks)} task blocks ({len(check_nums)} in checklist), {mode} mode "
                             "— all blocks have Files + a Done-when proof")


if __name__ == "__main__":
    main()
