// skills.js — the engineer's embodiment: sandboxed tools to inspect, edit,
// search, and run code inside the episode's working directory.
//
// Every skill takes (dir, args) and returns { ok, status, output, ... }.
// Writes are confined to `dir`; dangerous shell commands are blocked unless
// AGE_ALLOW_DANGEROUS=1 is set.

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// project root = age/ (skills.js lives in age/src/) — used to reach the
// physx solver and its trained models
const PROJECT_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const MAX_READ = 64 * 1024; // per-file read cap (bytes)
const MAX_SEARCH = 200; // max search hits
const MAX_TREE = 150; // max entries in a file tree
const IGNORED_DIRS = new Set([
  'node_modules', '.git', '.hg', '.svn', '__pycache__', '.venv', 'venv',
  'dist', 'build', 'coverage', '.next', '.age', '.demo', 'target',
]);

// ---------------------------------------------------------------- helpers

export function safeJoin(dir, rel) {
  const root = path.resolve(dir);
  const target = path.resolve(root, rel);
  if (target !== root && !target.startsWith(root + path.sep)) {
    throw new Error(`refusing to touch path outside working dir: ${rel}`);
  }
  return target;
}

function isText(buf) {
  return !buf.subarray(0, 8192).includes(0);
}

export function walk(dir, maxDepth = 8, depth = 0) {
  const out = [];
  if (depth > maxDepth) return out;
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries) {
    if (IGNORED_DIRS.has(e.name)) continue;
    if (e.isDirectory() && e.name.startsWith('.')) continue;
    const full = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...walk(full, maxDepth, depth + 1));
    else out.push(full);
  }
  return out;
}

// ------------------------------------------------------------------ skills

export function tree(dir, { maxDepth = 4, maxEntries = MAX_TREE } = {}) {
  const lines = [];
  let count = 0;
  const render = (d, depth, prefix) => {
    if (count >= maxEntries) return;
    let entries = [];
    try {
      entries = fs.readdirSync(d, { withFileTypes: true });
    } catch {
      return;
    }
    entries = entries.filter(
      (e) => !IGNORED_DIRS.has(e.name) && !(e.isDirectory() && e.name.startsWith('.')),
    );
    entries.sort((a, b) =>
      a.isDirectory() === b.isDirectory()
        ? a.name.localeCompare(b.name)
        : a.isDirectory() ? -1 : 1,
    );
    for (const e of entries) {
      if (count >= maxEntries) return;
      lines.push(
        prefix + (e.isDirectory() ? '[dir] ' : '      ') + e.name + (e.isDirectory() ? '/' : ''),
      );
      count++;
      if (e.isDirectory() && depth < maxDepth) {
        render(path.join(d, e.name), depth + 1, prefix + '  ');
      }
    }
  };
  render(dir, 0, '');
  return lines.join('\n') || '(empty directory)';
}

export function readFile(dir, { path: rel }) {
  const p = safeJoin(dir, rel);
  const st = fs.statSync(p);
  if (st.isDirectory()) return { ok: true, status: 'ok', output: tree(p) };
  const buf = fs.readFileSync(p);
  if (!isText(buf)) {
    return { ok: true, status: 'ok', output: `(binary file, ${st.size} bytes — skipped)` };
  }
  let s = buf.toString('utf8');
  const truncated = s.length > MAX_READ;
  if (truncated) s = s.slice(0, MAX_READ);
  return {
    ok: true,
    status: 'ok',
    output: truncated ? s + '\n… (truncated)' : s,
    truncated,
  };
}

export function inspect(dir, { maxDepth = 3 } = {}) {
  const t = tree(dir, { maxDepth });
  const files = walk(dir).map((f) => path.relative(dir, f).split(path.sep).join('/'));
  const keys = [
    'README.md', 'readme.md', 'README.txt', 'package.json', 'pyproject.toml',
    'requirements.txt', 'go.mod', 'Cargo.toml', 'Makefile', 'tsconfig.json',
  ];
  const body = [];
  for (const k of keys) {
    if (files.includes(k)) {
      try {
        body.push(`\n===== ${k} =====\n${readFile(dir, { path: k }).output}`);
      } catch {
        /* skip unreadable */
      }
    }
  }
  return {
    ok: true,
    status: 'ok',
    output: `${t}\n${body.join('\n')}`,
    files,
  };
}

export function search(dir, { pattern, maxResults = MAX_SEARCH }) {
  let re;
  try {
    re = new RegExp(pattern, 'i');
  } catch (e) {
    return { ok: false, status: 'error', output: `bad regex: ${e.message}` };
  }
  const hits = [];
  for (const f of walk(dir)) {
    let buf;
    try {
      buf = fs.readFileSync(f);
    } catch {
      continue;
    }
    if (!isText(buf)) continue;
    const rel = path.relative(dir, f).split(path.sep).join('/');
    const lines = buf.toString('utf8').split('\n');
    for (let i = 0; i < lines.length; i++) {
      if (re.test(lines[i])) {
        hits.push(`${rel}:${i + 1}: ${lines[i].trim().slice(0, 160)}`);
        if (hits.length >= maxResults) {
          return {
            ok: true,
            status: 'ok',
            output: `search hits for /${pattern}/:\n${hits.join('\n')}\n(truncated at ${maxResults})`,
          };
        }
      }
    }
  }
  return {
    ok: true,
    status: 'ok',
    output: hits.length
      ? `search hits for /${pattern}/:\n${hits.join('\n')}`
      : `no matches for /${pattern}/`,
  };
}

