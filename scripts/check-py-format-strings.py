# -*- coding: utf-8 -*-
"""Catch "%"-format calls whose placeholders outnumber their arguments.

WHY THIS EXISTS
---------------
On 2026-11-11 three translation runs died with

    TypeError: not enough arguments for format string

inside a timing print. The exception was raised AFTER the translations
finished, so a whole tool's ten languages were thrown away - and the runner
had already moved on to the next tool. Nothing in the output said "this run
is void"; it said "failed" and the next tool started.

A "%"-format call with more conversions than arguments is a pure static
property. It can be proven without running the code, and it must fail the
build, because the cost of missing it is measured in hours of gateway time.

WHAT IS CHECKED
---------------
Every `print(...)` call whose first positional argument is `LITERAL % ARGS`,
where LITERAL is a string literal (adjacent string literals are already
folded into one Constant by the parser).

The argument side is resolved through the enclosing scopes:

* a tuple literal            -> its length
* a name bound to a tuple    -> that tuple's length
* a name bound to anything else -> 1
* anything else              -> 1

When a name cannot be resolved (a function parameter, a global), the call is
counted as UNKNOWN and reported in the summary. It is never a failure: a
gate that fires on 170-odd known-fine lines is a gate nobody reads.

CONVERSION COUNTING
-------------------
The scanner follows CPython's own rules: a mapping key in parentheses, the
flag set, width, precision and length modifiers, then exactly one
conversion character. `%%` is a literal percent sign and is NOT a
conversion, and neither is the text that follows it.

NEGATIVE CONTROL
----------------
`--negative-control` writes a known-bad format call to a temp file and
asserts that this checker reports it. A checker that cannot fail proves
nothing.
"""

import argparse
import ast
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONV_CHARS = "diouxXeEfFgGcrsa"
FLAG_CHARS = "+- #0"


def count_conversions(fmt):
    """Number of real conversions in a format string.

    Mirrors CPython: "%%" is a literal percent and the text after it is
    literal too, so "%%-format" contributes zero conversions.
    """
    n = 0
    i = 0
    length = len(fmt)
    while i < length:
        if fmt[i] != "%":
            i += 1
            continue
        if i + 1 < length and fmt[i + 1] == "%":
            i += 2
            continue
        j = i + 1
        if j < length and fmt[j] == "(":
            k = fmt.find(")", j)
            if k == -1:
                return n
            j = k + 1
        while j < length and fmt[j] in FLAG_CHARS:
            j += 1
        while j < length and (fmt[j].isdigit() or fmt[j] == "*"):
            j += 1
        if j < length and fmt[j] == ".":
            j += 1
            while j < length and (fmt[j].isdigit() or fmt[j] == "*"):
                j += 1
        while j < length and fmt[j] in "hlL":
            j += 1
        if j < length and fmt[j] in CONV_CHARS:
            n += 1
            i = j + 1
        else:
            i += 1
    return n


def value_shape(node, scopes):
    """How this node behaves as the right side of a "%" operation.

    Returns (kind, count) where kind is:

      "tuple"   -> count values, and "%" will try to use every one of them
      "single"  -> exactly one value
      "unknown" -> cannot be proven (an expression may be a tuple at runtime)

    "%" formatting has TWO ways to fail, not one:

      * fewer values than conversions -> "not enough arguments"
      * more values than conversions  -> "not all arguments converted"

    So a tuple is only safe when its length is EXACTLY the conversion count,
    and a single value is only safe with exactly one conversion.
    """
    if isinstance(node, (ast.Tuple, ast.List)):
        return ("tuple", len(node.elts))
    if isinstance(node, ast.Name):
        for scope in reversed(scopes):
            if node.id in scope:
                return scope[node.id]
        return ("unknown", None)
    return ("unknown", None)


def collect_bindings(body):
    """name -> (kind, count) for names bound by simple assignments.

    A scalar literal is definitely one value. An expression is NOT: it may
    evaluate to a tuple at runtime, so its shape stays unknown.
    """
    out = {}
    for node in ast.walk(body):
        targets = []
        value = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        else:
            continue
        if value is None:
            continue
        if isinstance(value, (ast.Tuple, ast.List)):
            shape = ("tuple", len(value.elts))
        elif isinstance(value, ast.Constant):
            shape = ("single", 1)
        else:
            continue
        for tgt in targets:
            if isinstance(tgt, ast.Name):
                out[tgt.id] = shape
    return out


def judge(fmt, need, shape):
    """Return a defect description, or None when the call is provably safe."""
    kind, count = shape
    if kind == "unknown":
        return "unknown"
    if kind == "tuple":
        if count < need:
            return ("%d conversions but only %d argument(s) in the tuple: %r"
                    % (need, count, fmt[:70]))
        if count > need:
            return ("%d conversion(s) but the tuple carries %d value(s), "
                    "so Python raises 'not all arguments converted': %r"
                    % (need, count, fmt[:70]))
        return None
    if need > 1:
        return ("%d conversions but one argument: %r" % (need, fmt[:70]))
    return None


