"""Standalone sandbox used to execute a student's Python solution.

This file is intentionally dependency-free: it is also packaged as a separate
PyInstaller executable so the frozen exam binary can run submitted code without
requiring Python on the target Linux machine.

Usage::

    exam-runner solution.py input.txt
"""

from __future__ import annotations

import ast
import builtins
import io
import math
import sys
import traceback

ALLOWED_IMPORTS = {"math"}
MAX_OUTPUT = 64 * 1024
FORBIDDEN_NAMES = {
    "__import__",
    "__builtins__",
    "open",
    "exec",
    "eval",
    "compile",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "breakpoint",
    "help",
    "exit",
    "quit",
}
SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "ascii": ascii,
    "bin": bin,
    "bool": bool,
    "bytearray": bytearray,
    "bytes": bytes,
    "chr": chr,
    "complex": complex,
    "dict": dict,
    "divmod": divmod,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "format": format,
    "frozenset": frozenset,
    "hex": hex,
    "int": int,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "iter": iter,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "next": next,
    "object": object,
    "oct": oct,
    "ord": ord,
    "pow": pow,
    "print": print,
    "range": range,
    "reversed": reversed,
    "round": round,
    "set": set,
    "slice": slice,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "type": type,
    "zip": zip,
    "True": True,
    "False": False,
    "None": None,
    "ArithmeticError": ArithmeticError,
    "Exception": Exception,
    "IndexError": IndexError,
    "KeyError": KeyError,
    "RuntimeError": RuntimeError,
    "StopIteration": StopIteration,
    "TypeError": TypeError,
    "ValueError": ValueError,
    "ZeroDivisionError": ZeroDivisionError,
    "__build_class__": builtins.__build_class__,
}


class OutputLimitError(RuntimeError):
    pass


class LimitedWriter(io.TextIOBase):
    def __init__(self, target: io.TextIOBase, limit: int) -> None:
        self.target = target
        self.limit = limit
        self.written = 0

    def write(self, text: str) -> int:
        if not isinstance(text, str):
            text = str(text)
        self.written += len(text)
        if self.written > self.limit:
            raise OutputLimitError("output limit exceeded")
        return self.target.write(text)

    def flush(self) -> None:
        self.target.flush()

    def isatty(self) -> bool:
        return False


def check_ast(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in ALLOWED_IMPORTS:
                    raise PermissionError(f"import {alias.name} is not allowed")
        elif isinstance(node, ast.ImportFrom):
            if node.module not in ALLOWED_IMPORTS:
                raise PermissionError(f"import from {node.module} is not allowed")
        elif isinstance(node, ast.Name):
            if (node.id.startswith("__") and node.id != "__name__") or node.id in FORBIDDEN_NAMES:
                raise PermissionError(f"name {node.id} is not allowed")
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise PermissionError("dunder attributes are not allowed")


def apply_limits() -> None:
    try:
        import resource
    except ImportError:
        return
    limits = [
        (resource.RLIMIT_CPU, (2, 2)),
        (resource.RLIMIT_AS, (384 * 1024 * 1024, 384 * 1024 * 1024)),
        (resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024)),
        (resource.RLIMIT_CORE, (0, 0)),
        (resource.RLIMIT_NPROC, (1, 1)),
    ]
    for which, value in limits:
        try:
            resource.setrlimit(which, value)
        except (ValueError, OSError):
            pass


def build_globals(data: str) -> dict[str, object]:
    lines = data.splitlines()

    def sandbox_input(prompt: str = "") -> str:
        # Prompts are intentionally discarded: they must not pollute stdout.
        if not lines:
            raise EOFError("not enough input data")
        return lines.pop(0)

    safe = dict(SAFE_BUILTINS)
    safe["input"] = sandbox_input
    safe["__import__"] = lambda name, *args, **kwargs: (
        math if name == "math" else (_ for _ in ()).throw(PermissionError(f"import {name} is not allowed"))
    )
    return {"__builtins__": safe, "__name__": "__main__"}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: exam-runner solution.py input.txt", file=sys.stderr)
        return 64
    code_path, input_path = sys.argv[1], sys.argv[2]
    try:
        with open(code_path, encoding="utf-8") as handle:
            code = handle.read()
        with open(input_path, encoding="utf-8") as handle:
            data = handle.read()
    except OSError as exc:
        print(f"cannot read submission: {exc}", file=sys.stderr)
        return 66

    try:
        tree = ast.parse(code, filename="solution.py")
        check_ast(tree)
        compiled = compile(tree, "solution.py", "exec")
    except (SyntaxError, PermissionError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 65

    real_stderr = sys.stderr
    stdout = LimitedWriter(sys.stdout, MAX_OUTPUT)
    sys.stdout = stdout
    sys.stderr = io.StringIO()
    apply_limits()
    try:
        exec(compiled, build_globals(data))  # noqa: S102 - sandboxed namespace
    except OutputLimitError:
        print("output limit exceeded", file=real_stderr)
        return 67
    except BaseException:  # noqa: BLE001 - report any student failure as runtime error
        traceback.print_exc(file=real_stderr)
        return 70
    finally:
        try:
            stdout.flush()
        except Exception:  # noqa: BLE001, S110 - flushing must never mask the result
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
