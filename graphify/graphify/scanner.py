"""Scanner: laeuft einmal ueber die komplette Code-Base und baut den Graphen.

Python wird vollstaendig ueber den AST analysiert (EXTRACTED-Kanten).
Referenzen ueber Dateigrenzen hinweg werden per globaler Namensaufloesung
verbunden (INFERRED-Kanten). JavaScript/TypeScript wird heuristisch
per Regex erfasst.
"""

from __future__ import annotations

import ast
import os
import re
from collections import defaultdict

from .graph import (
    EXTRACTED,
    INFERRED,
    KIND_CLASS,
    KIND_FILE,
    KIND_FUNCTION,
    KIND_METHOD,
    Graph,
    Node,
)

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".graphify", "__pycache__", "node_modules",
    ".venv", "venv", "env", ".tox", ".mypy_cache", ".pytest_cache",
    "dist", "build", ".eggs", "site-packages", ".next", ".cache",
}

PY_EXT = {".py"}
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

# Python-Builtins, die als Referenzziele nur Rauschen waeren
_NOISE = {
    "print", "len", "str", "int", "float", "bool", "list", "dict", "set",
    "tuple", "type", "super", "isinstance", "issubclass", "range", "repr",
    "object", "Exception", "ValueError", "TypeError", "KeyError",
    "RuntimeError", "AttributeError", "NotImplementedError", "StopIteration",
    "enumerate", "zip", "map", "filter", "sorted", "reversed", "getattr",
    "setattr", "hasattr", "delattr", "id", "hash", "iter", "next", "vars",
    "min", "max", "sum", "abs", "round", "open", "staticmethod",
    "classmethod", "property", "self", "cls", "None", "True", "False",
    "bytes", "frozenset", "callable", "format", "any", "all", "input",
}


def scan(root: str) -> Graph:
    """Baut den kompletten Wissensgraphen fuer ein Projektverzeichnis."""
    root = os.path.abspath(root)
    graph = Graph(root=root)
    py_files: list[str] = []
    js_files: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for fn in sorted(filenames):
            ext = os.path.splitext(fn)[1]
            full = os.path.join(dirpath, fn)
            if ext in PY_EXT:
                py_files.append(full)
            elif ext in JS_EXT:
                js_files.append(full)

    # Phase 1: Definitionen + AST-Kanten (EXTRACTED)
    collector = _PyCollector(graph, root)
    for path in py_files:
        collector.collect_definitions(path)
    for path in js_files:  # Dateiknoten zuerst, damit Import-Kanten aufloesbar sind
        rel = os.path.relpath(path, root)
        graph.add_node(Node(id=rel, name=os.path.basename(rel), kind=KIND_FILE, file=rel, line=1))
    for path in js_files:
        _collect_js(graph, root, path)

    # Phase 2: Referenzen aufloesen (imports -> EXTRACTED, Namensmatch -> INFERRED)
    collector.link_references()

    graph.dedupe_edges()
    graph.detect_communities()
    return graph


# --------------------------------------------------------------------------
# Python (AST)
# --------------------------------------------------------------------------

