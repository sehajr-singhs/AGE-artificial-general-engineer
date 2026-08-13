import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { runEpisode } from '../src/agent.js';
import { makeMechanicalBrain, detectPhysicsDomain, extractParams } from '../src/mechanical.js';
import * as skills from '../src/skills.js';
import { Journal } from '../src/memory.js';
import { extractJSON } from '../src/brain.js';

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'age-test-'));
const silentJournal = (dir) => new Journal(path.join(dir, '.age-test.jsonl'));

test('scaffold + verify mission completes green', async () => {
  const dir = tmp();
  const ep = await runEpisode({
    goal: 'scaffold a new python calculator project called calc',
    dir,
    brain: makeMechanicalBrain(),
    journal: silentJournal(dir),
  });
  assert.equal(ep.status, 'done');
  assert.ok(fs.existsSync(path.join(dir, 'calc', 'calc.py')));
  assert.ok(fs.existsSync(path.join(dir, 'calc', 'test_calc.py')));
  const last = ep.results[ep.results.length - 1];
  assert.equal(last.expect, 'ok');
  assert.ok(last.ok, 'verify step should pass for a pristine scaffold');
});

test('verify step catches broken code (trial-and-error loop)', async () => {
  const dir = tmp();
  await runEpisode({
    goal: 'scaffold a new python calculator project called broken',
    dir,
    brain: makeMechanicalBrain(),
    journal: silentJournal(dir),
  });
  const p = path.join(dir, 'broken', 'calc.py');
  fs.writeFileSync(p, fs.readFileSync(p, 'utf8').replace('return a + b', 'return a - b'));
  const ep = await runEpisode({
    goal: 'run the test suite and check it passes',
    dir: path.join(dir, 'broken'),
    brain: makeMechanicalBrain(),
    journal: silentJournal(dir),
  });
  assert.equal(ep.status, 'failed');
  assert.match(ep.summary, /not complete/i);
  assert.ok(ep.lessons.length >= 1, 'failure should produce a lesson');
});

test('without the gate, broken code is reported as success (control arm)', async () => {
  const dir = tmp();
  await runEpisode({
    goal: 'scaffold a new python calculator project called broken',
    dir,
    brain: makeMechanicalBrain(),
    journal: silentJournal(dir),
  });
  const p = path.join(dir, 'broken', 'calc.py');
  fs.writeFileSync(p, fs.readFileSync(p, 'utf8').replace('return a + b', 'return a - b'));
  const ep = await runEpisode({
    goal: 'run the test suite and check it passes',
    dir: path.join(dir, 'broken'),
    brain: makeMechanicalBrain(),
    journal: silentJournal(dir),
    enforceGate: false,
  });
  // the verifier-free agent claims success on code whose tests actually fail:
  // this is the exact failure mode the gate prevents (verified in the sibling
  // test 'verify step catches broken code')
  assert.equal(ep.status, 'done');
  assert.match(ep.summary, /green/i);
});

test('scaffold refuses to clobber a non-empty dir', async () => {
  const dir = tmp();
  fs.mkdirSync(path.join(dir, 'taken'));
  fs.writeFileSync(path.join(dir, 'taken', 'keep.txt'), 'x');
  const ep = await runEpisode({
    goal: 'scaffold a new node project called taken',
    dir,
    brain: makeMechanicalBrain(),
    journal: silentJournal(dir),
  });
  assert.equal(ep.status, 'failed');
  assert.ok(fs.existsSync(path.join(dir, 'taken', 'keep.txt')));
});

test('explain mission produces an overview', async () => {
  const dir = tmp();
  fs.writeFileSync(path.join(dir, 'README.md'), '# demo project\n\nA tiny demo.\n');
  fs.writeFileSync(path.join(dir, 'main.py'), 'print("hi")\n');
  const ep = await runEpisode({
    goal: 'explain this project',
    dir,
    brain: makeMechanicalBrain(),
    journal: silentJournal(dir),
  });
  assert.equal(ep.status, 'done');
  assert.match(ep.summary, /main\.py/);
  assert.match(ep.summary, /Python/);
});

test('todo scan finds markers', async () => {
  const dir = tmp();
  fs.writeFileSync(path.join(dir, 'a.py'), 'x = 1  # TODO: refactor\n');
  const ep = await runEpisode({
    goal: 'find TODOs in this codebase',
    dir,
    brain: makeMechanicalBrain(),
    journal: silentJournal(dir),
  });
  assert.equal(ep.status, 'done');
  assert.match(ep.summary, /a\.py:1/);
});

