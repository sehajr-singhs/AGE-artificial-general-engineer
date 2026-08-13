// mechanical.js — the deterministic fallback brain. It recognizes common
// engineering missions from the goal text, chains skills + macros to complete
// them, and reflects on results. No API keys, no network, fully testable.
//
// Missions recognized:
//   scaffold | explain | find TODO/FIXME | run the test suite
// Anything else degrades to inspect-and-report.

import fs from 'node:fs';
import path from 'node:path';
import * as skills from './skills.js';
import { parseLang, parseName, TEMPLATES } from './templates.js';

export const name = 'mechanical';

export function makeMechanicalBrain() {
  return { name, plan, reflect };
}

// ---------------------------------------------------------------- planning

export function plan({ goal, dir }) {
  const g = goal.toLowerCase();

  if (/\b(scaffold|create|start|new|make|generate|init|boilerplate|template)\b/.test(g) &&
      /\b(project|app|repo|tool|cli|module|program)\b/.test(g)) {
    const lang = parseLang(goal);
    const nm = parseName(goal);
    return {
      steps: [
        { skill: 'inspect', args: {}, expect: 'ok' },
        { macro: 'scaffold', args: { lang, name: nm }, label: `scaffold ${lang} project ${nm}`, expect: 'ok' },
        { skill: 'verify', args: { command: TEMPLATES[lang].verify, cwd: nm }, label: `verify: ${TEMPLATES[lang].verify}`, expect: 'ok' },
      ],
    };
  }

  const physDomain = detectPhysicsDomain(g);
  if (physDomain) {
    const params = extractParams(goal, physDomain);
    const given = Object.keys(params).length
      ? Object.entries(params).map(([k, v]) => `${k}=${v}`).join(', ')
      : 'default parameters (mid-range)';
    return {
      steps: [
        {
          skill: 'physx',
          args: { domain: physDomain, params },
          label: `solve ${physDomain} design (${given}) — closed form + numeric verify`,
          expect: 'ok',
        },
      ],
    };
  }

  if (/\b(explain|summarize|overview|describe|tour|walk me through|what does|understand|analyze)\b/.test(g)) {
    return { steps: [{ skill: 'inspect', args: {}, expect: 'ok' }] };
  }

  if (/\b(todos?|fixme|hack|xxx)\b/.test(g) && /\b(scan|find|search|list|check)\b/.test(g)) {
    return {
      steps: [
        { skill: 'search', args: { pattern: 'TODO|FIXME|HACK|XXX' }, expect: 'ok' },
      ],
    };
  }

  if (/\b(test|verify|check|validate)\b/.test(g) && /\b(suite|pass|fail|run|green|red)\b/.test(g)) {
    const lang = detectLang(dir);
    const t = TEMPLATES[lang];
    if (t) {
      return { steps: [{ skill: 'verify', args: { command: t.verify }, expect: 'ok' }] };
    }
  }

  return { steps: [{ skill: 'inspect', args: {}, expect: 'ok' }] };
}

// ---------------------------------------------------------------- macros

export function runMacro(name, args, dir) {
  if (name === 'scaffold') {
    const t = TEMPLATES[args.lang];
    if (!t) return { ok: false, status: 'fail', output: `unknown template lang: ${args.lang}` };
    const target = path.join(dir, args.name);
    if (fs.existsSync(target) && fs.readdirSync(target).length > 0) {
      return { ok: false, status: 'fail', output: `target dir ${args.name}/ exists and is not empty` };
    }
    for (const [rel, content] of Object.entries(t.files)) {
      const p = skills.safeJoin(target, rel);
      fs.mkdirSync(path.dirname(p), { recursive: true });
      fs.writeFileSync(p, content.replaceAll('{NAME}', args.name));
    }
    const fileCount = Object.keys(t.files).length;
    return {
      ok: true,
      status: 'ok',
      output: `scaffolded ${t.label} project in ${args.name}/ (${fileCount} files, template ${t.id})`,
    };
  }
  return { ok: false, status: 'fail', output: `unknown macro: ${name}` };
}

// -------------------------------------------------------------- reflection

export function reflect({ goal, results, dir, iteration }) {
  const failed = results.filter((r) => r.expect === 'ok' && !r.ok);
  if (failed.length) {
    const first = failed[0];
    const tail = String(first.output).split('\n').slice(-4).join(' | ');
    const lesson = `verify step failed (${first.label || first.skill}): ${tail.slice(0, 300)}`;
    return {
      done: true,
      summary: `Mission not complete — ${lesson}. Fix the code and re-run, or retry with the LLM brain.`,
      lessons: [lesson],
    };
  }

  const g = goal.toLowerCase();
  const lines = results.map((r) => summarizeResult(r));

  if (detectPhysicsDomain(g) || results.some((r) => r.skill === 'physx')) {
    const pr = results.find((r) => r.skill === 'physx');
    if (pr && pr.data) {
      const d = pr.data;
      let s = `Physics design complete — ${d.question}\n`;
      s += `Answer: ${fmt(d.answer)} ${d.unit} — verified against an independent numeric simulation: ${d.verified}`;
      if (d.residual != null) s += ` (relative residual ${Number(d.residual).toExponential(2)})`;
      if (d.model_prediction != null) {
        s += `\nPhysFormer (physics-adjusted transformer) predicted ${fmt(d.model_prediction)} ${d.unit} `;
        s += `with physics residual ${Number(d.model_residual).toExponential(2)}`;
      }
      return { done: true, summary: s, lessons: [] };
    }
  }

  if (/\b(explain|summarize|overview|describe|tour|walk me through|what does|understand|analyze)\b/.test(g)) {
    return { done: true, summary: overview(goal, results, dir), lessons: [] };
  }
  if (/\b(todos?|fixme|hack)\b/.test(g)) {
    return { done: true, summary: `Scan complete.\n${lines.join('\n')}`, lessons: [] };
  }
  if (/\b(test|verify|check)\b/.test(g)) {
    return { done: true, summary: `All checks green.\n${lines.join('\n')}`, lessons: [] };
  }
  return { done: true, summary: `Mission complete.\n${lines.join('\n')}`, lessons: [] };
}

