#!/usr/bin/env python3
"""Verify a blueprint plan.

Layout (v0.9.0): the plan is split for at-a-glance tracking —
  tasks.md     — `## Needs your attention` (if any) + `## Tasks` CHECKLIST
                 (one `- [ ] TASK-n — title` line per task, grouped by area).
  reference.md — `## Overview` … `## Task details` with the full `### TASK-n`
                 blocks (**Files**, `Done when:` shell proof, `Edge:`). The
                 `Done when:` proofs and `### TASK-n` anchors live HERE now.
A trivial spec may be a single `<spec>.md` holding both `## Tasks` and
`## Task details`.

FAIL (exit 1) on structural problems (missing sections/proofs, dangling refs,
old layout). WARN (still exit 0) on drift + style regressions toward the old
RFC-2119 / AC-N.N / Given-When-Then ceremony the skill moved away from.
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
    """TASK numbers from `- [ ] TASK-n` rows within the `## Tasks` section."""
    in_tasks, nums = False, set()
    for ln in text.splitlines():
        if ln.startswith("## Tasks"):
            in_tasks = True
            continue
        if in_tasks and ln.startswith("## ") and not ln.startswith("## Tasks"):
            in_tasks = False
        if in_tasks and (m := CHECK_ROW.match(ln)):
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

    # --- Handed the reference file directly → validate context + task-detail blocks, stop. ---
    if spec_name == "reference.md" or spec_path.endswith(".reference.md"):
        if "## Overview" not in content:
            errors.append("reference file missing ## Overview")
        is_product = "## User Stories" in content
        blocks = task_blocks(content)
        if "## Task details" in content and not blocks:
            errors.append("reference has '## Task details' but no `### TASK-n` blocks")
        check_detail_blocks(blocks, spec_name, errors, warnings, is_product)
        for k, n in sorted(section_group_dupes(content, "Task details").items()):
            warnings.append(f"group '▸ {k}' appears {n}× in ## Task details — each group once (split-area)")
        placeholder_and_dead([(spec_name, content)], content, errors)
        style_warnings([(spec_name, content)], warnings)
        report(errors, warnings, f"reference file: {len(blocks)} task blocks, "
                                 f"all with Files + a Done-when proof")

    # --- Otherwise: the tasks file (checklist). Resolve the reference. ---
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

    detail = ref_content if two_file else content        # where the `### TASK-n` blocks live
    detail_label = os.path.basename(ref_path) if two_file else spec_name
    files = [(spec_name, content)] + ([(detail_label, ref_content)] if two_file else [])

    # --- Old layout guard: `### TASK-n` blocks in the tasks file with no `## Task details`. ---
    if task_blocks(content) and "## Task details" not in content:
        errors.append("tasks file holds `### TASK-n` blocks directly — the current layout keeps a "
                      "`- [ ] TASK-n` checklist in tasks.md and moves the full `### TASK-n` detail to "
                      "reference.md `## Task details`. Migrate the plan (see blueprint).")
        report(errors, warnings, "old layout")

    # --- Required sections ---
    if "## Tasks" not in content:
        errors.append("tasks file missing required section: ## Tasks (the checklist)")
    if two_file:
        if "## Overview" not in ref_content:
            errors.append(f"{detail_label} missing ## Overview")
        if "## Task details" not in ref_content:
            errors.append(f"{detail_label} missing ## Task details (the `### TASK-n` blocks)")
    else:
        for sec in ("## Overview", "## Task details"):
            if sec not in content:
                errors.append(f"single-file spec missing required section: {sec}")

    is_product = "## User Stories" in content or "## User Stories" in detail
    has_requirements = "## Requirements" in detail or "## Contracts" in detail

    placeholder_and_dead(files, content + "\n" + ref_content, errors)

    # --- Task detail blocks: Files + Done when ---
    blocks = task_blocks(detail)
    if not blocks:
        errors.append(f"no `### TASK-n` blocks found in {detail_label} (expected under '## Task details')")
    check_detail_blocks(blocks, detail_label, errors, warnings, is_product)
    detail_nums = {num for num, _, _ in blocks}

    # --- Checklist ↔ detail cross-checks ---
    check_nums = checklist_nums(content)
    if not check_nums:
        errors.append("## Tasks has no `- [ ] TASK-n` checklist rows")
    for num in sorted(check_nums - detail_nums, key=int):
        errors.append(f"checklist TASK-{num} has no `### TASK-{num}` block in {detail_label} ## Task details")
    for num in sorted(detail_nums - check_nums, key=int):
        warnings.append(f"TASK-{num} has a detail block but is missing from the ## Tasks checklist")

    # --- Needs your attention: `→ blocks: TASK-n` must resolve (dangling = FAIL) ---
    if "## Needs your attention" in content:
        for i, line in enumerate(content.splitlines(), 1):
            m = re.search(r'(?:→|->)\s*blocks:\s*(.+)', line, re.IGNORECASE)
            if not m or re.search(r'\ball\b', m.group(1)):
                continue
            for num in re.findall(r'TASK-(\d+)', m.group(1)):
                if num not in check_nums and num not in detail_nums:
                    errors.append(f"{spec_name} line {i}: '## Needs your attention' blocks a "
                                  f"non-existent TASK-{num}")

    # --- Split-area (each group once) in checklist and in details (WARN) ---
    for txt, lbl, sec in [(content, spec_name, "Tasks"), (detail, detail_label, "Task details")]:
        for k, n in sorted(section_group_dupes(txt, sec).items()):
            warnings.append(f"group '▸ {k}' appears {n}× in {lbl} ## {sec} — each area/story "
                            "group should appear exactly once (split-area bug)")

    # --- One attention surface: no blocking duplication / old heading in reference (WARN) ---
    if two_file:
        if re.search(r'❓\s*\*{0,2}\s*NEEDS YOU', ref_content):
            warnings.append(f"{detail_label} carries a blocking '❓ NEEDS YOU' — keep blockers only in "
                            "tasks.md '## Needs your attention' (one attention surface)")
        if "## Assumptions & open questions" in ref_content:
            warnings.append(f"{detail_label} uses old heading '## Assumptions & open questions' — "
                            "rename to '## Assumptions' (ranked, non-blocking only)")

    if is_product and not has_requirements:
        warnings.append("Product spec has '## User Stories' but no '## Requirements' section")

    style_warnings(files, warnings)

    mode = "product" if is_product else "technical/small"
    report(errors, warnings, f"{len(blocks)} task blocks ({len(check_nums)} in checklist), {mode} mode "
                             "— all blocks have Files + a Done-when proof")


if __name__ == "__main__":
    main()
