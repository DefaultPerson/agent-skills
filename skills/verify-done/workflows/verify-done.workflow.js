export const meta = {
  name: 'verify-done-gate',
  description: 'Plan-aware tiered acceptance gate: conformance + independent scenarios + advisory quality',
  phases: [
    { title: 'Tier1-Conformance', detail: 'run every Done-when proof + build/test/regression' },
    { title: 'Tier2-Scenarios', detail: 'generate scenarios from original intent, run the runnable ones' },
    { title: 'Tier3-Quality', detail: 'advisory maintainability pass (only if behaviour works)' },
    { title: 'Synthesis', detail: 'DONE / NOT-DONE + buckets' },
  ],
}

// ── args (rendered by SKILL.md) ──
//   doneWhenProofs : [{id, title, cmd}]    from the plan's `Done when:` lines, or derived
//                                          from an unstructured plan — may be [] (then Tier 1
//                                          falls back to build/test, else verdict leans on Tier 2)
//   buildCmd, testCmd, regressionCmd, coverageCmd : string|null
//   intentNotes    : ORIGINAL intent text (<spec>.reference.md, goal.md, or a plan-mode/inline plan) — Tier-2 grounding
//   deep           : bool  (--deep; default false = light)
//   blockOnQuality : bool  (--block-on-quality; default false = advisory)
//   qualityPrompt  : full text of roles/quality-review.md
//   sandboxKind    : 'worktree' | 'tmpdir' | 'none'
//   sandboxDir     : path to run proofs/scenarios in (or '.')
const a = args || {}
const deep = !!a.deep
const sandbox = a.sandboxKind || 'none'
const where = a.sandboxDir || '.'

const PROOF = {
  type: 'object', additionalProperties: false,
  required: ['id', 'verdict', 'evidence'],
  properties: {
    id: { type: 'string' },
    verdict: { type: 'string', enum: ['PASS', 'FAIL', 'UNKNOWN'] },
    evidence: { type: 'string', description: 'cmd + exit code + last lines, or why UNKNOWN' },
  },
}
const SCEN = {
  type: 'object', additionalProperties: false,
  required: ['scenario', 'risk', 'category', 'verdict', 'confidence', 'evidence', 'groundedIn'],
  properties: {
    scenario: { type: 'string' },
    risk: { type: 'string', enum: ['high', 'med', 'low'] },
    category: { type: 'string', enum: ['user-case', 'edge', 'adversarial'] },
    verdict: { type: 'string', enum: ['PASS', 'FAIL', 'UNKNOWN'] },
    confidence: { type: 'string', enum: ['high', 'med', 'low'] },
    evidence: { type: 'string' },
    groundedIn: { type: 'string', description: 'quote/ref from the original intent' },
  },
}
const SCEN_GEN = {
  type: 'object', additionalProperties: false,
  required: ['scenarios', 'discarded'],
  properties: {
    scenarios: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['scenario', 'risk', 'category', 'runnable', 'groundedIn'],
        properties: {
          scenario: { type: 'string' },
          risk: { type: 'string', enum: ['high', 'med', 'low'] },
          category: { type: 'string', enum: ['user-case', 'edge', 'adversarial'] },
          runnable: { type: 'boolean', description: 'can this be executed with a shell/test command here?' },
          groundedIn: { type: 'string', description: 'quote/ref from the original intent (REQUIRED — ungrounded ⇒ discard)' },
        },
      },
    },
    discarded: { type: 'integer', description: 'count of candidate scenarios dropped as ungrounded/out-of-scope' },
  },
}
const QUALITY = {
  type: 'object', additionalProperties: false,
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['severity', 'category', 'location', 'finding', 'remedy'],
        properties: {
          severity: { type: 'string', enum: ['high', 'med', 'low'] },
          category: { type: 'string', enum: ['file-size', 'spaghetti', 'indirection', 'type-boundary', 'layer-leak', 'orchestration', 'duplication'] },
          location: { type: 'string' },
          finding: { type: 'string' },
          remedy: { type: 'string' },
        },
      },
    },
  },
}

const RAILS = `Honesty rails (mandatory):
- UNKNOWN ≠ pass and ≠ fail. If you cannot actually run the check here (no runnable env / missing deps / server down), return verdict "UNKNOWN" with the reason — never guess PASS or FAIL.
- Quote real output as evidence. No command run ⇒ UNKNOWN.`

const proofPrompt = (p) => `You are verifying ONE acceptance proof of an already-built change, in: ${where} (sandbox: ${sandbox}).
Task: ${p.title || p.id}
Run exactly this and judge it: \`${p.cmd}\`
Return PASS if it succeeds as intended, FAIL if it fails, UNKNOWN if it can't be run here. Use id "${p.id}".
${RAILS}`

const suitePrompt = (cmd) => `Run the project check \`${cmd}\` in ${where} (sandbox: ${sandbox}) and report PASS/FAIL/UNKNOWN with the tail of its output as evidence. Use id "${cmd}".
${RAILS}`