function summarizeResult(r) {
  const mark = r.ok ? '[ok]' : `[${r.status}]`;
  const head = (r.label || `${r.macro ? 'macro:' + r.macro : 'skill:' + r.skill}`).slice(0, 90);
  const tail = String(r.output || '').split('\n').slice(0, 3).join(' | ').slice(0, 200);
  return `${mark} ${head}${tail ? ' — ' + tail : ''}`;
}

// ------------------------------------------------------ physics missions

// domains recognized from goal text + their canonical parameter keys
const PHYSICS_DOMAINS = {
  beam: { keys: ['L', 'P', 'E', 'I', 'h'], label: 'simply-supported beam' },
  cantilever: { keys: ['L', 'P', 'E', 'I', 'h'], label: 'cantilever beam' },
  projectile: { keys: ['v0', 'angle'], label: 'projectile' },
  pendulum: { keys: ['L', 'theta0'], label: 'pendulum' },
  spring: { keys: ['k', 'm', 'A'], label: 'spring-mass' },
  burgers: { keys: ['nu', 'A', 'sigma'], label: 'viscous Burgers flow' },
  rc: { keys: ['R', 'C', 'V0'], label: 'RC circuit' },
  heat2d: { keys: ['A', 'k', 'l'], label: '2D heat-conduction plate' },
};

// key/alias -> canonical key, for `key = value` style goals
const ALIAS = {
  beam: { l: 'L', length: 'L', span: 'L', p: 'P', load: 'P', force: 'P', e: 'E', modulus: 'E', i: 'I', inertia: 'I', h: 'h', height: 'h', depth: 'h' },
  cantilever: { l: 'L', length: 'L', span: 'L', p: 'P', load: 'P', force: 'P', e: 'E', modulus: 'E', i: 'I', inertia: 'I', h: 'h', height: 'h', depth: 'h' },
  projectile: { v0: 'v0', velocity: 'v0', speed: 'v0', angle: 'angle', theta: 'theta' },
  pendulum: { l: 'L', length: 'L', theta0: 'theta0', theta: 'theta0' },
  spring: { k: 'k', stiffness: 'k', m: 'm', mass: 'm', a: 'A', amplitude: 'A' },
  burgers: { nu: 'nu', viscosity: 'nu', a: 'A', amplitude: 'A', sigma: 'sigma', width: 'sigma' },
  rc: { r: 'R', resistance: 'R', c: 'C', capacitance: 'C', v0: 'V0', voltage: 'V0' },
  heat2d: { a: 'A', amplitude: 'A', peak: 'A', temperature: 'A', k: 'k', l: 'l', mode: 'k' },
};

// natural-language patterns: "span 4 m", "point load 3000 N", "modulus 2e11 Pa"
const NL = {
  beam: [
    [/\b(?:span|length)\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'L'],
    [/\b(?:point\s+)?load\b(?: of)?\s+(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)/i, 'P'],
    [/\b(?:elastic\s+)?modulus\b(?: of)?\s+(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)/i, 'E'],
    [/\b(?:moment\s+of\s+)?inertia\b(?: of)?\s+(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)/i, 'I'],
    [/\b(?:section\s+)?height\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'h'],
  ],
  cantilever: [
    [/\b(?:span|length)\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'L'],
    [/\b(?:tip\s+|point\s+)?load\b(?: of)?\s+(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)/i, 'P'],
    [/\b(?:elastic\s+)?modulus\b(?: of)?\s+(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)/i, 'E'],
    [/\b(?:moment\s+of\s+)?inertia\b(?: of)?\s+(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)/i, 'I'],
    [/\b(?:section\s+)?height\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'h'],
  ],
  projectile: [
    [/\b(?:velocity|speed)\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'v0'],
    [/\bangle\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'angle'],
  ],
  pendulum: [
    [/\b(?:length|pendulum\s+length)\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'L'],
    [/\b(?:initial\s+)?(?:angle|theta0?)\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'theta0'],
  ],
  spring: [
    [/\b(?:stiffness|spring\s+constant)\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'k'],
    [/\bmass\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'm'],
    [/\bamplitude\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'A'],
  ],
  burgers: [
    [/\b(?:viscosity|nu)\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'nu'],
    [/\bamplitude\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'A'],
    [/\b(?:initial\s+)?(?:width|sigma)\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'sigma'],
  ],
  rc: [
    [/\bresistance\b(?: of)?\s+(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)/i, 'R'],
    [/\bcapacitance\b(?: of)?\s+(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)/i, 'C'],
    [/\b(?:supply\s+)?voltage\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'V0'],
  ],
  heat2d: [
    [/\b(?:peak\s+)?(?:temperature|amplitude)\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'A'],
    [/\b(?:mode|k)\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'k'],
    [/\bl\b(?: of)?\s+(-?\d+(?:\.\d+)?)/i, 'l'],
  ],
};

