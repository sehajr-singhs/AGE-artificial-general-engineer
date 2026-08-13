// templates.js — scaffold templates the mechanical brain can materialize.
// Each template ships with a test suite so the agent can *verify* its work
// (trial-and-error: scaffold -> run tests -> green? done : fix and retry).

export const TEMPLATES = {
  python: {
    id: 'python',
    label: 'Python',
    verify: 'python -m unittest discover -s . -p "test_*.py"',
    files: {
      'calc.py': `"""A tiny calculator CLI — scaffolded by AGE (Artificial General Engineer)."""
import sys


def add(a, b):
    return a + b


def sub(a, b):
    return a - b


def mul(a, b):
    return a * b


def div(a, b):
    if b == 0:
        raise ValueError("division by zero")
    return a / b


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 3:
        print("usage: calc.py <a> <op> <b>   (op in + - * /)")
        return 2
    try:
        a, op, b = float(argv[0]), argv[1], float(argv[2])
    except ValueError:
        print("error: numbers please")
        return 2
    ops = {"+": add, "-": sub, "*": mul, "/": div}
    if op not in ops:
        print(f"error: unknown operator {op!r}")
        return 2
    print(ops[op](a, b))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
`,
      'test_calc.py': `import unittest

from calc import add, div, mul, sub


class TestCalc(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_sub(self):
        self.assertEqual(sub(10, 4), 6)

    def test_mul(self):
        self.assertEqual(mul(3, 7), 21)

    def test_div(self):
        self.assertEqual(div(9, 3), 3)
        with self.assertRaises(ValueError):
            div(1, 0)


if __name__ == "__main__":
    unittest.main()
`,
      'README.md': `# {NAME}

A calculator project scaffolded by [AGE](https://github.com/yourfork/age) — an Artificial General Engineer.

## Run

    python calc.py 2 + 3

## Test

    python -m unittest discover -s . -p "test_*.py"
`,
    },
  },

  node: {
    id: 'node',
    label: 'Node.js',
    verify: 'node --test',
    files: {
      'package.json': `{
  "name": "{NAME}",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "test": "node --test"
  }
}
`,
      'calc.js': `// A tiny calculator — scaffolded by AGE (Artificial General Engineer).
import { pathToFileURL } from 'node:url';

export function add(a, b) { return a + b; }
export function sub(a, b) { return a - b; }
export function mul(a, b) { return a * b; }
export function div(a, b) {
  if (b === 0) throw new Error('division by zero');
  return a / b;
}

const isMain = process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href;
if (isMain) {
  const [a, op, b] = process.argv.slice(2);
  const ops = { '+': add, '-': sub, '*': mul, '/': div };
  const x = Number(a);
  const y = Number(b);
  if (Number.isNaN(x) || Number.isNaN(y) || !(op in ops)) {
    console.error('usage: node calc.js <a> <op> <b>   (op in + - * /)');
    process.exit(2);
  }
  console.log(ops[op](x, y));
}
`,
      'test/calc.test.js': `import { test } from 'node:test';
import assert from 'node:assert/strict';
import { add, div, mul, sub } from '../calc.js';

test('add', () => assert.equal(add(2, 3), 5));
test('sub', () => assert.equal(sub(10, 4), 6));
test('mul', () => assert.equal(mul(3, 7), 21));
test('div', () => {
  assert.equal(div(9, 3), 3);
  assert.throws(() => div(1, 0));
});
`,
      'README.md': `# {NAME}

A calculator project scaffolded by [AGE](https://github.com/yourfork/age) — an Artificial General Engineer.

## Run

    node calc.js 2 + 3

## Test

    npm test
`,
    },
  },

  go: {
    id: 'go',
    label: 'Go',
    verify: 'go test ./...',
    files: {
      'go.mod': `module {NAME}

go 1.22
`,
      'calc.go': `// Package calc is a tiny calculator — scaffolded by AGE (Artificial General Engineer).
package calc

import "errors"

func Add(a, b float64) float64 { return a + b }
func Sub(a, b float64) float64 { return a - b }
func Mul(a, b float64) float64 { return a * b }

func Div(a, b float64) (float64, error) {
	if b == 0 {
		return 0, errors.New("division by zero")
	}
	return a / b, nil
}
`,
      'calc_test.go': `package calc

import "testing"

func TestAdd(t *testing.T) {
	if Add(2, 3) != 5 {
		t.Fatal("Add(2, 3) != 5")
	}
}

func TestSub(t *testing.T) {
	if Sub(10, 4) != 6 {
		t.Fatal("Sub(10, 4) != 6")
	}
}

func TestMul(t *testing.T) {
	if Mul(3, 7) != 21 {
		t.Fatal("Mul(3, 7) != 21")
	}
}

func TestDiv(t *testing.T) {
	if v, err := Div(9, 3); err != nil || v != 3 {
		t.Fatalf("Div(9, 3) = %v, %v", v, err)
	}
	if _, err := Div(1, 0); err == nil {
		t.Fatal("expected error for Div(1, 0)")
	}
}
`,
      'README.md': `# {NAME}

A calculator project scaffolded by [AGE](https://github.com/yourfork/age) — an Artificial General Engineer.

## Test

    go test ./...
`,
    },
  },
};

// --- goal parsing (mechanical brain) -----------------------------------

const LANG_RE = /(golang|python|node(?:\.?js)?|javascript|\bjs\b|typescript)|(?:in\s+(?:the\s+)?|\b)go\s+(project|app|repo|module|cli)/i;

export function parseLang(goal) {
  const m = goal.match(LANG_RE);
  if (!m) return 'python';
  if (m[2]) return 'go';
  const w = (m[1] || '').toLowerCase();
  if (w.includes('py')) return 'python';
  if (/node|js|javascript|ts/.test(w)) return 'node';
  if (w === 'golang') return 'go';
  return 'python';
}

export function parseName(goal) {
  const m = goal.match(/(?:called|named)\s+["']?([A-Za-z0-9_.-]+)/i);
  return m ? m[1] : 'age-app';
}