class _PyCollector:
    def __init__(self, graph: Graph, root: str):
        self.graph = graph
        self.root = root
        # globaler Namensindex: Kurzname -> [node_id, ...]
        self.by_name: dict[str, list[str]] = defaultdict(list)
        # pro Datei: gesammelte Namensreferenzen (name -> nutzende node_id)
        self.pending: list[tuple[str, str, str]] = []  # (src_node, ref_name, edge_type)
        # pro Datei: explizit importierte Namen -> Modulpfad
        self.imports_in_file: dict[str, dict[str, str]] = defaultdict(dict)

    def rel(self, path: str) -> str:
        return os.path.relpath(path, self.root)

    def collect_definitions(self, path: str) -> None:
        rel = self.rel(path)
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                source = fh.read()
            tree = ast.parse(source, filename=rel)
        except (SyntaxError, OSError):
            return

        file_node = self.graph.add_node(
            Node(id=rel, name=os.path.basename(rel), kind=KIND_FILE, file=rel, line=1)
        )
        self._register(file_node)
        visitor = _DefVisitor(self, rel, file_node.id)
        visitor.visit(tree)

    def _register(self, node: Node) -> None:
        short = node.name.rsplit(".", 1)[-1]
        self.by_name[short].append(node.id)
        if node.kind == KIND_FILE:
            base = os.path.splitext(os.path.basename(node.name))[0]
            self.by_name[base].append(node.id)

    def link_references(self) -> None:
        """Phase 2: Namensreferenzen gegen den globalen Index aufloesen."""
        for src_id, ref, edge_type in self.pending:
            if ref in _NOISE:
                continue
            targets = self.by_name.get(ref, [])
            src = self.graph.nodes[src_id]
            # bevorzugt Ziel in derselben Datei (EXTRACTED, direkt sichtbar)
            same_file = [t for t in targets if self.graph.nodes[t].file == src.file]
            if same_file:
                self.graph.add_edge(src_id, same_file[0], edge_type, EXTRACTED)
                continue
            # explizit importierter Name -> EXTRACTED
            imported_from = self.imports_in_file.get(src.file, {}).get(ref)
            if imported_from is not None:
                for t in targets:
                    if self.graph.nodes[t].file == imported_from:
                        self.graph.add_edge(src_id, t, edge_type, EXTRACTED)
                        break
                else:
                    if len(targets) == 1:
                        self.graph.add_edge(src_id, targets[0], edge_type, INFERRED)
                continue
            # eindeutiger globaler Treffer -> INFERRED
            others = [t for t in targets if self.graph.nodes[t].file != src.file]
            if len(others) == 1:
                self.graph.add_edge(src_id, others[0], edge_type, INFERRED)


class _DefVisitor(ast.NodeVisitor):
    """Sammelt Klassen, Funktionen, Methoden, Imports und Referenzen einer Datei."""

    def __init__(self, collector: _PyCollector, rel: str, file_id: str):
        self.c = collector
        self.rel = rel
        self.file_id = file_id
        self.scope: list[str] = []  # Stack der umgebenden Knoten-IDs
        self.class_stack: list[str] = []

    # ------------------------------------------------------------ Helfer
    def _current(self) -> str:
        return self.scope[-1] if self.scope else self.file_id

    def _qual(self, name: str) -> str:
        prefix = ".".join(n for n in self.class_stack)
        return f"{prefix}.{name}" if prefix else name

    def _add_ref(self, name: str, edge_type: str) -> None:
        self.c.pending.append((self._current(), name, edge_type))

    # ----------------------------------------------------------- Imports
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._add_ref(alias.name.split(".")[0], "imports")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module_file = self._resolve_module(node)
        for alias in node.names:
            if alias.name == "*":
                continue
            self._add_ref(alias.name, "imports")
            if module_file:
                self.c.imports_in_file[self.rel][alias.asname or alias.name] = module_file
        self.generic_visit(node)

    def _resolve_module(self, node: ast.ImportFrom) -> str | None:
        """Mappt ein from-Import-Modul auf eine relative Datei im Projekt."""
        parts = (node.module or "").split(".") if node.module else []
        if node.level:  # relativer Import
            base = os.path.dirname(self.rel)
            for _ in range(node.level - 1):
                base = os.path.dirname(base)
            candidate_parts = ([base] if base else []) + parts
        else:
            candidate_parts = parts
        if not candidate_parts:
            return None
        stem = os.path.join(*candidate_parts)
        for candidate in (f"{stem}.py", os.path.join(stem, "__init__.py")):
            if candidate in self.c.graph.nodes:
                return candidate
        return None

    # -------------------------------------------------------- Definitionen
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qual = self._qual(node.name)
        nid = f"{self.rel}::{qual}"
        cls = self.c.graph.add_node(
            Node(id=nid, name=qual, kind=KIND_CLASS, file=self.rel, line=node.lineno)
        )
        self.c._register(cls)
        self.c.graph.add_edge(self.file_id, nid, "defines", EXTRACTED)
        for base in node.bases:
            base_name = _base_name(base)
            if base_name:
                self.c.pending.append((nid, base_name, "inherits"))
        for dec in node.decorator_list:
            name = _base_name(dec)
            if name:
                self.c.pending.append((nid, name, "uses"))
        self.scope.append(nid)
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()
        self.scope.pop()

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qual = self._qual(node.name)
        kind = KIND_METHOD if self.class_stack else KIND_FUNCTION
        nid = f"{self.rel}::{qual}"
        fn = self.c.graph.add_node(
            Node(id=nid, name=qual, kind=kind, file=self.rel, line=node.lineno)
        )
        self.c._register(fn)
        owner = self._current()
        self.c.graph.add_edge(owner, nid, "method" if kind == KIND_METHOD else "defines", EXTRACTED)
        for dec in node.decorator_list:
            name = _base_name(dec)
            if name:
                self.c.pending.append((nid, name, "uses"))
        for arg_node in _annotations(node):
            name = _base_name(arg_node)
            if name:
                self.c.pending.append((nid, name, "uses"))
        self.scope.append(nid)
        self.generic_visit(node)
        self.scope.pop()

    visit_FunctionDef = _visit_function
    visit_AsyncFunctionDef = _visit_function

    # ---------------------------------------------------------- Referenzen
    def visit_Call(self, node: ast.Call) -> None:
        name = _base_name(node.func)
        if name:
            self._add_ref(name, "calls")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self._add_ref(node.id, "references")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if isinstance(node.ctx, ast.Load):
            self._add_ref(node.attr, "uses")
        self.generic_visit(node)