export function edit(dir, { path: rel, content = '', mode = 'replace' }) {
  const p = safeJoin(dir, rel);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  const exists = fs.existsSync(p);
  if (mode === 'create' && exists) {
    return { ok: false, status: 'fail', output: `already exists: ${rel}` };
  }
  if (mode === 'append') fs.appendFileSync(p, content);
  else fs.writeFileSync(p, content);
  const verb = mode === 'create' ? 'created' : mode === 'append' ? 'appended' : exists ? 'rewrote' : 'created';
  return { ok: true, status: 'ok', output: `${verb} ${rel} (${Buffer.byteLength(content)} bytes)` };
}

// --------------------------------------------------------------- execution

const DANGEROUS = /^\s*(rm\s+-rf\s+(\/|~)|git\s+push|git\s+reset\s+--hard|sudo|doas|pkexec|mkfs|dd\s|shutdown|reboot|poweroff|init\s|curl[^\n]*\|\s*(ba)?sh)/i;
const PYTHON_CANDIDATES = ['python3', 'py', 'python'];

// Find a python interpreter that exists on this host (cached).
let _python = null;
export function findPython() {
  if (_python) return _python;
  for (const c of PYTHON_CANDIDATES) {
    const probe = spawnSync(c, ['--version'], { encoding: 'utf8' });
    if (probe.status === 0) {
      _python = c;
      return c;
    }
  }
  _python = 'python';
  return _python;
}

// Rewrite a leading `python` token to an interpreter that exists on this host.
function resolveCommand(command) {
  if (!/^python(\s|$)/.test(command)) return command;
  return command.replace(/^python/, findPython());
}

// Python caches compiled bytecode in __pycache__/*.pyc. A source edit that is
// same-length and lands within the same second as the cached compile is
// invisible to Python's pyc invalidation check (mtime seconds + size), so a
// verify step could run *stale* code and pass broken sources. Purge caches
// under the workdir before any python command so the gate always recompiles
// from source. (Bounded depth; descends into ignored dirs, which walk() skips.)
function purgePythonCaches(root, depth = 0) {
  if (depth > 6) return;
  let entries;
  try {
    entries = fs.readdirSync(root, { withFileTypes: true });
  } catch {
    return;
  }
  for (const e of entries) {
    const full = path.join(root, e.name);
    if (e.isDirectory()) {
      if (e.name === '__pycache__') fs.rmSync(full, { recursive: true, force: true });
      else purgePythonCaches(full, depth + 1);
    }
  }
}

export function run(dir, { command, timeoutMs = 120_000, cwd }) {
  if (!process.env.AGE_ALLOW_DANGEROUS && DANGEROUS.test(command)) {
    return {
      ok: false,
      status: 'blocked',
      output: `blocked dangerous command (set AGE_ALLOW_DANGEROUS=1 to override): ${command}`,
    };
  }
  const workdir = cwd ? safeJoin(dir, cwd) : dir;
  if (/^(python3?|py)(\s|$)/.test(resolveCommand(command))) purgePythonCaches(workdir);
  const res = spawnSync(resolveCommand(command), {
    cwd: workdir,
    shell: true,
    timeout: timeoutMs,
    encoding: 'utf8',
    maxBuffer: 16 * 1024 * 1024,
  });
  if (res.error && (res.error.code === 'ETIMEDOUT' || res.signal === 'SIGTERM')) {
    return { ok: false, status: 'timeout', output: `timed out after ${timeoutMs}ms` };
  }
  const output = [res.stdout, res.stderr].filter(Boolean).join('').trim().slice(-6000) || '(no output)';
  return { ok: res.status === 0, status: res.status === 0 ? 'ok' : 'fail', code: res.status, output };
}

export function verify(dir, args) {
  return run(dir, args);
}

// ------------------------------------------------------------- physics

// physx — the physics-engineering skill. Delegates to physx/solve.py, which
// computes the closed-form answer, verifies it against an independent numeric
// simulation, and (when a trained PhysFormer exists) predicts it with the
// physics-adjusted transformer. Spawned without a shell so JSON args never
// hit shell quoting (cross-platform safe).
export function physx(dir, { domain, params = {} } = {}) {
  // standalone repos keep the physics core under src/physx
  const solvePy = ['physx', 'src/physx']
    .map((p) => path.join(PROJECT_ROOT, p, 'solve.py'))
    .find((p) => fs.existsSync(p));
  if (!solvePy) {
    return { ok: false, status: 'fail', output: `physx solver not found (expected ${path.join(PROJECT_ROOT, 'physx', 'solve.py')})` };
  }
  const blob = JSON.stringify({ domain, params });
  const res = spawnSync(findPython(), [solvePy, '--json', blob], {
    encoding: 'utf8',
    timeout: 120_000,
    maxBuffer: 16 * 1024 * 1024,
  });
  if (res.error) {
    return { ok: false, status: 'error', output: `physx solver failed: ${res.error.message}` };
  }
  let data = null;
  const stdout = (res.stdout || '').trim();
  try {
    data = JSON.parse(stdout);
  } catch {
    /* fall through to error */
  }
  if (!data || data.error) {
    const tail = (stdout + '\n' + (res.stderr || '')).trim().slice(-800) || '(no output)';
    return { ok: false, status: 'fail', output: `physx solver error: ${tail}` };
  }
  const lines = [
    `domain: ${data.domain}`,
    `question: ${data.question}`,
    `answer: ${data.answer} ${data.unit}`,
    `verified by independent numeric simulation: ${data.verified} (relative residual ${data.residual})`,
  ];
  if (data.extras && Object.keys(data.extras).length) {
    lines.push(`extras: ${JSON.stringify(data.extras)}`);
  }
  if (data.model_prediction != null) {
    lines.push(
      `PhysFormer prediction: ${data.model_prediction} ${data.unit} ` +
        `(physics residual ${data.model_residual})`,
    );
  }
  return { ok: true, status: 'ok', output: lines.join('\n'), data };
}
