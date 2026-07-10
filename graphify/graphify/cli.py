"""Graphify CLI.

    $ graphify scan .
    $ graphify explain "APIRouter"
    $ graphify path "FastAPI" "ModelField"
    $ graphify search "router"
    $ graphify stats
    $ graphify mcp        # MCP-Server fuer Claude Code
"""

from __future__ import annotations

import argparse
import sys
import time

from . import __version__
from .graph import Graph, Node


def _load_graph(start: str = ".") -> Graph:
    root = Graph.find_root(start)
    if root is None:
        sys.exit("Kein Graph gefunden. Zuerst ausfuehren:  graphify scan <projektpfad>")
    return Graph.load(root)


def _pick(graph: Graph, name: str, what: str) -> Node:
    matches = graph.resolve(name)
    if not matches:
        sys.exit(f'Kein Knoten fuer {what} "{name}" gefunden. Tipp: graphify search "{name}"')
    if len(matches) > 1:
        exact = [m for m in matches if m.name == name or m.name.rsplit(".", 1)[-1] == name]
        if len(exact) >= 1:
            return exact[0]
        print(f'"{name}" ist mehrdeutig ({len(matches)} Treffer), nehme ersten:', file=sys.stderr)
        for m in matches[:5]:
            print(f"  - {m.id}", file=sys.stderr)
    return matches[0]


# ---------------------------------------------------------------- Befehle

def cmd_scan(args: argparse.Namespace) -> None:
    from .scanner import scan

    t0 = time.time()
    graph = scan(args.path)
    out = graph.save(graph.root)
    dt = time.time() - t0
    files = sum(1 for n in graph.nodes.values() if n.kind == "file")
    print(f"Scanned {files} files in {dt:.1f}s")
    print(f"{len(graph.nodes)} nodes, {len(graph.edges)} edges, "
          f"{len(set(graph.communities.values()))} communities")
    print(f"Graph saved to {out}")
    print("Done. Query it instead of reading files:")
    print('  graphify explain "<Name>"')
    print('  graphify path "<A>" "<B>"')


def cmd_explain(args: argparse.Namespace) -> None:
    graph = _load_graph()
    node = _pick(graph, args.name, "Knoten")
    neigh = graph.neighbors(node.id)

    print(f"Node: {node.display}")
    print(f"  Source:    {node.file} L{node.line}")
    print(f"  Community: {graph.communities.get(node.id, 0)}")
    print(f"  Degree:    {len(neigh)}")
    print()
    print(f"Connections ({len(neigh)}):")
    shown = 0
    limit = args.limit
    for edge, other_id in sorted(neigh, key=lambda t: (t[0].origin, t[0].type)):
        other = graph.nodes[other_id]
        if edge.src == node.id:
            print(f"  --> {other.display} [{edge.type}] [{edge.origin}]")
        else:
            print(f"  <-- {other.display} [{edge.type}] [{edge.origin}]")
        shown += 1
        if limit and shown >= limit:
            rest = len(neigh) - shown
            if rest > 0:
                print(f"  ... ({rest} more, use --limit 0 for all)")
            break


def cmd_path(args: argparse.Namespace) -> None:
    graph = _load_graph()
    src = _pick(graph, args.src, "Start")
    dst = _pick(graph, args.dst, "Ziel")
    path = graph.shortest_path(src.id, dst.id)
    if path is None:
        sys.exit(f"No path between {src.display} and {dst.display}.")
    hops = len(path) - 1
    print(f"Shortest path ({hops} hops):")
    print(src.display)
    for node_id, edge in path[1:]:
        node = graph.nodes[node_id]
        assert edge is not None
        if edge.dst == node_id:
            print(f"  --{edge.type}--> {node.display}")
        else:
            print(f"  <--{edge.type}-- {node.display}")
    print()
    print(f"{hops} hops. Zero files opened.")


def cmd_search(args: argparse.Namespace) -> None:
    graph = _load_graph()
    matches = graph.resolve(args.query)
    if not matches:
        sys.exit(f'Keine Treffer fuer "{args.query}".')
    for n in matches[: args.limit or None]:
        print(f"{n.display:40s} [{n.kind}]  {n.file} L{n.line}")
    if args.limit and len(matches) > args.limit:
        print(f"... ({len(matches) - args.limit} more)")


def cmd_stats(args: argparse.Namespace) -> None:
    graph = _load_graph()
    kinds: dict[str, int] = {}
    for n in graph.nodes.values():
        kinds[n.kind] = kinds.get(n.kind, 0) + 1
    origins: dict[str, int] = {}
    types: dict[str, int] = {}
    for e in graph.edges:
        origins[e.origin] = origins.get(e.origin, 0) + 1
        types[e.type] = types.get(e.type, 0) + 1
    print(f"Root:        {graph.root}")
    print(f"Nodes:       {len(graph.nodes)}  " +
          " ".join(f"{k}={v}" for k, v in sorted(kinds.items())))
    print(f"Edges:       {len(graph.edges)}  " +
          " ".join(f"{k}={v}" for k, v in sorted(types.items())))
    print(f"Origins:     " + " ".join(f"{k}={v}" for k, v in sorted(origins.items())))
    print(f"Communities: {len(set(graph.communities.values()))}")
    top = sorted(graph.nodes.values(), key=lambda n: graph.degree(n.id), reverse=True)[:10]
    print("Top hubs:")
    for n in top:
        print(f"  {graph.degree(n.id):4d}  {n.display}  ({n.file})")


def cmd_mcp(args: argparse.Namespace) -> None:
    from .mcp_server import serve

    serve()


# ------------------------------------------------------------------ main

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="graphify",
        description="Baut einen Wissensgraphen deiner Codebase — Claude navigiert "
                    "durch den Graphen, statt Dateien neu zu lesen.",
    )
    parser.add_argument("--version", action="version", version=f"graphify {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("scan", help="Codebase einmal scannen und Graph bauen")
    p.add_argument("path", nargs="?", default=".", help="Projektverzeichnis (Default: .)")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("explain", help="Knoten erklaeren: Quelle, Community, Verbindungen")
    p.add_argument("name")
    p.add_argument("--limit", type=int, default=25, help="max. Verbindungen (0 = alle)")
    p.set_defaults(func=cmd_explain)

    p = sub.add_parser("path", help="Kuerzesten Pfad zwischen zwei Knoten finden")
    p.add_argument("src")
    p.add_argument("dst")
    p.set_defaults(func=cmd_path)

    p = sub.add_parser("search", help="Knoten per Name suchen")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("stats", help="Graph-Statistiken anzeigen")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("mcp", help="MCP-Server (stdio) fuer Claude Code starten")
    p.set_defaults(func=cmd_mcp)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