def _base_name(node: ast.AST) -> str | None:
    """Extrahiert den relevanten Namen aus Name/Attribute/Call/Subscript."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Call):
        return _base_name(node.func)
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.rsplit(".", 1)[-1]  # String-Annotation "pkg.Klasse"
    return None


def _annotations(node: ast.FunctionDef | ast.AsyncFunctionDef):
    args = node.args
    for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
        if a.annotation is not None:
            yield a.annotation
    if args.vararg and args.vararg.annotation:
        yield args.vararg.annotation
    if args.kwarg and args.kwarg.annotation:
        yield args.kwarg.annotation
    if node.returns is not None:
        yield node.returns


# --------------------------------------------------------------------------
# JavaScript / TypeScript (heuristisch)
# --------------------------------------------------------------------------

_JS_CLASS = re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)(?:\s+extends\s+([A-Za-z_$][\w$.]*))?")
_JS_FUNC = re.compile(
    r"(?:^|\s)(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)"
    r"|(?:^|\s)(?:export\s+)?const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[\w$]+)\s*=>",
    re.MULTILINE,
)
_JS_IMPORT = re.compile(r"""import\s+(?:[^'"]+\s+from\s+)?['"]([^'"]+)['"]""")


def _collect_js(graph: Graph, root: str, path: str) -> None:
    rel = os.path.relpath(path, root)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            source = fh.read()
    except OSError:
        return

    file_node = graph.add_node(
        Node(id=rel, name=os.path.basename(rel), kind=KIND_FILE, file=rel, line=1)
    )

    for m in _JS_CLASS.finditer(source):
        line = source.count("\n", 0, m.start()) + 1
        nid = f"{rel}::{m.group(1)}"
        graph.add_node(Node(id=nid, name=m.group(1), kind=KIND_CLASS, file=rel, line=line))
        graph.add_edge(file_node.id, nid, "defines", EXTRACTED)

    for m in _JS_FUNC.finditer(source):
        name = m.group(1) or m.group(2)
        if not name:
            continue
        line = source.count("\n", 0, m.start()) + 1
        nid = f"{rel}::{name}"
        graph.add_node(Node(id=nid, name=name, kind=KIND_FUNCTION, file=rel, line=line))
        graph.add_edge(file_node.id, nid, "defines", EXTRACTED)

    for m in _JS_IMPORT.finditer(source):
        spec = m.group(1)
        if not spec.startswith("."):
            continue
        base = os.path.normpath(os.path.join(os.path.dirname(rel), spec))
        for candidate in [base] + [base + ext for ext in sorted(JS_EXT)] + [
            os.path.join(base, "index" + ext) for ext in sorted(JS_EXT)
        ]:
            if candidate in graph.nodes:
                graph.add_edge(file_node.id, candidate, "imports", INFERRED)
                break
