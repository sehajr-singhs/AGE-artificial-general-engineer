# AGE — Artificial General Engineer

> Jeff Bezos's Prometheus ($6.2B, 120 engineers, SF/London/Zurich) is building
> an **Artificial General Engineer**: AI that learns engineering through
> real-world trial and error, aimed at physical products — aerospace, autos,
> computers. This is that idea, applied to software, in ~1,000 lines of
> dependency-free Node. The $6.2B idea, minus the $6.2B.

**Papers (in this repo):** [Nature Machine Intelligence format](nmi_paper.pdf) ·
[IEEE format](ieee_paper.pdf) · [supplementary information](supplementary_information.pdf).
Source of truth is `nmi_paper.tex`; every number in it reads from a committed
JSON under `physx/models/`, never hand-typed. The system's component studies
(physics transformers, PhysBench, verification gating, loss-channel analysis,
few-shot law acquisition, field consistency) live in their own repos, linked
at the bottom.

AGE is an autonomous engineering agent. Give it a goal ("scaffold a new Python
calculator project", "explain this repo", "find the TODOs", "make the test
suite pass") and it plans, acts, **verifies** (runs your tests/typechecks),
iterates on failures, and journals every episode as a learned lesson.

```bash
node age.js "scaffold a new python calculator project called myapp" --dir ~/code
node age.js "explain this project" --dir ../street-fighter-2-remake
node age.js "find TODOs in this codebase" --dir ~/code/myapp
node age.js --demo          # two-act demo: software scaffold + physics design
npm test                    # 16 node tests: loop, skills, sandboxing, physics, brains, journal
python3 -m unittest physx.test_physx   # 49 physics tests: closed forms, verifiers, physformer, ablations
```

## Physics engineering (physx)

AGE also *does* physics. `physx/` is a physics-informed engineering core
(~700 lines of Python, PyTorch) that turns engineering questions into
**verified answers**: every design is computed from the closed-form solution,
then cross-checked by an *independent* numeric simulation (Euler/RK4
integration, finite-difference beam solver). If a trained model exists, a
**PhysFormer** — a transformer with reasoning layers *plus* physics-consistency
layers (PINN-style residual loss against the governing equations) — predicts
the answer from the parameters alone.

```bash
node age.js "design a simply supported beam with span 4 m, point load 3000 N, modulus 2e11 Pa, inertia 5e-6 m^4, height 0.2 m"
# → Answer: 0.004 m — verified against an independent numeric simulation: true (residual 2.6e-9)
#   PhysFormer (physics-adjusted transformer) predicted 0.003895 m
```

- **Domains** (each with exact closed form + numeric verify): projectile,
  pendulum, spring-mass, simply-supported beam (deflection + stress), RC circuit.
- **Goal syntax** — `key = value` assignments or natural language:
  `"span 4 m, point load 3000 N, modulus 2e11 Pa"`, `"v0 = 15, angle = 30"`,
  `"find the time constant of an RC circuit with R = 1e3, C = 1e-6"`.
- **The transformer** (`physx/physformer.py`): param embeddings → reasoning
  transformer encoder → trajectory + answer heads; a physics-consistency layer
  computes how far a predicted trajectory strays from the governing equation
  and that residual is added to the loss, so the model is trained on data AND
  physics. Beam/RC answers spanning orders of magnitude are learned in log space;
  the physics gradient is scale-free so it can't destabilize training.
- **Train your own**: `python3 physx/train.py --domain beam --epochs 50 --samples 1500`
  (saves to `physx/models/`). Trained models: projectile 3.9% rel error, beam
  12.7%. Unit tests: `python3 -m unittest physx.test_physx` (49 physics tests).
- **Solver CLI**: `python3 physx/solve.py --domain beam --params '{"L":4,"P":3000,"E":2e11,"I":5e-6,"h":0.2}'`
  — prints closed-form answer, independent numeric verification, and the
  PhysFormer prediction with its physics residual.

## How it maps to Prometheus

Prometheus's stated thesis is that AGI for engineering must learn from
**real-world trial and error**, not just digital data. AGE implements the same
architecture in the software domain — and, with physx, a slice of the physical
one:

| Prometheus (physical world)          | AGE (software world)                                  |
| ------------------------------------ | ----------------------------------------------------- |
| World model of physics & materials   | Codebase model: file tree, key files, regex search    |
| Real-world trial and error           | `plan → act → verify` loop; tests/typechecks gate it  |
| Embodiment (robots, tooling)         | Sandboxed skill layer: inspect / read / search / edit / run / verify |
| Memory of manufacturing runs         | JSONL episode journal + lessons replayed into later plans |
| General engineer (any physical task) | Mission recognition: scaffold / explain / scan / test / **physics design** — plus a general LLM brain |
| Physics-informed model of materials | PhysFormer: transformer with reasoning layers + physics-consistency layers (PINN residual), trained on exact closed-form trajectories |
| Simulated/physical trial and error | `physx` solver: closed-form answer cross-checked by independent numeric simulators (Euler/RK4, finite differences) — the verify gate for physics |

The loop is the heart: every step can carry `expect: "ok"`, and a failed
verification fails the mission and writes a **lesson** (`verify step failed:
...`) into the journal, so the engineer gets smarter across runs.

## Two brains

- **mechanical** (default, zero keys): deterministic mission recognition —
  scaffolds real projects from templates, explains repos, scans for
  TODO/FIXME, runs test suites. Fully offline and unit-tested.
- **llm**: plugs into any OpenAI-compatible endpoint and re-plans each
  iteration from observations, so it can actually *fix* bugs, not just
  find them.

```bash
export AGE_API_KEY=sk-...        # OpenAI, OpenRouter, or any compatible provider
export AGE_BASE_URL=http://localhost:11434/v1   # e.g. Ollama
export AGE_MODEL=qwen2.5-coder:14b
node age.js "add a multiply function to calc.py and make the tests pass" --dir ~/code/myapp
```

## Architecture

```
age.js (CLI) ──► agent.js (trial-and-error loop)
                    │  plan()      │  executeStep()      │  reflect()
                    ▼              ▼                     ▼
              brain (mechanical | llm)   skills (embodiment)   memory (journal)
                                         ├─ inspect  file tree + key files
                                         ├─ read     one file
                                         ├─ search   regex across text files
                                         ├─ edit     create/replace/append (confined to dir)
                                         ├─ run      shell command (timeout, denylist)
                                         └─ verify   gating check (expect: "ok")
```

- `src/skills.js` — the hands. Writes are confined to the working dir
  (path-traversal blocked); destructive commands (`rm -rf /`, `git push`,
  `sudo`, …) are refused unless `AGE_ALLOW_DANGEROUS=1`.
- `src/mechanical.js` — deterministic brain: mission regexes, the scaffold
  macro, reflection/summarization.
- `src/brain.js` — LLM brain: OpenAI-compatible chat client, JSON plan
  parsing, graceful degradation to inspect-only on errors.
- `src/templates.js` — Python / Node / Go calculator scaffolds, each with a
  passing test suite, so "scaffold" always ends in a verified green run.
- `src/memory.js` — JSONL journal (default `age/.age/journal.jsonl`), lessons
  replayed into future LLM plans.
- `src/agent.js` — orchestrates: plan → act → verify → reflect → journal.

## Roadmap

1. **Symbol index** — a real codebase model (functions, classes, call sites)
   so plans are grounded in symbols, not just file text.
2. **Verifier-driven fixes** — when the LLM brain hits a red test, feed the
   failing diff back and iterate until green (the loop already supports it;
   needs a good coder model and more iterations).
3. **More physics** — dynamics (multi-body, orbital), fluids, thermo;
   PhysFormer residual heads for ODE systems; fine-tune on real measured data
   instead of closed forms only.
4. **Skill library growth** — `git-diff`, `typecheck`, `refactor`, `test-gen`
   as first-class skills with schemas.
5. **Human-in-the-loop** — approval gates for edits outside the working dir
   and for `run`; diff review before merge.
6. **Physical embodiment** — extend the skill layer to hardware: CAD APIs,
   simulator harnesses, robot toolchains. That's the Prometheus endgame; the
   plan/verify loop is identical.

## Safety

AGE is sandboxed by default: edits confined to the working directory, command
timeouts, and a denylist for destructive commands. For real autonomy, run it
inside a container/VM and review journal entries before merging changes. It is
a research prototype, not a product — verify its work before trusting it.

## Tests

```bash
npm test
```

Covers: scaffold→verify green path, verify catching broken code (the
trial-and-error gate), non-empty-dir refusal, explain overview, TODO scan,
search, path-traversal blocking, dangerous-command blocking, python
interpreter resolution, JSON plan parsing, physx beam solving + verification,
the physics param parser, and journal/lesson recording.

## Component papers

The physics-AI core is dissected in five standalone studies, each with its own
repo and manuscript:

- **physics-transformers** — the PhysFormer architecture: physics as input
  tokens, as loss, and as a causal intervention; a ten-law pre-registered
  regime test (falsified, reported honestly); DeepONet external baseline.
- **physbench** — the 12-domain verifiable benchmark the whole suite is
  measured on.
- **verification-gated-agents** — why the gate, not the model, is the missing
  control in agent evaluation (0% vs 29% false success).
- **physics-loss-channel** — when physics supervision in the loss helps, and
  when it merely makes predictions consistent (19× residual cut, null
  accuracy effect).
- **fewshot-law-acquisition** — transfer across *laws*: vocabulary is the
  dominant carrier (10×), residual constrains trajectory specialization at
  tiny data budgets.
- **field-consistency** — consistency is not accuracy at the field level;
  the cost of enforcing PDE residuals on 2D fields, with a DeepXDE tradeoff.

All seven manuscripts share one codebase (`physx/`) and one guarantee: every
number traces to a committed JSON and regenerates from a committed script.