const ASSIGN = /([a-zA-Z][a-zA-Z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)/g;

export function detectPhysicsDomain(g) {
  const s = g.toLowerCase();
  if (/\bcantilever\b|\bfixed\s+end\b|\btip\s+load\b/.test(s)) return 'cantilever';
  if (/\bbeam\b|\bdeflection\b|\bbending\b|(?:simply\s+)?supported/.test(s)) return 'beam';
  if (/\bprojectile\b|\blaunch\w*\b|\btrajectory\b/.test(s)) return 'projectile';
  if (/\bpendulum\b|\bperiod\b/.test(s)) return 'pendulum';
  if (/\bspring\b|\boscillat\w*\b/.test(s)) return 'spring';
  if (/\brc\s+circuit\b|\btime\s+constant\b|\bcapacitor\b|\bcapacitance\b/.test(s)) return 'rc';
  if (/\bburgers\b|\bviscous\s+flow\b|\bshock\b/.test(s)) return 'burgers';
  if (/\bheat\b|\bplate\b|\bpoisson\b|\bconduction\b|\btemperature\s+field\b/.test(s)) return 'heat2d';
  return null;
}

export function extractParams(goal, domain) {
  const g = goal.replace(/\s+/g, ' ');
  const alias = ALIAS[domain] || {};
  const found = {};
  let m;
  ASSIGN.lastIndex = 0;
  while ((m = ASSIGN.exec(g))) {
    const canon = alias[m[1].toLowerCase()];
    if (canon && found[canon] === undefined) found[canon] = parseFloat(m[2]);
  }
  for (const [re, key] of NL[domain] || []) {
    if (found[key] !== undefined) continue;
    const hit = re.exec(g);
    if (hit) found[key] = parseFloat(hit[1]);
  }
  return found;
}

function fmt(x) {
  return Number(Number(x).toPrecision(6));
}

// ------------------------------------------------------- explain overview

const EXT_LABELS = {
  '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.go': 'Go',
  '.rs': 'Rust', '.c': 'C', '.cpp': 'C++', '.java': 'Java', '.ps1': 'PowerShell',
  '.html': 'HTML', '.css': 'CSS', '.sh': 'Shell', '.md': 'Markdown',
  '.json': 'JSON', '.yaml': 'YAML', '.toml': 'TOML', '.lua': 'Lua',
};

export function detectLang(dir) {
  const files = skills.walk(dir).map((f) => path.basename(f));
  if (files.includes('package.json')) return 'node';
  if (files.includes('go.mod')) return 'go';
  if (files.some((f) => f.endsWith('.py'))) return 'python';
  return 'python';
}

export function overview(goal, results, dir) {
  const insp = results.find((r) => r.skill === 'inspect');
  const files = skills.walk(dir)
    .map((f) => path.relative(dir, f).split(path.sep).join('/'))
    .filter((f) => !f.startsWith('.'));
  const extCount = {};
  for (const f of files) {
    const ext = path.extname(f).toLowerCase();
    if (EXT_LABELS[ext]) extCount[EXT_LABELS[ext]] = (extCount[EXT_LABELS[ext]] || 0) + 1;
  }
  const langs = Object.entries(extCount).sort((a, b) => b[1] - a[1]).map(([l, n]) => `${l} (${n})`);
  const readme = files.find((f) => /^readme/i.test(f));
  const entry = files.find((f) => /^(main|app|index|server|cli)\.[a-z]+$/i.test(f)) || files.find((f) => /^[a-z0-9_-]+\.(py|js|ts|go)$/i.test(f));

  let out = `## Repo overview — ${files.length} file(s) detected\n`;
  out += langs.length ? `Languages: ${langs.join(', ')}\n` : 'Languages: none detected\n';
  if (entry) out += `Likely entry point: ${entry}\n`;
  if (readme) {
    try {
      const txt = fs.readFileSync(path.join(dir, readme), 'utf8').slice(0, 1500);
      out += `\n### README (${readme})\n${txt}\n`;
    } catch {
      /* skip */
    }
  }
  if (insp) {
    out += `\n### File tree\n${insp.output.split('\n').slice(0, 40).map((l) => '  ' + l).join('\n')}\n`;
  }
  out += `\nNote: the mechanical brain inspects but does not modify. Re-run with the LLM brain (AGE_API_KEY) for autonomous edits.\n`;
  return out;
}
