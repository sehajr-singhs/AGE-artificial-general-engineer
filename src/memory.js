// memory.js — the engineer's episodic memory. Every mission is appended to a
// JSONL journal; lessons learned from failures are replayed into later plans.

import fs from 'node:fs';
import path from 'node:path';

export class Journal {
  constructor(file) {
    this.file = file || process.env.AGE_JOURNAL;
    if (!this.file) {
      this.file = path.join(import.meta.dirname, '..', '.age', 'journal.jsonl');
    }
    fs.mkdirSync(path.dirname(this.file), { recursive: true });
  }

  append(episode) {
    const line = JSON.stringify({ ts: new Date().toISOString(), ...episode });
    fs.appendFileSync(this.file, line + '\n');
  }

  recent(n = 5) {
    if (!fs.existsSync(this.file)) return [];
    const lines = fs.readFileSync(this.file, 'utf8').trim().split('\n').filter(Boolean);
    return lines
      .slice(-n)
      .map((l) => {
        try {
          return JSON.parse(l);
        } catch {
          return null;
        }
      })
      .filter(Boolean);
  }

  lessons(n = 5) {
    return this.recent(n * 3)
      .flatMap((e) => (e.lessons || []).map((l) => `[${e.ts.slice(0, 10)} "${String(e.goal).slice(0, 60)}"] ${l}`))
      .slice(-n);
  }
}
