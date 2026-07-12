# Graph Report - .  (2026-07-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 42 nodes · 53 edges · 12 communities (5 shown, 7 thin omitted)
- Extraction: 58% EXTRACTED · 42% INFERRED · 0% AMBIGUOUS · INFERRED: 22 edges (avg confidence: 0.92)
- Token cost: 72,069 input · 292 output

## Graph Freshness
- Built from commit: `e8d8317d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Graphify Skill & Docs
- ULTRA Team Orchestration
- ULTRA Review & QA
- ULTRA Enterprise OS Core
- ULTRA Docs Agent
- ULTRA Architect Agent
- ULTRA Business Agent
- ULTRA Data/ML Agent
- ULTRA Design Agent
- ULTRA DevOps Agent
- ULTRA Fullstack Agent
- ULTRA Security Agent

## God Nodes (most connected - your core abstractions)
1. `ULTRA AI ENTERPRISE OS README` - 14 edges
2. `graphify skill` - 10 edges
3. `/ultra-review command (plugin source)` - 5 edges
4. `/ultra-review command` - 4 edges
5. `/ultra-team command (plugin source)` - 4 edges
6. `ultra-enterprise-os skill (plugin source)` - 4 edges
7. `/ultra-team command` - 3 edges
8. `ultra-enterprise-os skill` - 3 edges
9. `ULTRA OS role catalog (org-chart)` - 3 edges
10. `ultra-architect agent (plugin source)` - 3 edges

## Surprising Connections (you probably didn't know these)
- `Graphify Project Rules (root CLAUDE.md)` --conceptually_related_to--> `graphify skill`  [INFERRED]
  CLAUDE.md → .claude/skills/graphify/SKILL.md
- `ultra-architect agent` --shares_data_with--> `ultra-architect agent (plugin source)`  [INFERRED]
  .claude/agents/ultra-architect.md → ultra-enterprise-os/agents/ultra-architect.md
- `ultra-business agent` --shares_data_with--> `ultra-business agent (plugin source)`  [INFERRED]
  .claude/agents/ultra-business.md → ultra-enterprise-os/agents/ultra-business.md
- `ultra-data-ml agent` --shares_data_with--> `ultra-data-ml agent (plugin source)`  [INFERRED]
  .claude/agents/ultra-data-ml.md → ultra-enterprise-os/agents/ultra-data-ml.md
- `ultra-design agent` --shares_data_with--> `ultra-design agent (plugin source)`  [INFERRED]
  .claude/agents/ultra-design.md → ultra-enterprise-os/agents/ultra-design.md

## Hyperedges (group relationships)
- **ULTRA AI ENTERPRISE OS virtual organization** — claude_skills_ultra_enterprise_os_skill_ultra_enterprise_os, claude_agents_ultra_orchestrator_ultra_orchestrator, claude_agents_ultra_architect_ultra_architect, claude_agents_ultra_fullstack_ultra_fullstack, claude_agents_ultra_devops_ultra_devops, claude_agents_ultra_security_ultra_security, claude_agents_ultra_qa_ultra_qa, claude_agents_ultra_data_ml_ultra_data_ml, claude_agents_ultra_design_ultra_design, claude_agents_ultra_business_ultra_business, claude_agents_ultra_docs_ultra_docs [INFERRED 0.80]
- **ULTRA OS command interface** — claude_commands_ultra_ultra, claude_commands_ultra_team_ultra_team, claude_commands_ultra_review_ultra_review [EXTRACTED 0.90]
- **graphify extraction and query pipeline** — claude_skills_graphify_skill_graphify, claude_skills_graphify_references_extraction_spec_extraction_spec, claude_skills_graphify_references_query_query, claude_skills_graphify_references_update_update, claude_skills_graphify_references_exports_exports, claude_skills_graphify_references_add_watch_add_watch, claude_skills_graphify_references_github_and_merge_github_and_merge, claude_skills_graphify_references_hooks_hooks, claude_skills_graphify_references_transcribe_transcribe [EXTRACTED 0.90]

## Communities (12 total, 7 thin omitted)

### Community 0 - "Graphify Skill & Docs"
Cohesion: 0.18
Nodes (11): Graphify Skill Trigger (.claude/CLAUDE.md), Graphify Project Rules (root CLAUDE.md), graphify add/watch reference, graphify exports reference, graphify extraction subagent spec, graphify GitHub clone/merge reference, graphify hooks/CLAUDE.md integration reference, graphify query/path/explain reference (+3 more)

### Community 1 - "ULTRA Team Orchestration"
Cohesion: 0.47
Nodes (6): ultra-orchestrator agent, /ultra-team command, ULTRA OS role catalog (org-chart), ultra-orchestrator agent (plugin source), /ultra-team command (plugin source), ULTRA OS role catalog (plugin source)

### Community 2 - "ULTRA Review & QA"
Cohesion: 0.67
Nodes (4): ultra-qa agent, /ultra-review command, ultra-qa agent (plugin source), /ultra-review command (plugin source)

### Community 3 - "ULTRA Enterprise OS Core"
Cohesion: 0.67
Nodes (4): /ultra command, ultra-enterprise-os skill, /ultra command (plugin source), ultra-enterprise-os skill (plugin source)

### Community 4 - "ULTRA Docs Agent"
Cohesion: 0.67
Nodes (3): ultra-docs agent, ultra-docs agent (plugin source), ULTRA AI ENTERPRISE OS README

## Knowledge Gaps
- **16 isolated node(s):** `Graphify Project Rules (root CLAUDE.md)`, `Graphify Skill Trigger (.claude/CLAUDE.md)`, `ultra-business agent`, `ultra-data-ml agent`, `ultra-design agent` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ULTRA AI ENTERPRISE OS README` connect `ULTRA Docs Agent` to `ULTRA Team Orchestration`, `ULTRA Review & QA`, `ULTRA Enterprise OS Core`, `ULTRA Architect Agent`, `ULTRA Business Agent`, `ULTRA Data/ML Agent`, `ULTRA Design Agent`, `ULTRA DevOps Agent`, `ULTRA Fullstack Agent`, `ULTRA Security Agent`?**
  _High betweenness centrality (0.451) - this node is a cross-community bridge._
- **Why does `ultra-enterprise-os skill (plugin source)` connect `ULTRA Enterprise OS Core` to `ULTRA Team Orchestration`, `ULTRA Docs Agent`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `/ultra-team command (plugin source)` connect `ULTRA Team Orchestration` to `ULTRA Docs Agent`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `/ultra-review command (plugin source)` (e.g. with `/ultra-review command` and `ultra-architect agent (plugin source)`) actually correct?**
  _`/ultra-review command (plugin source)` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `/ultra-review command` (e.g. with `ultra-architect agent` and `ultra-qa agent`) actually correct?**
  _`/ultra-review command` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Graphify Project Rules (root CLAUDE.md)`, `Graphify Skill Trigger (.claude/CLAUDE.md)`, `ultra-business agent` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._