def check_function(fn, label, findings, unknown, outer):
    scopes = [outer, collect_bindings(fn)]
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not (isinstance(f, ast.Name) and f.id == "print"):
            continue
        if not node.args:
            continue
        first = node.args[0]
        if not isinstance(first, ast.BinOp) or not isinstance(first.op, ast.Mod):
            continue
        fmt_node = first.left
        if not isinstance(fmt_node, ast.Constant):
            continue
        if not isinstance(fmt_node.value, str):
            continue
        fmt = fmt_node.value
        need = count_conversions(fmt)
        if need == 0:
            continue
        shape = value_shape(first.right, scopes)
        verdict = judge(fmt, need, shape)
        if verdict == "unknown":
            unknown.append((label, first.lineno, fmt))
        elif verdict:
            findings.append((label, first.lineno, verdict))


def check_module(tree, label, findings, unknown):
    module_scope = collect_bindings(tree)
    scopes = [module_scope]
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not (isinstance(f, ast.Name) and f.id == "print"):
            continue
        if not node.args:
            continue
        first = node.args[0]
        if not isinstance(first, ast.BinOp) or not isinstance(first.op, ast.Mod):
            continue
        fmt_node = first.left
        if not isinstance(fmt_node, ast.Constant):
            continue
        if not isinstance(fmt_node.value, str):
            continue
        fmt = fmt_node.value
        need = count_conversions(fmt)
        if need == 0:
            continue
        shape = value_shape(first.right, scopes)
        verdict = judge(fmt, need, shape)
        if verdict == "unknown":
            unknown.append((label, first.lineno, fmt))
        elif verdict:
            findings.append((label, first.lineno, verdict))
    for fn in tree.body:
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            check_function(fn, label, findings, unknown, module_scope)


def scan(paths):
    findings = []
    unknown = []
    for path in paths:
        try:
            with open(path, "rb") as fh:
                src = fh.read()
            tree = ast.parse(src, filename=path)
        except (OSError, SyntaxError) as exc:
            findings.append((path, 0, "cannot parse: %s" % exc))
            continue
        check_module(tree, path, findings, unknown)
    # The module pass walks function bodies too, so the same call can be
    # reported twice. One line is one defect.
    seen = set()
    deduped = []
    for item in findings:
        key = (item[0], item[1])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped, unknown


def collect_files(roots):
    out = []
    for root in roots:
        if os.path.isfile(root):
            out.append(root)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if d not in (".git", "node_modules", "__pycache__",
                                        ".tmp", "i18n", "vendor")]
            for fn in filenames:
                if fn.endswith(".py"):
                    out.append(os.path.join(dirpath, fn))
    return out


NEGATIVE_CONTROL = (
    # 1) the historical crash: 6 conversions, 5 values.
    "def a(target):\n"
    "    print('    [%s] %d strings, %d batches, %d repairs, "
    "translate %.0fs, verify %.0fs' % (target, 1, 2, 3, 4.0))\n"
    # 2) the sibling failure: one conversion, two values in the tuple.
    "def b():\n"
    "    print('  the output decodes: %s' % (100, 200))\n"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*",
                    help="files or directories to scan")
    ap.add_argument("--negative-control", action="store_true",
                    help="prove the checker can fail")
    ap.add_argument("--show-unknown", action="store_true",
                    help="list the calls whose argument count is unprovable")
    args = ap.parse_args()

    roots = args.paths or [os.path.join(ROOT, "scripts")]
    files = collect_files(roots)
    findings, unknown = scan(files)

    if args.negative_control:
        tmp = tempfile.mkdtemp(prefix="fmtstr-neg-")
        try:
            bad = os.path.join(tmp, "bad.py")
            with open(bad, "w", encoding="utf-8") as fh:
                fh.write(NEGATIVE_CONTROL)
            nf, _ = scan([bad])
            if len(nf) < 2:
                print("[FAIL] negative control: expected 2 findings in the "
                      "known-bad file (too few arguments AND too many "
                      "arguments), got %d - the checker cannot fail, so its "
                      "zero means nothing." % len(nf))
                return 1
            print("[OK] negative control: the checker reported %d finding(s) "
                  "in the known-bad file (both failure shapes)." % len(nf))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    if args.show_unknown:
        print("-- unprovable calls (first 40) --")
        for label, lineno, fmt in unknown[:40]:
            print("   %s:%s  %r" % (label, lineno, fmt[:60]))

    if findings:
        print("[FAIL] %d format-string problem(s):" % len(findings))
        for label, lineno, detail in findings:
            print("   %s:%s  %s" % (label, lineno, detail))
        return 1

    print("[OK] %d python file(s) scanned, %d format-string defect(s), "
          "%d call(s) whose argument count could not be proven (not a failure)."
          % (len(files), len(findings), len(unknown)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