test('search skill finds matches with line numbers', () => {
  const dir = tmp();
  fs.writeFileSync(path.join(dir, 'a.txt'), 'hello world\nTODO fix this\n');
  const out = skills.search(dir, { pattern: 'TODO' });
  assert.equal(out.ok, true);
  assert.match(out.output, /a\.txt:2/);
});

test('edit blocks paths outside the working dir', () => {
  const dir = tmp();
  assert.throws(() => skills.edit(dir, { path: '../evil.txt', content: 'x' }));
  assert.throws(() => skills.edit(dir, { path: '/etc/passwd', content: 'x' }));
});

test('run blocks dangerous commands by default', () => {
  const dir = tmp();
  const r = skills.run(dir, { command: 'rm -rf /' });
  assert.equal(r.status, 'blocked');
  assert.equal(r.ok, false);
});

test('run resolves a python interpreter that exists', () => {
  const dir = tmp();
  fs.writeFileSync(path.join(dir, 'x.py'), 'print("hi")\n');
  const r = skills.run(dir, { command: 'python x.py' });
  assert.equal(r.ok, true, r.output);
});

test('extractJSON parses fenced model output', () => {
  const t = 'Sure! Here you go:\n```json\n{"steps":[{"skill":"inspect","args":{}}]}\n```\nDone.';
  assert.deepEqual(JSON.parse(extractJSON(t)), { steps: [{ skill: 'inspect', args: {} }] });
});

test('physx skill solves and verifies a beam design (closed form + numeric)', () => {
  const dir = tmp();
  const out = skills.physx(dir, {
    domain: 'beam',
    params: { L: 4, P: 3000, E: 2e11, I: 5e-6, h: 0.2 },
  });
  assert.equal(out.ok, true, out.output);
  assert.equal(out.data.verified, true);
  assert.ok(Math.abs(out.data.answer - 0.004) < 1e-9, `answer ${out.data.answer}`);
  assert.match(out.output, /question:/);
  const model = path.join('physx', 'models', 'beam.pt');
  if (fs.existsSync(model)) {
    assert.ok(out.data.model_prediction != null, 'trained PhysFormer should predict');
    assert.match(out.output, /PhysFormer prediction/);
  }
});

test('physx skill solves and verifies a cantilever design (closed form + numeric)', () => {
  const dir = tmp();
  const out = skills.physx(dir, {
    domain: 'cantilever',
    params: { L: 4, P: 3000, E: 2e11, I: 5e-6, h: 0.2 },
  });
  assert.equal(out.ok, true, out.output);
  assert.equal(out.data.verified, true);
  assert.ok(Math.abs(out.data.answer - 0.064) < 1e-9, `answer ${out.data.answer}`);
  assert.match(out.output, /question:/);
});

test('mechanical brain runs a beam-design mission end-to-end', async () => {
  const dir = tmp();
  const ep = await runEpisode({
    goal: 'design a simply supported beam with span 4 m, point load 3000 N, modulus 2e11 Pa, inertia 5e-6 m^4, height 0.2 m',
    dir,
    brain: makeMechanicalBrain(),
    journal: silentJournal(dir),
  });
  assert.equal(ep.status, 'done');
  assert.match(ep.summary, /0\.004 m/);
  assert.match(ep.summary, /verified/);
});

test('physics param parser handles key=value and natural language', () => {
  assert.equal(detectPhysicsDomain('design a beam that carries a load'), 'beam');
  assert.equal(detectPhysicsDomain('find the time constant of an RC circuit'), 'rc');
  assert.equal(detectPhysicsDomain('explain this project'), null);
  const nl = extractParams('span 4 m, point load 3000 N, modulus 2e11 Pa, inertia 5e-6 m^4, height 0.2 m', 'beam');
  assert.deepEqual(nl, { L: 4, P: 3000, E: 2e11, I: 5e-6, h: 0.2 });
  const kv = extractParams('R = 1e3, C = 1e-6, V0 = 12', 'rc');
  assert.deepEqual(kv, { R: 1000, C: 1e-6, V0: 12 });
  const proj = extractParams('a projectile launched at velocity 15 m/s and angle 30 deg', 'projectile');
  assert.deepEqual(proj, { v0: 15, angle: 30 });
});

test('journal records episodes and lessons', () => {
  const dir = tmp();
  const j = new Journal(path.join(dir, '.age-test.jsonl'));
  j.append({ goal: 'g', status: 'done', results: [], lessons: ['lesson one'] });
  j.append({ goal: 'g2', status: 'failed', results: [], lessons: ['lesson two'] });
  assert.equal(j.recent(1)[0].goal, 'g2');
  const ls = j.lessons(5);
  assert.equal(ls.length, 2);
  assert.match(ls[0], /lesson one/);
  assert.match(ls[1], /lesson two/);
});
