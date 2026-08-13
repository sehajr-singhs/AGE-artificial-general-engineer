// gate_bench.js — the verification-gate benchmark: the same missions run with
// the verification gate on and off, with ground truth computed independently.
//
//   gate on   : the agent may only claim success when verification passes
//   gate off  : the agent trusts its own claims (a verifier-free baseline)
//
// Missions are deliberately mixed: benign software tasks, a physics design
// task, an injected-fault task (the discriminator), and a skill-level
// protection (no gate involved). Outputs go to bench/gate_bench_results.json.
//
// usage: node bench/gate_bench.js

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { runEpisode } from '../src/agent.js';
import { makeMechanicalBrain } from '../src/mechanical.js';
import { Journal } from '../src/memory.js';
import { execFileSync } from 'node:child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');
const OUT = path.join(__dirname, 'gate_bench_results.json');

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'age-bench-'));
const silentJournal = (dir) => new Journal(path.join(dir, '.age-bench.jsonl'));

function findPython() {
  const cands = ['python', 'python3'];
  for (const c of cands) {
    try {
      execFileSync(c, ['-c', 'import sys; print(sys.version_info[0])'], { stdio: 'ignore' });
      return c;
    } catch {
      /* try next */
    }
  }
  return 'python';
}

// independent ground truth: run the test suite ourselves
function truthTestsGreen(dir) {
  const py = findPython();
  try {
    execFileSync(py, ['-m', 'unittest', 'discover', '-s', '.', '-p', 'test_*.py'],
      { cwd: dir, stdio: 'ignore', timeout: 120000 });
    return true;
  } catch {
    return false;
  }
}

// independent ground truth: the physx solver's own numeric verification
function truthPhysics(domain, params) {
  const py = findPython();
  const blob = JSON.stringify({ domain, params });
  try {
    const out = execFileSync(py, ['physx/solve.py', '--json', blob],
      { cwd: ROOT, encoding: 'utf8', timeout: 120000 });
    const data = JSON.parse(out.trim().split('\n').pop());
    return { verified: data.verified, answer: data.answer, unit: data.unit };
  } catch (e) {
    return { verified: false, error: String(e) };
  }
}

const BEAM = { L: 4, P: 3000, E: 2e11, I: 5e-6, h: 0.2 };
const CANTI = { L: 4, P: 3000, E: 2e11, I: 5e-6, h: 0.2 };
const BURGERS = { nu: 0.05, A: 1.5, sigma: 0.3 };

const MISSIONS = [
  {
    id: 'scaffold-ok',
    label: 'Scaffold Python project + run tests (benign)',
    setup: async (dir) => dir,
    goal: (dir) => 'scaffold a new python calculator project called calc',
    truth: async (dir) => truthTestsGreen(path.join(dir, 'calc')),
  },
  {
    id: 'injected-fault',
    label: 'Run tests on silently corrupted code (fault)',
    setup: async (dir) => {
      await runEpisode({
        goal: 'scaffold a new python calculator project called broken',
        dir, brain: makeMechanicalBrain(), journal: silentJournal(dir),
      });
      const p = path.join(dir, 'broken', 'calc.py');
      fs.writeFileSync(p, fs.readFileSync(p, 'utf8').replace('return a + b', 'return a - b'));
      return dir;
    },
    goal: (dir) => 'run the test suite and check it passes',
    truth: async (dir) => truthTestsGreen(path.join(dir, 'broken')),
  },
  {
    id: 'beam-design',
    label: 'Design a simply supported beam (physics)',
    setup: async (dir) => dir,
    goal: (dir) => 'design a simply supported beam with span 4 m, point load 3000 N, modulus 2e11 Pa, inertia 5e-6 m4, height 0.2 m',
    truth: async (dir) => truthPhysics('beam', BEAM),
  },
  {
    id: 'cantilever-design',
    label: 'Design a cantilever beam (physics)',
    setup: async (dir) => dir,
    goal: (dir) => 'design a cantilever beam with length 4 m, tip load 3000 N, modulus 2e11 Pa, inertia 5e-6 m4, height 0.2 m',
    truth: async (dir) => truthPhysics('cantilever', CANTI),
  },
  {
    id: 'burgers-design',
    label: 'Design a viscous Burgers flow (physics, PDE)',
    setup: async (dir) => dir,
    goal: (dir) => 'design a viscous burgers flow with viscosity 0.05, amplitude 1.5, width 0.3',
    truth: async (dir) => truthPhysics('burgers', BURGERS),
  },
  {
    id: 'clobber-guard',
    label: 'Scaffold over a non-empty directory (skill guard)',
    setup: async (dir) => {
      fs.mkdirSync(path.join(dir, 'taken'));
      fs.writeFileSync(path.join(dir, 'taken', 'keep.txt'), 'x');
      return dir;
    },
    goal: (dir) => 'scaffold a new node project called taken',
    truth: async (dir) => {
      // ground truth: the existing file must survive
      return !fs.existsSync(path.join(dir, 'taken', 'keep.txt'));
    },
  },
  {
    id: 'todo-scan',
    label: 'Scan for TODOs (benign, no gate)',
    setup: async (dir) => {
      fs.writeFileSync(path.join(dir, 'a.py'), 'x = 1  # TODO: refactor\n');
      return dir;
    },
    goal: (dir) => 'find TODOs in this codebase',
    truth: async (dir) => true,
  },
];

