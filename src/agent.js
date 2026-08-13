// agent.js — the trial-and-error loop that binds a brain to the skills.
//
//   plan -> act (skills/macros) -> verify (expect: "ok" gates the loop)
//        -> reflect (done? or next batch) -> ... until done or max iterations
//   every episode is appended to the journal.

import * as skills from './skills.js';
import { Journal } from './memory.js';
import { runMacro } from './mechanical.js';

export async function runEpisode({
  goal,
  dir,
  brain,
  maxIterations = 6,
  journal = new Journal(),
  onEvent = () => {},
  enforceGate = true,
}) {
  const started = Date.now();
  const event = (kind, data) => onEvent(kind, data);

  event('brain', { name: brain.name });
  let plan = await brain.plan({ goal, dir, journal });
  if (!plan || !Array.isArray(plan.steps) || plan.steps.length === 0) {
    const episode = idleEpisode({ goal, dir, brain, started });
    journal.append(episode);
    event('done', { summary: episode.summary, status: episode.status });
    return episode;
  }

  const allResults = [];
  const lessons = [];
  let iteration = 0;
  let summary = '';
  let status = 'done';

  while (plan.steps.length && iteration < maxIterations) {
    iteration++;
    const results = [];
    event('plan', { iteration, steps: plan.steps });
    for (const step of plan.steps) {
      const rec = await executeStep(step, dir);
      results.push(rec);
      allResults.push(rec);
      event('step', { step: rec, iteration });
      if (enforceGate && step.expect === 'ok' && !rec.ok) {
        status = 'failed';
        break;
      }
    }

    // a verifier-free agent does not see gates at all: failures are not
    // distinguished from successes, so it trusts its own claims. This is the
    // baseline the verification gate is measured against (Fig. 9 / Table 3).
    const reflectResults = enforceGate ? results
      : results.map((r) => ({ ...r, expect: undefined }));
    const ref = await brain.reflect({ goal, dir, results: reflectResults, iteration, maxIterations, journal });
    if (ref.lessons) lessons.push(...ref.lessons);
    for (const l of ref.lessons || []) event('lesson', { lesson: l });
    summary = ref.summary;
    if (ref.done) break;
    plan = { steps: ref.steps || [] };
  }

  if (iteration >= maxIterations && summary === '') {
    status = 'failed';
    summary = 'Max iterations reached without completion.';
  }

  const episode = {
    goal,
    dir,
    brain: brain.name,
    iterations: iteration,
    results: allResults,
    summary,
    status,
    lessons,
    durationMs: Date.now() - started,
  };
  journal.append(episode);
  event('done', { summary, status, iterations: iteration });
  return episode;
}

function idleEpisode({ goal, dir, brain, started }) {
  return {
    goal,
    dir,
    brain: brain.name,
    iterations: 0,
    results: [],
    status: 'idle',
    summary:
      'No actionable plan for this goal with the mechanical brain. Try: "scaffold a new python project called X", "explain this project", "find TODOs", "run the test suite" — or set AGE_API_KEY for the LLM brain.',
    lessons: [],
    durationMs: Date.now() - started,
  };
}

async function executeStep(step, dir) {
  const base = { label: step.label };
  if (step.macro) {
    try {
      const out = runMacro(step.macro, step.args || {}, dir);
      return { ...base, ...step, ...out };
    } catch (e) {
      return { ...base, ...step, ok: false, status: 'error', output: e.message };
    }
  }
  const fn = skills[step.skill];
  if (typeof fn !== 'function') {
    return { ...base, ...step, ok: false, status: 'error', output: `unknown skill: ${step.skill}` };
  }
  try {
    const out = await fn(dir, step.args || {});
    return { ...base, ...step, ...out };
  } catch (e) {
    return { ...base, ...step, ok: false, status: 'error', output: e.message };
  }
}
