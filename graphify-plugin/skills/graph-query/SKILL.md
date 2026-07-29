---
name: graph-query
description: "Answer questions from an existing graphify knowledge graph without rebuilding it. Use when graphify-out/ already exists and the user asks how parts of a project relate, wants the path between two concepts, an explanation of one node, or a summary of a community. Cheaper and faster than re-reading source files."
---

# graph-query

Query an existing `graphify-out/` instead of grepping or re-reading the corpus. Rebuild nothing unless the graph is stale.

## Locate the graph

Look for `graphify-out/graph.json` in the project root (or the path the user names). If it is missing, this skill does not apply — run the main `graphify` skill first. If source files changed since the graph was built, refresh cheaply with `graphify update <path>` (code-only, no LLM) before answering.

## Three query shapes

**1. Explain one concept** — what is X and what touches it:

```bash
graphify explain "X" --graph graphify-out/graph.json
```

Returns the node, its source location, community, degree, and every connection with its evidence tag.

**2. Path between two concepts** — how does A reach B:

```bash
graphify path "A" "B" --graph graphify-out/graph.json
```

Returns the shortest chain of nodes and edges. Use it for questions like "how does the checkout touch the discount logic".

**3. Broad questions** — read the graph directly. `graph.json` holds `nodes` (id, source file and line, type, community) and `edges` (source, target, relation, EXTRACTED or INFERRED tag). For "what are the main areas of this project" read `GRAPH_REPORT.md` first — it already names the communities and highlights.

## Answering rules

- Cite the node's source file and line when making a claim about code — every node carries them.
- Distinguish evidence: EXTRACTED edges are literally in the source; INFERRED edges were resolved by graphify. Say which kind supports a claim when it matters.
- If a queried name matches no node, list the closest node ids from graph.json rather than guessing — exact ids beat fuzzy prose.
- Do not silently fall back to reading the whole codebase; the point of the graph is to avoid that. Fall back only when the graph genuinely lacks the answer, and say so.
