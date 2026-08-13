#!/usr/bin/env node
// age — an Artificial General Engineer.
//
//   node age.js "goal" [--dir DIR] [--brain mechanical|llm] [--max-iter N] [--demo]
//
// Defaults: dir = current directory, brain = llm if AGE_API_KEY is set else
// mechanical. `--demo` scaffolds and verifies a sample project in age/.demo/.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { runEpisode } from './src/agent.js';
import { makeMechanicalBrain } from './src/mechanical.js';
import { makeLLMBrain, available as llmAvailable } from './src/brain.js';
import { Journal } from './src/memory.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const C = (code, s) => (process.stdout.isTTY ? `\x1b[${code}m${s}\x1b[0m` : s);
const BOLD = 1, DIM = 2, GREEN = 32, RED = 31, YELLOW = 33, CYAN = 36, MAGENTA = 35;

function usage() {
  console.log(`age — an Artificial General Engineer

usage:
  node age.js "goal" [options]

options:
  --dir DIR        working directory for the mission (default: cwd)
  --brain NAME     mechanical | llm (default: llm if AGE_API_KEY set, else mechanical)
  --model NAME     LLM model (env AGE_MODEL, default gpt-4o-mini)
  --base-url URL   OpenAI-compatible endpoint (env AGE_BASE_URL)
  --max-iter N     max plan iterations (default 6)
  --demo           run a self-contained scaffold+verify demo in age/.demo/
  --journal FILE   episode journal path (env AGE_JOURNAL)
  -h, --help       this help
  -v, --version    print version

env:
  AGE_API_KEY      API key for the LLM brain (any OpenAI-compatible endpoint)
  AGE_BASE_URL     endpoint base, e.g. http://localhost:11434/v1 (Ollama)
  AGE_MODEL        model id, e.g. gpt-4o-mini, qwen2.5-coder, deepseek-chat
  AGE_JOURNAL      path to the episode journal
  AGE_ALLOW_DANGEROUS=1   allow destructive shell commands in run/verify`);
}

function parseArgs(argv) {
  const opts = { goal: '', dir: process.cwd(), brain: null, maxIter: 6, demo: false, journal: null };
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    if (a === '--dir') opts.dir = next();
    else if (a === '--brain') opts.brain = next();
    else if (a === '--model') process.env.AGE_MODEL = next();
    else if (a === '--base-url') process.env.AGE_BASE_URL = next();
    else if (a === '--max-iter') opts.maxIter = parseInt(next(), 10) || 6;
    else if (a === '--journal') opts.journal = next();
    else if (a === '--demo') opts.demo = true;
    else if (a === '-h' || a === '--help') opts.help = true;
    else if (a === '-v' || a === '--version') opts.version = true;
    else positional.push(a);
  }
  opts.goal = positional.join(' ');
  return opts;
}

function printer() {
  return (kind, data) => {
    switch (kind) {
      case 'brain':
        console.log(C(BOLD, `\n🧠 brain: ${data.name}`));
        break;
      case 'plan': {
        const list = data.steps.map((s, i) => `${i + 1}.${s.label || s.skill + (s.args ? ' ' + JSON.stringify(s.args) : '')}`).join('\n    ');
        console.log(C(CYAN, `\n[plan #${data.iteration}]`));
        console.log('    ' + list);
        break;
      }
      case 'step': {
        const r = data.step;
        const head = (r.label || `${r.macro ? 'macro:' + r.macro : 'skill:' + r.skill}`).slice(0, 80);
        if (r.ok) console.log(`  ${C(GREEN, '✔')} ${C(DIM, head)}`);
        else {
          console.log(`  ${C(RED, '✘')} ${head} — ${C(RED, r.status)}`);
          const tail = String(r.output || '').split('\n').slice(0, 6).join('\n    ');
          console.log(C(DIM, '    ' + tail));
        }
        break;
      }
      case 'lesson':
        console.log(`  ${C(YELLOW, '⚠ lesson:')} ${C(DIM, data.lesson)}`);
        break;
      case 'done': {
        const color = data.status === 'done' ? GREEN : RED;
        console.log(`\n${C(BOLD, '— mission ' + data.status.toUpperCase() + ' —')} ${data.iterations ? `(${data.iterations} iteration${data.iterations > 1 ? 's' : ''})` : ''}\n`);
        console.log(C(color, data.summary));
        console.log(C(DIM, `\njournal: ${global.__ageJournalFile || '~/.age/journal.jsonl'}`));
        break;
      }
    }
  };
}

async function demo() {
  const demoRoot = path.join(HERE, '.demo');
  fs.rmSync(demoRoot, { recursive: true, force: true });
  const journal = new Journal(path.join(HERE, '.age', 'journal.jsonl'));
  console.log(C(BOLD, 'AGE demo — Artificial General Engineer (mechanical brain, no API keys needed)'));
  console.log(C(DIM, `working dir: ${demoRoot}`));

  const software = await runEpisode({
    goal: 'scaffold a new python calculator project called age-demo',
    dir: demoRoot,
    brain: makeMechanicalBrain(),
    journal,
    onEvent: printer(),
  });
  console.log(C(DIM, `\nartifacts: ${path.join(demoRoot, 'age-demo')}`));

  console.log(C(BOLD, '\n\nAct 2 — physics engineering (PhysFormer + numeric verification)'));
  const physics = await runEpisode({
    goal: 'design a simply supported beam with span 4 m, point load 3000 N, modulus 2e11 Pa, inertia 5e-6 m^4, height 0.2 m',
    dir: demoRoot,
    brain: makeMechanicalBrain(),
    journal,
    onEvent: printer(),
  });
  process.exit(software.status === 'done' && physics.status === 'done' ? 0 : 1);
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) return usage();
  if (opts.version) {
    const pkg = JSON.parse(fs.readFileSync(path.join(HERE, 'package.json'), 'utf8'));
    console.log(`age v${pkg.version}`);
    return;
  }
  if (opts.demo) return demo();

  if (!opts.goal) {
    usage();
    process.exit(2);
  }

  fs.mkdirSync(opts.dir, { recursive: true });
  const journal = new Journal(opts.journal);
  global.__ageJournalFile = journal.file;

  const brain = opts.brain === 'mechanical'
    ? makeMechanicalBrain()
    : opts.brain === 'llm'
      ? makeLLMBrain()
      : llmAvailable()
        ? makeLLMBrain()
        : makeMechanicalBrain();

  const episode = await runEpisode({
    goal: opts.goal,
    dir: opts.dir,
    brain,
    maxIterations: opts.maxIter,
    journal,
    onEvent: printer(),
  });
  process.exit(episode.status === 'done' ? 0 : 1);
}

main().catch((e) => {
  console.error(`[age] fatal: ${e.stack || e.message}`);
  process.exit(1);
});
