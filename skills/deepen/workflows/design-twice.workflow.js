export const meta = {
  name: 'deepen-design-twice',
  description: 'Parallel "Design It Twice" interface exploration for /deepen Phase 3',
  phases: [{ title: 'Design' }],
}

// Optional Claude-only fast path for /deepen Phase 3.
// The MAIN LOOP (skill) renders each brief from references/parallel-interface-design.md
// + the chosen Phase-2 candidate, and passes them in via args.briefs. This script only
// fans them out in parallel and validates the output. Synthesis (compare / recommend /
// hybrid) stays in the main loop, NOT here.
//
// args.briefs: [{ label, prompt }]   // 3 by default, optional 4th (ports & adapters)
//
// DESIGN_SCHEMA mirrors the step-2 output contract in
// references/parallel-interface-design.md (interface / usage / hidden / deps / trade-offs).
// It is advisory: it makes collection uniform but does NOT try to enforce "radically
// different" — that remains the synthesis step's job.
const DESIGN_SCHEMA = {
  type: 'object',
  required: ['interface', 'usage', 'hidden', 'dependencies', 'tradeoffs'],
  additionalProperties: false,
  properties: {
    interface: {
      type: 'string',
      description: 'types, methods, params, plus invariants, ordering, error modes',
    },
    usage: {
      type: 'string',
      description: 'usage example showing how callers use it',
    },
    hidden: {
      type: 'string',
      description: 'what the implementation hides behind the seam',
    },
    dependencies: {
      type: 'string',
      description: 'dependency strategy + adapters (deepening-patterns.md category)',
    },
    tradeoffs: {
      type: 'string',
      description: 'where leverage is high, where it is thin',
    },
  },
}

const designs = await parallel(
  args.briefs.map((b) => () =>
    agent(b.prompt, { label: b.label, phase: 'Design', schema: DESIGN_SCHEMA }).then((d) => ({
      label: b.label,
      ...d,
    }))
  )
)

// A crashed agent becomes null (parallel() never rejects). Drop nulls and let the main
// loop compare returned vs requested counts: <briefs.length means an agent failed, which
// the skill surfaces (it is one fewer design to compare, never silent data loss).
return designs.filter(Boolean)
