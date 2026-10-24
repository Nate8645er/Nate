"""Datenmodell des Wissensgraphen: Knoten, Kanten, Persistenz, Navigation."""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field

GRAPH_DIR = ".graphify"
GRAPH_FILE = "graph.json"

# Knoten-Arten
KIND_FILE = "file"
KIND_CLASS = "class"
KIND_FUNCTION = "function"
KIND_METHOD = "method"
KIND_MODULE = "module"

# Herkunft einer Kante: direkt aus dem AST extrahiert oder per
# Namensaufloesung ueber Dateigrenzen hinweg erschlossen.
EXTRACTED = "EXTRACTED"
INFERRED = "INFERRED"


@dataclass
class Node:
    id: str
    name: str
    kind: str
    file: str = ""
    line: int = 0

    @property
    def display(self) -> str:
        """Anzeigename wie im CLI-Output: Funktionen mit (), Methoden mit .()"""
        if self.kind == KIND_FUNCTION:
            return f"{self.name}()"
        if self.kind == KIND_METHOD:
            return f".{self.name.rsplit('.', 1)[-1]}()"
        return self.name


@dataclass
class Edge:
    src: str
    dst: str
    type: str  # imports | defines | inherits | calls | uses | references | method
    origin: str = EXTRACTED  # EXTRACTED | INFERRED


@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    communities: dict[str, int] = field(default_factory=dict)
    root: str = ""

    # ------------------------------------------------------------- Aufbau
    def add_node(self, node: Node) -> Node:
        existing = self.nodes.get(node.id)
        if existing is not None:
            return existing
        self.nodes[node.id] = node
        return node

    def add_edge(self, src: str, dst: str, type: str, origin: str = EXTRACTED) -> None:
        if src == dst or src not in self.nodes or dst not in self.nodes:
            return
        self.edges.append(Edge(src, dst, type, origin))

    def dedupe_edges(self) -> None:
        seen: set[tuple[str, str, str]] = set()
        unique: list[Edge] = []
        for e in self.edges:
            key = (e.src, e.dst, e.type)
            if key in seen:
                continue
            seen.add(key)
            unique.append(e)
        self.edges = unique

    # --------------------------------------------------------- Navigation
    def neighbors(self, node_id: str) -> list[tuple[Edge, str]]:
        """Alle Kanten, die den Knoten beruehren, mit dem jeweils anderen Ende."""
        out: list[tuple[Edge, str]] = []
        for e in self.edges:
            if e.src == node_id:
                out.append((e, e.dst))
            elif e.dst == node_id:
                out.append((e, e.src))
        return out

    def degree(self, node_id: str) -> int:
        return len(self.neighbors(node_id))

    def resolve(self, name: str) -> list[Node]:
        """Findet Knoten anhand eines (Kurz-)Namens.

        Akzeptiert exakte IDs, exakte Namen, Namen ohne Klammern/Punkt
        ("get_request_handler()" == "get_request_handler") sowie den letzten
        Bestandteil qualifizierter Namen ("APIRouter.get" -> "get").
        """
        query = name.strip().strip('"').strip("'")
        query = query.removesuffix("()").lstrip(".")
        if node := self.nodes.get(query):
            return [node]
        exact = [n for n in self.nodes.values() if n.name == query]
        if exact:
            return exact
        tail = [
            n for n in self.nodes.values()
            if n.name.rsplit(".", 1)[-1] == query or os.path.basename(n.name) == query
        ]
        if tail:
            return tail
        lowered = query.lower()
        return [n for n in self.nodes.values() if lowered in n.name.lower()]

    def shortest_path(self, src_id: str, dst_id: str) -> list[tuple[str, Edge | None]] | None:
        """BFS ueber ungerichtete Sicht des Graphen.

        Liefert [(node_id, edge_der_hierher_fuehrte)] — erste Kante ist None.
        """
        if src_id == dst_id:
            return [(src_id, None)]
        adj: dict[str, list[tuple[str, Edge]]] = defaultdict(list)
        for e in self.edges:
            adj[e.src].append((e.dst, e))
            adj[e.dst].append((e.src, e))
        prev: dict[str, tuple[str, Edge]] = {}
        seen = {src_id}
        queue = deque([src_id])
        while queue:
            cur = queue.popleft()
            for nxt, edge in adj[cur]:
                if nxt in seen:
                    continue
                seen.add(nxt)
                prev[nxt] = (cur, edge)
                if nxt == dst_id:
                    path: list[tuple[str, Edge | None]] = []
                    node = dst_id
                    while node != src_id:
                        parent, edge = prev[node]
                        path.append((node, edge))
                        node = parent
                    path.append((src_id, None))
                    path.reverse()
                    return path
                queue.append(nxt)
        return None

    # -------------------------------------------------------- Communities
    def detect_communities(self, rounds: int = 10) -> None:
        """Label-Propagation: architektonische Cluster ohne externe Abhaengigkeiten."""
        order = sorted(self.nodes)
        labels = {nid: i for i, nid in enumerate(order)}
        adj: dict[str, list[str]] = defaultdict(list)
        for e in self.edges:
            adj[e.src].append(e.dst)
            adj[e.dst].append(e.src)
        for _ in range(rounds):
            changed = False
            for nid in order:
                if not adj[nid]:
                    continue
                counts = Counter(labels[n] for n in adj[nid])
                best = min(l for l, c in counts.items() if c == max(counts.values()))
                if labels[nid] != best:
                    labels[nid] = best
                    changed = True
            if not changed:
                break
        renumber: dict[int, int] = {}
        for nid in order:
            renumber.setdefault(labels[nid], len(renumber))
        self.communities = {nid: renumber[labels[nid]] for nid in order}

    # ---------------------------------------------------------- Persistenz
    def save(self, root: str) -> str:
        path = os.path.join(root, GRAPH_DIR)
        os.makedirs(path, exist_ok=True)
        out = os.path.join(path, GRAPH_FILE)
        data = {
            "version": 1,
            "root": self.root,
            "nodes": [vars(n) for n in self.nodes.values()],
            "edges": [vars(e) for e in self.edges],
            "communities": self.communities,
        }
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)
        return out

    @classmethod
    def load(cls, root: str) -> "Graph":
        path = os.path.join(root, GRAPH_DIR, GRAPH_FILE)
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        g = cls(root=data.get("root", root))
        for n in data["nodes"]:
            g.nodes[n["id"]] = Node(**n)
        g.edges = [Edge(**e) for e in data["edges"]]
        g.communities = data.get("communities", {})
        return g

    @staticmethod
    def find_root(start: str = ".") -> str | None:
        """Sucht .graphify/graph.json vom Startverzeichnis aufwaerts."""
        cur = os.path.abspath(start)
        while True:
            if os.path.exists(os.path.join(cur, GRAPH_DIR, GRAPH_FILE)):
                return cur
            parent = os.path.dirname(cur)
            if parent == cur:
                return None
            cur = parent