const genPrompt = (notes) => `You generate acceptance SCENARIOS to test whether a built change actually works for real usage — independently of the task list (which may have blind spots).

ORIGINAL INTENT (ground every scenario in THIS — not in a task list):
"""
${notes || '(none provided — generate only what the change visibly implies; be conservative)'}
"""

Rules:
- Generate ${deep ? 'a thorough set across all requirements + adversarial inputs' : 'a LIGHT set: only the top high/med-risk user-cases + a couple of edge/adversarial cases'}.
- Every scenario MUST be grounded: put a quote/reference from the ORIGINAL INTENT in groundedIn. Do NOT invent requirements the intent never stated — drop those and count them in "discarded".
- Mark "runnable": true only if it can be checked here with a shell/test command (sandbox: ${sandbox}; "${where}").
- Rank by risk. Categories: user-case / edge / adversarial.`

const runPrompt = (s) => `Execute this acceptance scenario against the built change in ${where} (sandbox: ${sandbox}) and judge it:
SCENARIO: ${s.scenario}
(grounded in: ${s.groundedIn}; risk ${s.risk}; ${s.category})
Return PASS/FAIL/UNKNOWN + evidence + your confidence. A FAIL that merely reflects a feature the intent never asked for is NOT a fail — return UNKNOWN with confidence low and note "out-of-scope, confirm with human".
${RAILS}`

// ── Tier 1 — Conformance ──
phase('Tier1-Conformance')
const proofs = a.doneWhenProofs || []
const suites = [a.buildCmd, a.testCmd, a.regressionCmd, a.coverageCmd].filter(Boolean)
const t1 = (await parallel([
  ...proofs.map((p) => () => agent(proofPrompt(p), { label: `proof:${p.id}`, phase: 'Tier1-Conformance', schema: PROOF })),
  ...suites.map((cmd) => () => agent(suitePrompt(cmd), { label: `suite`, phase: 'Tier1-Conformance', schema: PROOF })),
])).filter(Boolean)
const tier1Pass = t1.length > 0 && t1.every((r) => r.verdict === 'PASS')
const tier1Unknown = t1.length === 0 || t1.some((r) => r.verdict === 'UNKNOWN')
log(`Tier1: ${t1.filter((r) => r.verdict === 'PASS').length}/${t1.length} PASS, ${t1.filter((r) => r.verdict === 'UNKNOWN').length} UNKNOWN`)

// ── Tier 2 — Independent scenarios ──
phase('Tier2-Scenarios')
const gen = await agent(genPrompt(a.intentNotes), { label: 'scenario-gen', phase: 'Tier2-Scenarios', schema: SCEN_GEN })
const scenarios = gen && gen.scenarios ? gen.scenarios : []
const canRun = (s) => s.runnable && sandbox !== 'none'
const ran = (await parallel(scenarios.filter(canRun).map((s) => () =>
  agent(runPrompt(s), { label: `scn`, phase: 'Tier2-Scenarios', schema: SCEN })))).filter(Boolean)
const unrun = scenarios.filter((s) => !canRun(s)).map((s) => ({
  scenario: s.scenario, risk: s.risk, category: s.category, groundedIn: s.groundedIn,
  verdict: 'UNKNOWN', confidence: 'low',
  evidence: sandbox === 'none' ? 'no runnable env (sandbox=none)' : 'scenario not runnable — manual check',
}))
const t2 = [...ran, ...unrun]
const tier2RealGap = t2.some((s) => s.verdict === 'FAIL' && s.confidence === 'high')
log(`Tier2: ${scenarios.length} generated (${gen ? gen.discarded : 0} discarded), ${ran.length} run, ${t2.filter((s) => s.verdict === 'UNKNOWN').length} UNKNOWN`)

// ── Tier 3 — Quality (advisory; only if behaviour works) ──
phase('Tier3-Quality')
const behaviorWorks = tier1Pass && !tier2RealGap
let t3 = { findings: [] }
if (behaviorWorks) {
  t3 = (await agent(a.qualityPrompt || 'Audit the changed code for maintainability; emit structured findings only.',
    { label: 'quality', phase: 'Tier3-Quality', schema: QUALITY })) || { findings: [] }
  log(`Tier3: ${t3.findings.length} quality findings (${a.blockOnQuality ? 'blocking on high' : 'advisory'})`)
} else {
  log('Tier3 skipped — behaviour not confirmed working')
}

// ── Synthesis ──
phase('Synthesis')
const qualityBlocks = !!a.blockOnQuality && (t3.findings || []).some((f) => f.severity === 'high')
const verdict = tier1Pass && !tier2RealGap && !qualityBlocks ? 'DONE' : 'NOT-DONE'
const reason = !tier1Pass
  ? (t1.length === 0 ? 'no conformance checks ran' : tier1Unknown ? 'conformance UNKNOWN — could not verify (no runnable env?)' : 'conformance FAIL')
  : tier2RealGap ? 'a confirmed high-confidence scenario gap'
  : qualityBlocks ? 'high-severity quality findings (--block-on-quality)'
  : 'all gates passed'
return {
  verdict,
  reason,
  tier1: { pass: tier1Pass, results: t1 },
  tier2: { realGap: tier2RealGap, discarded: gen ? gen.discarded : 0, results: t2 },
  tier3: { advisory: !a.blockOnQuality, findings: t3.findings || [] },
  notCovered: [   // no silent truncation — Tier-1 + Tier-2 UNKNOWNs
    ...t1.filter((r) => r.verdict === 'UNKNOWN').map((r) => ({ tier: 1, id: r.id, evidence: r.evidence })),
    ...t2.filter((s) => s.verdict === 'UNKNOWN').map((s) => ({ tier: 2, scenario: s.scenario, evidence: s.evidence })),
  ],
}
