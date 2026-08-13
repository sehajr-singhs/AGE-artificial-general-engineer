// brain.js — the LLM brain. Talks to any OpenAI-compatible /chat/completions
// endpoint (OpenAI, OpenRouter, Ollama, local servers). Plans and re-plans in
// JSON; degrades gracefully to mechanical behavior on network/parse errors.

import * as skills from './skills.js';

const BASE = (process.env.AGE_BASE_URL || 'https://api.openai.com/v1').replace(/\/+$/, '');
const MODEL = process.env.AGE_MODEL || 'gpt-4o-mini';
const KEY = process.env.AGE_API_KEY;

export const name = 'llm';

export function available() {
  return Boolean(KEY);
}

export function makeLLMBrain() {
  return { name, plan, reflect };
}

const SYSTEM = `You are AGE — an Artificial General Engineer. You work autonomously inside a working directory to accomplish the user's goal: you plan small steps, act, then verify by running checks, iterating on failures (trial and error) until the goal is met.

Available skills (JSON args):
- inspect {"maxDepth": 3} — file tree + contents of key files in the working dir
- read {"path": "file"} — contents of one file
- search {"pattern": "regex"} — regex search across text files
- edit {"path": "file", "content": "...", "mode": "create|replace|append"} — write a file (writes confined to the working dir; prefer create for new files)
- run {"command": "shell command"} — run a command in the working dir
- verify {"command": "check command"} — a check that must pass; include "expect": "ok" so the loop gates on it

Rules:
- Verify after editing: run the relevant test/typecheck command and expect ok.
- Keep writes small and targeted. Do not touch files unrelated to the goal.
- Inspect first when the layout is unknown.
- Respond ONLY with JSON: {"reasoning": "one short line", "steps": [{"skill": "...", "args": {...}, "expect": "ok"?}]}`;

function world(dir, journal) {
  let w = '';
  try {
    const insp = skills.inspect(dir, { maxDepth: 3 });
    w = insp.output;
  } catch (e) {
    w = `(could not inspect: ${e.message})`;
  }
  const lessons = journal ? journal.lessons(5) : [];
  if (lessons.length) {
    w += `\n\nPAST LESSONS (from earlier missions — apply them):\n${lessons.map((l) => ' - ' + l).join('\n')}`;
  }
  return w;
}

async function chat(messages) {
  const res = await fetch(`${BASE}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(KEY ? { Authorization: `Bearer ${KEY}` } : {}),
    },
    body: JSON.stringify({ model: MODEL, messages, temperature: 0.2, max_tokens: 1500 }),
    signal: AbortSignal.timeout(120_000),
  });
  if (!res.ok) {
    throw new Error(`LLM endpoint ${res.status}: ${(await res.text()).slice(0, 400)}`);
  }
  const data = await res.json();
  const content = data?.choices?.[0]?.message?.content;
  if (!content) throw new Error('LLM returned empty content');
  return content;
}

export function extractJSON(text) {
  const start = text.indexOf('{');
  if (start === -1) return null;
  let depth = 0;
  let inStr = false;
  let esc = false;
  for (let i = start; i < text.length; i++) {
    const c = text[i];
    if (inStr) {
      if (esc) esc = false;
      else if (c === '\\') esc = true;
      else if (c === '"') inStr = false;
      continue;
    }
    if (c === '"') inStr = true;
    else if (c === '{') depth++;
    else if (c === '}') {
      depth--;
      if (depth === 0) return text.slice(start, i + 1);
    }
  }
  return null;
}

function parseResponse(text) {
  const json = extractJSON(text);
  if (!json) return null;
  try {
    return JSON.parse(json);
  } catch {
    return null;
  }
}

const safeSteps = (obj) => Array.isArray(obj?.steps) ? obj.steps : null;

export async function plan({ goal, dir, journal }) {
  try {
    const content = await chat([
      { role: 'system', content: SYSTEM },
      { role: 'user', content: `GOAL: ${goal}\n\nWORKING DIR: ${dir}\n\n${world(dir, journal)}\n\nPlan the first batch of steps as JSON.` },
    ]);
    const obj = parseResponse(content);
    const steps = safeSteps(obj);
    if (steps && steps.length) return { steps };
    // fall through to degrade
  } catch (e) {
    console.error(`[age] LLM plan failed (${e.message}); degrading to inspect.`);
  }
  return { steps: [{ skill: 'inspect', args: {}, expect: 'ok' }] };
}

export async function reflect({ goal, dir, results, iteration, maxIterations, journal }) {
  if (iteration >= maxIterations - 1) {
    return {
      done: true,
      summary: 'Max iterations reached. Results so far:\n' + results.map(summarize).join('\n'),
      lessons: [],
    };
  }
  const summary = results.map(summarize).join('\n');
  try {
    const content = await chat([
      { role: 'system', content: SYSTEM },
      {
        role: 'user',
        content: `GOAL: ${goal}\n\nWORKING DIR: ${dir}\n\n${world(dir, journal)}\n\nRESULTS OF LAST STEPS:\n${summary}\n\nDecide: either respond {"done": true, "summary": "final report"} or {"steps": [next batch]}. The mission is complete only when the goal is genuinely satisfied and checks pass.`,
      },
    ]);
    const obj = parseResponse(content);
    if (obj?.done) return { done: true, summary: String(obj.summary || 'Done.'), lessons: [] };
    const steps = safeSteps(obj);
    if (steps && steps.length) return { done: false, steps };
  } catch (e) {
    console.error(`[age] LLM reflect failed (${e.message}); finishing.`);
  }
  return { done: true, summary: 'LLM reflect unavailable; stopping.\n' + summary, lessons: [] };
}

function summarize(r) {
  const mark = r.ok ? '[ok]' : `[${r.status}]`;
  const head = (r.label || `${r.macro ? 'macro:' + r.macro : 'skill:' + r.skill}`).slice(0, 90);
  const tail = String(r.output || '').split('\n').slice(0, 3).join(' | ').slice(0, 200);
  return `${mark} ${head}${tail ? ' — ' + tail : ''}`;
}