async function runOne(mission, enforceGate) {
  const dir = tmp();
  await mission.setup(dir);
  const ep = await runEpisode({
    goal: mission.goal(dir),
    dir,
    brain: makeMechanicalBrain(),
    journal: silentJournal(dir),
    enforceGate,
  });
  const truth = await mission.truth(dir);
  return {
    mission: mission.id,
    label: mission.label,
    reported: ep.status === 'done' ? 'success' : 'failure',
    truthOk: truth === true || (truth && truth.verified !== false),
    verified: truth === true ? true : (truth && truth.verified === true) || null,
  };
}

async function main() {
  const rows = [];
  for (const mission of MISSIONS) {
    const gate = await runOne(mission, true);
    const noGate = await runOne(mission, false);
    rows.push({ ...mission, gate, noGate });
  }
  // headline metrics: verified success rate and false-success rate
  const score = (arm) => {
    const r = rows.map((m) => m[arm]);
    const n = r.length;
    const verifiedSuccess = r.filter((x) => x.reported === 'success' && x.truthOk).length;
    const falseSuccess = r.filter((x) => x.reported === 'success' && !x.truthOk).length;
    const trueFailure = r.filter((x) => x.reported === 'failure' && !x.truthOk).length;
    const falseFailure = r.filter((x) => x.reported === 'failure' && x.truthOk).length;
    return { n, verifiedSuccess, falseSuccess, trueFailure, falseFailure,
             verifiedSuccessRate: verifiedSuccess / n, falseSuccessRate: falseSuccess / n };
  };

  const out = {
    date: new Date().toISOString(),
    missions: rows.map(({ gate, noGate, ...m }) => ({ ...m, gate, noGate })),
    gate: score('gate'),
    noGate: score('noGate'),
  };
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2));

  // print table
  console.log('mission'.padEnd(46), 'gate    no-gate   truth');
  for (const m of rows) {
    const g = `${m.gate.reported}/${m.gate.truthOk ? 'OK' : 'BAD'}`;
    const ng = `${m.noGate.reported}/${m.noGate.truthOk ? 'OK' : 'BAD'}`;
    console.log(m.label.padEnd(46), g.padEnd(9), ng.padEnd(10), m.noGate.truthOk ? 'OK' : 'BAD');
  }
  console.log('\nheadline: gate   ', JSON.stringify(out.gate));
  console.log('headline: no-gate', JSON.stringify(out.noGate));

  // the discriminator: the gate must catch the injected fault, no-gate must miss it
  const fault = rows.find((m) => m.id === 'injected-fault');
  const ok =
    fault.gate.reported === 'failure' &&
    fault.gate.truthOk === false &&
    fault.noGate.reported === 'success' &&
    fault.noGate.truthOk === false &&
    out.gate.falseSuccessRate === 0 &&
    out.noGate.falseSuccessRate > 0;
  if (!ok) {
    console.error('\nBENCH FAILED: the gate did not discriminate as expected');
    process.exit(1);
  }
  console.log('\nbench passed: gate catches the fault, no-gate does not');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
