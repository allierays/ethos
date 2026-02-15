# Ethos x Claude Code: Deep Integration Strategy

## MCP, Hooks, Skills, Subagents, and the Agent SDK

**Purpose:** Research document for the "Built with Opus 4.6" Claude Code Hackathon (Feb 10-16, 2026). This covers every integration surface between Ethos (an open-source ethical knowledge graph for AI agents) and the Claude Code ecosystem, with code examples and a strategic plan for maximizing hackathon impact.

---

## Table of Contents

1. [The Strategic Angle](#1-the-strategic-angle)
2. [MCP (Model Context Protocol)](#2-mcp-model-context-protocol)
3. [Building the Ethos MCP Server in Python](#3-building-the-ethos-mcp-server-in-python)
4. [Claude Code Hooks](#4-claude-code-hooks)
5. [Claude Code Skills](#5-claude-code-skills)
6. [Claude Code Subagents](#6-claude-code-subagents)
7. [Claude Agent SDK](#7-claude-agent-sdk)
8. [MCP + Neo4j Integration Patterns](#8-mcp--neo4j-integration-patterns)
9. [Existing MCP Server Patterns](#9-existing-mcp-server-patterns)
10. [The Full Integration Architecture](#10-the-full-integration-architecture)
11. [Implementation Priority](#11-implementation-priority)
12. [Sources](#12-sources)

---

## 1. The Strategic Angle

### Hackathon Context

The "Built with Opus 4.6" hackathon runs February 10-16, 2026 with $100K in API credits as prizes. Six judges from the Claude team (Boris Cherny, Cat Wu, Thariq Shihpar, Lydia Hallie, Ado Kukic, Jason Bigman) evaluate based on **technical innovation**, **implementation quality**, and **potential impact**. Projects demonstrating creative applications of Claude's capabilities -- particularly the 1M-token context window and 128K-token output -- with a clear and functional objective score highest.

Special prizes include "Most Creative Opus 4.6 Exploration" ($5K) and "The Keep Thinking Prize" ($5K), suggesting extended thinking / deep reasoning is valued.

### Why Deep Claude Code Integration Wins

The hackathon literally has a live session on "Tips and Tricks on new Claude Code MCP, Agent Skills, Claude Code Hooks." This signals that the judges want to see projects that leverage the full Claude Code platform, not just raw API calls. Here is why Ethos is positioned perfectly:

1. **MCP Server = Universal Adoption**: By building Ethos as an MCP server, any Claude Code or Claude Desktop user can add ethical evaluation to their workflow with a single config line. This is not a standalone app -- it is infrastructure.

2. **Hooks = Automatic Guardrails**: A `PreToolUse` hook that evaluates every agent action through Ethos before it executes is a novel safety pattern. No other MCP server does real-time ethical evaluation.

3. **Skills = User Accessibility**: `/ethos-evaluate` as a slash command makes the knowledge graph queryable by any user, no API knowledge required.

4. **Subagents = Ethical Oversight Architecture**: An Ethos subagent that runs in parallel with other agents, providing continuous ethical monitoring, demonstrates a new paradigm for AI safety.

5. **Agent SDK = Middleware for Production**: Ethos as SDK middleware means every agent built with the Claude Agent SDK can have ethical evaluation baked in.

**The pitch: Ethos is the first open-source ethical knowledge graph that integrates at every layer of the Claude Code stack -- MCP for tools, hooks for guardrails, skills for accessibility, subagents for oversight, and the Agent SDK for production pipelines.**

---

## 2. MCP (Model Context Protocol)

### What It Is

MCP is an open standard introduced by Anthropic in November 2024 (donated to the Linux Foundation's Agentic AI Foundation in December 2025) that standardizes how AI systems integrate with external tools, data sources, and services. It follows a client-server architecture using JSON-RPC 2.0.

### Architecture

```
┌─────────────────────────────────────────────┐
│  MCP Host (Claude Code, Claude Desktop)     │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │MCP Client│  │MCP Client│  │MCP Client│  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │              │              │        │
└───────┼──────────────┼──────────────┼────────┘
        │              │              │
  ┌─────┴─────┐  ┌─────┴─────┐  ┌────┴──────┐
  │Ethos MCP  │  │GitHub MCP │  │Neo4j MCP  │
  │Server     │  │Server     │  │Server     │
  └─────┬─────┘  └───────────┘  └───────────┘
        │
  ┌─────┴─────┐
  │Neo4j Graph│
  │Database   │
  └───────────┘
```

### Core Primitives

MCP servers expose three types of capabilities:

| Primitive | Description | Ethos Use Case |
|-----------|-------------|----------------|
| **Tools** | Executable functions the LLM can invoke | `evaluate_message`, `query_ethical_framework`, `get_manipulation_score` |
| **Resources** | Data sources providing contextual information | Ethical framework documentation, manipulation pattern database |
| **Prompts** | Reusable templates for structured interactions | "Evaluate this text for manipulation", "Score ethical alignment" |

### Transport Options

- **STDIO** (Standard Input/Output): For local integrations where server runs on same machine. Best for Claude Code CLI usage.
- **HTTP+SSE** (Streamable HTTP): For remote/cloud deployments. Best for shared team servers.

### Why Ethos Should Be an MCP Server

Making Ethos an MCP server is the single highest-impact design decision because:

1. **Zero-friction adoption**: Any Claude Code user adds one JSON block to their config
2. **Universal compatibility**: Works with Claude Desktop, Cursor, VS Code, Windsurf, and any MCP-compatible client
3. **Tool discovery**: Claude automatically sees Ethos tools and can use them when relevant
4. **No code changes**: Users do not modify their workflow; Ethos tools appear alongside their existing tools

### Configuration for Claude Code

Users would add Ethos to their `~/.claude/settings.json` or project `.claude/settings.json`:

```json
{
  "mcpServers": {
    "ethos": {
      "command": "uv",
      "args": ["--directory", "/path/to/ethos", "run", "ethos-mcp-server"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password"
      }
    }
  }
}
```

Or with pip-installed package:

```json
{
  "mcpServers": {
    "ethos": {
      "command": "ethos-mcp-server",
      "env": {
        "NEO4J_URI": "bolt://localhost:7687"
      }
    }
  }
}
```

---

## 3. Building the Ethos MCP Server in Python

### Using FastMCP (Official Python SDK)

FastMCP is the standard way to build MCP servers in Python. It was incorporated into the official MCP SDK and uses a decorator pattern that auto-generates tool definitions from type hints and docstrings.

#### Installation

```bash
uv add "mcp[cli]" neo4j
# or
pip install "mcp[cli]" neo4j
```

#### Core Server Implementation

```python
# ethos_academy/mcp_server.py
import json
import logging
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP
from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "ethos",
    description="Ethical knowledge graph for AI agent evaluation"
)

# Neo4j connection (configured via environment variables)
driver = None

async def get_driver():
    """Lazy initialization of Neo4j driver."""
    global driver
    if driver is None:
        import os
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    return driver


# ─────────────────────────────────────────────
# TOOLS: Functions the LLM can invoke
# ─────────────────────────────────────────────

@mcp.tool()
async def evaluate_message(
    message: str,
    context: Optional[str] = None,
    framework: str = "aristotelian"
) -> str:
    """Evaluate a message for ethical alignment and manipulation patterns.

    Analyzes text against the Ethos ethical knowledge graph, checking for
    manipulation techniques, logical fallacies, dark patterns, and
    rhetorical manipulation. Returns a structured evaluation with scores.

    Args:
        message: The text message to evaluate
        context: Optional context about the conversation or situation
        framework: Ethical framework to use (aristotelian, utilitarian, deontological, virtue)
    """
    db = await get_driver()
    async with db.session() as session:
        # Query the knowledge graph for matching manipulation patterns
        result = await session.run("""
            MATCH (t:Technique)-[:USES]->(p:Pattern)
            WHERE ANY(keyword IN $keywords
                WHERE toLower(t.description) CONTAINS toLower(keyword))
            OPTIONAL MATCH (t)-[:VIOLATES]->(principle:EthicalPrinciple)
            OPTIONAL MATCH (t)-[:CATEGORY]->(cat:Category)
            RETURN t.name AS technique,
                   t.severity AS severity,
                   t.description AS description,
                   collect(DISTINCT principle.name) AS violated_principles,
                   collect(DISTINCT cat.name) AS categories,
                   collect(DISTINCT p.name) AS patterns
            ORDER BY t.severity DESC
            LIMIT 10
        """, keywords=_extract_keywords(message))

        techniques = [record.data() async for record in result]

        # Calculate composite scores
        evaluation = {
            "message_preview": message[:200],
            "framework": framework,
            "manipulation_score": _calc_manipulation_score(techniques),
            "detected_techniques": techniques,
            "ethical_concerns": _aggregate_concerns(techniques),
            "recommendation": _generate_recommendation(techniques, framework),
            "confidence": _calc_confidence(techniques, message)
        }

        return json.dumps(evaluation, indent=2)


@mcp.tool()
async def query_ethical_framework(
    framework: str,
    topic: Optional[str] = None
) -> str:
    """Query the ethical knowledge graph for framework information.

    Retrieves principles, rules, and guidance from a specific ethical
    framework stored in the Ethos knowledge graph.

    Args:
        framework: The ethical framework (aristotelian, utilitarian, deontological, virtue, care)
        topic: Optional topic to focus the query on
    """
    db = await get_driver()
    async with db.session() as session:
        query = """
            MATCH (f:Framework {name: $framework})-[:CONTAINS]->(p:Principle)
            OPTIONAL MATCH (p)-[:APPLIES_TO]->(d:Domain)
            RETURN p.name AS principle,
                   p.description AS description,
                   collect(DISTINCT d.name) AS domains
            ORDER BY p.name
        """
        result = await session.run(query, framework=framework)
        principles = [record.data() async for record in result]

        return json.dumps({
            "framework": framework,
            "principles": principles,
            "total_principles": len(principles)
        }, indent=2)


@mcp.tool()
async def detect_manipulation_patterns(message: str) -> str:
    """Detect specific manipulation and persuasion patterns in text.

    Checks text against a database of known manipulation techniques including
    dark patterns, logical fallacies, social engineering tactics, emotional
    manipulation, and deceptive framing.

    Args:
        message: The text to analyze for manipulation patterns
    """
    db = await get_driver()
    async with db.session() as session:
        result = await session.run("""
            MATCH (t:Technique)-[:HAS_INDICATOR]->(i:Indicator)
            WHERE ANY(indicator IN i.phrases
                WHERE toLower($message) CONTAINS toLower(indicator))
            OPTIONAL MATCH (t)-[:CATEGORY]->(cat:Category)
            RETURN t.name AS technique,
                   t.severity AS severity,
                   t.description AS description,
                   collect(DISTINCT i.phrases) AS matched_indicators,
                   collect(DISTINCT cat.name) AS categories
            ORDER BY t.severity DESC
        """, message=message)

        patterns = [record.data() async for record in result]

        return json.dumps({
            "message_analyzed": message[:200],
            "patterns_detected": len(patterns),
            "patterns": patterns,
            "risk_level": _calc_risk_level(patterns)
        }, indent=2)


@mcp.tool()
async def get_societal_benefit_score(
    action_description: str,
    stakeholders: Optional[list[str]] = None
) -> str:
    """Calculate a societal benefit score for a proposed action or output.

    Evaluates an action against multiple ethical dimensions: harm prevention,
    fairness, transparency, autonomy preservation, and social good.

    Args:
        action_description: Description of the action or output to evaluate
        stakeholders: Optional list of affected stakeholders to consider
    """
    db = await get_driver()
    async with db.session() as session:
        result = await session.run("""
            MATCH (d:Dimension)
            OPTIONAL MATCH (d)-[:HAS_CRITERIA]->(c:Criteria)
            RETURN d.name AS dimension,
                   d.weight AS weight,
                   collect({name: c.name, description: c.description}) AS criteria
        """)

        dimensions = [record.data() async for record in result]

        return json.dumps({
            "action": action_description[:300],
            "stakeholders": stakeholders or ["general public"],
            "dimensions": dimensions,
            "overall_score_guidance": (
                "Use these dimensions to evaluate the action. "
                "Score each 0-10, weight by importance, and compute overall."
            )
        }, indent=2)


@mcp.tool()
async def log_ethical_decision(
    decision: str,
    reasoning: str,
    framework_used: str,
    score: float,
    context: Optional[str] = None
) -> str:
    """Log an ethical decision to the knowledge graph for auditing.

    Creates an audit trail of ethical evaluations performed, enabling
    transparency and accountability in AI agent decision-making.

    Args:
        decision: The decision that was made
        reasoning: The ethical reasoning behind it
        framework_used: Which ethical framework was applied
        score: The ethical alignment score (0.0-1.0)
        context: Optional additional context
    """
    db = await get_driver()
    async with db.session() as session:
        result = await session.run("""
            CREATE (d:Decision {
                decision: $decision,
                reasoning: $reasoning,
                framework: $framework_used,
                score: $score,
                context: $context,
                timestamp: datetime()
            })
            RETURN d.timestamp AS logged_at
        """,
            decision=decision,
            reasoning=reasoning,
            framework_used=framework_used,
            score=score,
            context=context
        )

        record = await result.single()
        return json.dumps({
            "status": "logged",
            "logged_at": str(record["logged_at"]),
            "decision_preview": decision[:200]
        }, indent=2)


# ─────────────────────────────────────────────
# RESOURCES: Data the LLM can read
# ─────────────────────────────────────────────

@mcp.resource("ethos://frameworks")
async def list_frameworks() -> str:
    """List all ethical frameworks in the knowledge graph."""
    db = await get_driver()
    async with db.session() as session:
        result = await session.run("""
            MATCH (f:Framework)
            RETURN f.name AS name, f.description AS description
            ORDER BY f.name
        """)
        frameworks = [record.data() async for record in result]
        return json.dumps(frameworks, indent=2)


@mcp.resource("ethos://techniques")
async def list_manipulation_techniques() -> str:
    """List all known manipulation techniques in the knowledge graph."""
    db = await get_driver()
    async with db.session() as session:
        result = await session.run("""
            MATCH (t:Technique)
            OPTIONAL MATCH (t)-[:CATEGORY]->(cat:Category)
            RETURN t.name AS name,
                   t.severity AS severity,
                   collect(DISTINCT cat.name) AS categories
            ORDER BY t.severity DESC
        """)
        techniques = [record.data() async for record in result]
        return json.dumps(techniques, indent=2)


# ─────────────────────────────────────────────
# PROMPTS: Reusable evaluation templates
# ─────────────────────────────────────────────

@mcp.prompt()
def ethical_review_prompt(text: str) -> str:
    """Generate a prompt for comprehensive ethical review of text."""
    return f"""Please perform a comprehensive ethical review of the following text
using the Ethos knowledge graph tools available to you.

Text to evaluate:
---
{text}
---

Steps:
1. Use `evaluate_message` to get an overall ethical alignment score
2. Use `detect_manipulation_patterns` to check for manipulation techniques
3. Use `query_ethical_framework` to reference relevant ethical principles
4. Synthesize findings into a clear report with:
   - Overall ethical alignment score (0-100)
   - Detected manipulation techniques (if any)
   - Ethical concerns by framework
   - Specific recommendations for improvement
"""


# ─────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────

def _extract_keywords(message: str) -> list[str]:
    """Extract relevant keywords for graph matching."""
    # Simple keyword extraction; could be enhanced with NLP
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                  "being", "have", "has", "had", "do", "does", "did", "will",
                  "would", "could", "should", "may", "might", "can", "shall",
                  "to", "of", "in", "for", "on", "with", "at", "by", "from",
                  "it", "this", "that", "and", "or", "but", "not", "no", "if"}
    words = message.lower().split()
    return [w.strip(".,!?;:\"'()[]{}") for w in words
            if w.strip(".,!?;:\"'()[]{}") not in stop_words and len(w) > 2]


def _calc_manipulation_score(techniques: list[dict]) -> float:
    """Calculate a 0-100 manipulation score based on detected techniques."""
    if not techniques:
        return 0.0
    total_severity = sum(t.get("severity", 0) for t in techniques)
    max_possible = len(techniques) * 10
    return round(min((total_severity / max(max_possible, 1)) * 100, 100), 1)


def _calc_risk_level(patterns: list[dict]) -> str:
    """Determine risk level from detected patterns."""
    if not patterns:
        return "low"
    max_severity = max(p.get("severity", 0) for p in patterns)
    if max_severity >= 8 or len(patterns) >= 5:
        return "critical"
    elif max_severity >= 6 or len(patterns) >= 3:
        return "high"
    elif max_severity >= 4 or len(patterns) >= 2:
        return "medium"
    return "low"


def _aggregate_concerns(techniques: list[dict]) -> list[str]:
    """Aggregate ethical concerns from techniques."""
    concerns = set()
    for t in techniques:
        for principle in t.get("violated_principles", []):
            concerns.add(f"Violates: {principle}")
    return sorted(concerns)


def _generate_recommendation(techniques: list[dict], framework: str) -> str:
    """Generate a recommendation based on analysis."""
    if not techniques:
        return "No ethical concerns detected. Message appears aligned with ethical principles."
    severity = max(t.get("severity", 0) for t in techniques)
    if severity >= 8:
        return "CRITICAL: This message contains severe manipulation patterns. Do not proceed without significant revision."
    elif severity >= 5:
        return "WARNING: Moderate ethical concerns detected. Review and address before proceeding."
    return "NOTICE: Minor ethical considerations found. Review the detected patterns."


def _calc_confidence(techniques: list[dict], message: str) -> float:
    """Calculate confidence in the evaluation."""
    if not techniques:
        return 0.5  # Medium confidence when nothing detected
    # More techniques found = higher confidence
    base = min(len(techniques) / 5, 1.0) * 0.7
    # Longer messages give more signal
    length_factor = min(len(message) / 500, 1.0) * 0.3
    return round(base + length_factor, 2)


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    """Run the Ethos MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

#### Package Entry Point

In `pyproject.toml`:

```toml
[project.scripts]
ethos-mcp-server = "ethos.mcp_server:main"
```

---

## 4. Claude Code Hooks

### What Hooks Are

Hooks are user-defined shell commands (or prompt/agent evaluations) that execute at specific points in Claude Code's lifecycle. They provide **deterministic** control over Claude Code's behavior -- ensuring certain actions always happen rather than relying on the LLM to choose them.

### All Available Hook Events

| Event | When It Fires | Ethos Use Case |
|-------|---------------|----------------|
| `SessionStart` | Session begins or resumes | Load ethical context, inject Ethos guidelines |
| `UserPromptSubmit` | User submits a prompt | Pre-screen user input for manipulation |
| `PreToolUse` | Before a tool call executes (can block) | **Evaluate every agent action before execution** |
| `PermissionRequest` | Permission dialog appears | Add ethical context to permission decisions |
| `PostToolUse` | After a tool call succeeds | Log ethical audit trail of actions taken |
| `PostToolUseFailure` | After a tool call fails | Track failed ethical evaluations |
| `Notification` | Claude sends a notification | Alert on ethical violations |
| `SubagentStart` | Subagent is spawned | Inject ethical context into subagents |
| `SubagentStop` | Subagent finishes | Evaluate subagent output |
| `Stop` | Claude finishes responding | **Final ethical review of complete response** |
| `TeammateIdle` | Agent team member about to idle | N/A |
| `TaskCompleted` | Task marked as completed | Final audit of completed work |
| `PreCompact` | Before context compaction | Preserve ethical context |
| `SessionEnd` | Session terminates | Generate ethical session report |

### Hook Types

1. **`command`**: Runs a shell command. Communicates via stdin (JSON input), stdout (output), stderr (error messages), and exit codes.
2. **`prompt`**: Single-turn LLM evaluation (Haiku by default). Returns `{ok: true/false, reason: "..."}`.
3. **`agent`**: Multi-turn subagent with tool access for verification. Same output format as prompt hooks.

### Exit Codes

- **Exit 0**: Action proceeds. Stdout content added to Claude's context (for `UserPromptSubmit` and `SessionStart`).
- **Exit 2**: Action **blocked**. Stderr message fed back to Claude as feedback.
- **Any other**: Action proceeds. Stderr logged but not shown to Claude.

### The Killer Feature: Ethos as a PreToolUse Hook

This is the most powerful integration point. A `PreToolUse` hook that evaluates every agent action through the Ethos knowledge graph before it executes:

#### Hook Script: `.claude/hooks/ethos-evaluate.sh`

```bash
#!/bin/bash
# ethos-evaluate.sh - Evaluate agent actions through Ethos knowledge graph
# Runs before every tool use in Claude Code

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input | tostring')

# Skip evaluation for read-only tools (performance optimization)
if [[ "$TOOL_NAME" == "Read" || "$TOOL_NAME" == "Glob" || "$TOOL_NAME" == "Grep" ]]; then
    exit 0
fi

# Call the Ethos evaluation API
RESULT=$(python3 -c "
import json, sys
sys.path.insert(0, '$CLAUDE_PROJECT_DIR')
from ethos_academy.evaluator import quick_evaluate

tool_name = '$TOOL_NAME'
tool_input = json.loads('$TOOL_INPUT')

result = quick_evaluate(tool_name, tool_input)
print(json.dumps(result))
" 2>/dev/null)

if [ $? -ne 0 ]; then
    # If evaluation fails, allow the action (fail-open)
    exit 0
fi

RISK_LEVEL=$(echo "$RESULT" | jq -r '.risk_level')
REASON=$(echo "$RESULT" | jq -r '.reason')

if [[ "$RISK_LEVEL" == "critical" ]]; then
    echo "ETHICAL VIOLATION: $REASON" >&2
    exit 2  # Block the action
elif [[ "$RISK_LEVEL" == "high" ]]; then
    # Output structured JSON to escalate to user
    echo "{
        \"hookSpecificOutput\": {
            \"hookEventName\": \"PreToolUse\",
            \"permissionDecision\": \"ask\",
            \"permissionDecisionReason\": \"Ethos ethical concern: $REASON\"
        }
    }"
    exit 0
fi

exit 0
```

#### Hook Configuration: `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ethos-evaluate.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash|Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq '{tool: .tool_name, input: .tool_input, result: .tool_output}' >> \"$CLAUDE_PROJECT_DIR\"/.ethos/audit-log.jsonl"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Review the conversation for ethical concerns. Check if any responses contained manipulation, deception, or harmful content. If concerns exist, respond with {\"ok\": false, \"reason\": \"description of concern\"}. If the response is ethically sound, respond with {\"ok\": true}."
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Ethos ethical knowledge graph is active. All tool uses will be evaluated for ethical alignment. Use /ethos-evaluate for manual evaluation.'"
          }
        ]
      }
    ]
  }
}
```

#### Agent-Based Hook for Deep Evaluation

For the `Stop` hook, use an agent-based hook that can actually query the Ethos knowledge graph:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "agent",
            "prompt": "You are the Ethos ethical evaluator. Use the Ethos MCP tools (evaluate_message, detect_manipulation_patterns) to review Claude's complete response for ethical concerns. If the response is ethically sound, respond {\"ok\": true}. If there are concerns, respond {\"ok\": false, \"reason\": \"specific concerns found\"}. $ARGUMENTS",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

---

## 5. Claude Code Skills

### What Skills Are

Skills extend what Claude can do. They are Markdown files with YAML frontmatter stored in `.claude/skills/` directories. The name becomes a `/slash-command`. Claude can auto-discover and use them when relevant, or users invoke them directly.

### Skill Structure

```
.claude/skills/
  ethos-evaluate/
    SKILL.md              # Main instructions (required)
    templates/
      evaluation.md       # Evaluation template
    examples/
      sample-report.md    # Example output
```

### The `/ethos-evaluate` Skill

```yaml
# .claude/skills/ethos-evaluate/SKILL.md
---
name: ethos-evaluate
description: Evaluate text for ethical alignment, manipulation patterns, and societal benefit using the Ethos knowledge graph. Use when reviewing content for ethical concerns, checking for manipulation, or when the user asks about ethical implications.
argument-hint: "[text or file path to evaluate]"
---

# Ethos Ethical Evaluation

Evaluate the provided text using the Ethos ethical knowledge graph.

## Steps

1. **Use `mcp__ethos__evaluate_message`** to get an overall ethical alignment assessment
   - Pass the text as the `message` parameter
   - Use "aristotelian" framework by default unless the user specifies otherwise

2. **Use `mcp__ethos__detect_manipulation_patterns`** to check for specific manipulation techniques
   - This checks against a database of known manipulation patterns
   - Pay special attention to any patterns with severity >= 7

3. **Synthesize findings** into a clear report:

### Report Format

**Ethical Evaluation Report**

| Dimension | Score | Details |
|-----------|-------|---------|
| Manipulation Risk | 0-100 | Summary of detected techniques |
| Ethical Alignment | 0-100 | Based on framework evaluation |
| Transparency | 0-100 | Honesty and disclosure assessment |
| Autonomy Respect | 0-100 | Whether it respects reader autonomy |

**Detected Patterns:** List any manipulation techniques found
**Ethical Concerns:** Specific principles violated
**Recommendations:** Actionable suggestions for improvement

## Arguments

Evaluate: $ARGUMENTS
```

### The `/ethos-audit` Skill (Session Audit)

```yaml
# .claude/skills/ethos-audit/SKILL.md
---
name: ethos-audit
description: Generate an ethical audit report for the current session. Reviews all actions taken and evaluates them against ethical frameworks.
disable-model-invocation: true
context: fork
agent: Explore
---

# Ethos Session Audit

Generate a comprehensive ethical audit of the current session.

## Steps

1. Read the audit log at `.ethos/audit-log.jsonl` if it exists
2. Use `mcp__ethos__query_ethical_framework` to load the relevant framework
3. For each logged action, evaluate ethical implications
4. Generate a summary report including:
   - Total actions reviewed
   - Actions flagged for ethical concerns
   - Overall ethical alignment score
   - Recommendations for future sessions

## Output

Write the report to `.ethos/audit-reports/session-{timestamp}.md`
```

### The `/ethos-framework` Skill (Browse Knowledge Graph)

```yaml
# .claude/skills/ethos-framework/SKILL.md
---
name: ethos-framework
description: Browse and query the Ethos ethical knowledge graph. Explore ethical frameworks, manipulation techniques, and societal benefit criteria.
argument-hint: "[framework name or 'list' to see all]"
---

# Ethos Framework Explorer

Browse the Ethos ethical knowledge graph.

If $ARGUMENTS is "list" or empty, use `mcp__ethos__query_ethical_framework` to
list all available frameworks.

Otherwise, query the specific framework named in $ARGUMENTS and present:
- Core principles
- Application domains
- Related manipulation techniques that violate this framework
- Practical guidance for AI agents

Format the output as a clear, readable reference guide.
```

---

## 6. Claude Code Subagents

### What Subagents Are

Subagents are specialized AI assistants that handle specific task types. Each runs in its own context window with a custom system prompt, specific tool access, and independent permissions. Claude delegates to them based on their description field.

### Key Features for Ethos

- **Context isolation**: Ethical evaluation happens in a separate context, keeping the main conversation clean
- **Tool restrictions**: Subagent can be limited to read-only + Ethos MCP tools
- **Parallel execution**: Multiple evaluations can run concurrently
- **Persistent memory**: Learns ethical patterns across sessions

### The Ethos Ethics Evaluator Subagent

```yaml
# .claude/agents/ethos-evaluator.md
---
name: ethos-evaluator
description: >
  Ethical evaluation specialist using the Ethos knowledge graph.
  Use proactively to evaluate any content, code, or agent output for
  ethical alignment, manipulation patterns, and societal benefit.
  Delegates to this agent whenever ethical review is needed.
tools: Read, Grep, Glob
mcpServers:
  - ethos
model: sonnet
permissionMode: dontAsk
memory: user
maxTurns: 20
---

You are the Ethos Ethics Evaluator, a specialized agent for ethical
analysis powered by the Ethos knowledge graph.

## Your Role

You evaluate text, code, and agent outputs for:
- **Manipulation techniques**: Dark patterns, social engineering, emotional manipulation
- **Logical fallacies**: Strawman, ad hominem, false dichotomy, etc.
- **Ethical alignment**: Against major ethical frameworks (Aristotelian, utilitarian, deontological, virtue, care ethics)
- **Societal benefit**: Net positive or negative impact on society
- **Transparency**: Honesty, disclosure, informed consent

## Evaluation Process

1. Use `mcp__ethos__evaluate_message` for overall assessment
2. Use `mcp__ethos__detect_manipulation_patterns` for technique detection
3. Use `mcp__ethos__query_ethical_framework` when deeper framework analysis is needed
4. Use `mcp__ethos__log_ethical_decision` to record your evaluation for auditing

## Output Format

Always provide:
- A clear risk level: LOW / MEDIUM / HIGH / CRITICAL
- Specific techniques detected with severity scores
- Violated ethical principles
- Actionable recommendations
- A confidence score for your assessment

## Memory Management

After each evaluation, update your agent memory with:
- New patterns discovered
- Common manipulation techniques in this codebase/project
- Framework preferences of the user
- Any false positives to avoid in the future
```

### The Ethos Guardian Subagent (Continuous Monitoring)

```yaml
# .claude/agents/ethos-guardian.md
---
name: ethos-guardian
description: >
  Continuous ethical monitoring agent. Runs in background to monitor
  agent outputs and flag ethical concerns in real-time. Use when you
  want ongoing ethical oversight of a complex multi-step task.
tools: Read, Grep, Glob
mcpServers:
  - ethos
model: haiku
permissionMode: dontAsk
maxTurns: 50
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: >
            Before stopping, check if there are any unreviewed items in
            the audit log. If so, respond with {"ok": false, "reason":
            "Unreviewed ethical items remain"}. Otherwise {"ok": true}.
---

You are the Ethos Guardian, a lightweight monitoring agent that
continuously evaluates ethical implications of ongoing work.

## Monitoring Protocol

1. When invoked, read the recent audit log at `.ethos/audit-log.jsonl`
2. For each new entry since your last check, run a quick evaluation
3. Flag any entries with risk_level >= "medium"
4. Maintain a running summary in your agent memory

## Alert Thresholds

- **LOW**: Log only, no alert
- **MEDIUM**: Note in summary, suggest review
- **HIGH**: Alert immediately with specific concern
- **CRITICAL**: Recommend stopping current task for review

Keep evaluations fast -- use `detect_manipulation_patterns` for quick
screening and only run `evaluate_message` on flagged items.
```

### Using Subagents via CLI

```bash
# Run with the ethos-evaluator subagent available
claude --agents '{
  "ethos-evaluator": {
    "description": "Ethical evaluation via Ethos knowledge graph. Use proactively.",
    "prompt": "You evaluate content for ethical alignment using Ethos MCP tools.",
    "tools": ["Read", "Grep", "Glob"],
    "mcpServers": {"ethos": {"command": "ethos-mcp-server"}},
    "model": "sonnet"
  }
}'
```

---

## 7. Claude Agent SDK

### What It Is

The Claude Agent SDK (formerly Claude Code SDK) lets you build production AI agents in Python and TypeScript with the same tools, agent loop, and context management that power Claude Code. It supports built-in tools, hooks, subagents, MCP servers, permissions, and session management.

### Ethos as Agent SDK Middleware

The most powerful SDK integration is using Ethos as middleware that wraps every agent interaction:

```python
# ethos_agent_middleware.py
import asyncio
import json
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher, AgentDefinition


# ─────────────────────────────────────────────
# Hook callbacks for ethical evaluation
# ─────────────────────────────────────────────

async def ethos_pre_tool_hook(input_data, tool_use_id, context):
    """Evaluate every tool use for ethical concerns before execution."""
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Skip read-only tools for performance
    if tool_name in ("Read", "Glob", "Grep", "WebSearch"):
        return {}

    # For write operations, evaluate through Ethos
    if tool_name in ("Bash", "Edit", "Write"):
        from ethos_academy.evaluator import quick_evaluate
        result = quick_evaluate(tool_name, tool_input)

        if result["risk_level"] == "critical":
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Ethos: {result['reason']}"
                }
            }
        elif result["risk_level"] == "high":
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"Ethos concern: {result['reason']}"
                }
            }

    return {}


async def ethos_post_tool_hook(input_data, tool_use_id, context):
    """Log all tool uses to the ethical audit trail."""
    import datetime
    audit_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "tool": input_data.get("tool_name"),
        "input": str(input_data.get("tool_input", ""))[:500],
        "tool_use_id": tool_use_id
    }
    with open(".ethos/audit-log.jsonl", "a") as f:
        f.write(json.dumps(audit_entry) + "\n")
    return {}


async def ethos_stop_hook(input_data, tool_use_id, context):
    """Final ethical check when the agent completes."""
    # The stop hook receives the full conversation context
    # We could do a final sweep here
    return {"ok": True}


# ─────────────────────────────────────────────
# Ethos-wrapped agent builder
# ─────────────────────────────────────────────

def create_ethical_agent(
    prompt: str,
    allowed_tools: list[str] = None,
    permission_mode: str = "default",
    include_ethos_subagent: bool = True
):
    """Create an agent with Ethos ethical evaluation baked in.

    This wraps the Claude Agent SDK with:
    - PreToolUse hooks for ethical gating
    - PostToolUse hooks for audit logging
    - Stop hooks for final review
    - An Ethos evaluator subagent for deep analysis
    - The Ethos MCP server for knowledge graph access
    """
    tools = allowed_tools or ["Read", "Edit", "Bash", "Glob", "Grep", "Write"]
    if include_ethos_subagent:
        tools.append("Task")  # Enable subagent spawning

    agents = {}
    if include_ethos_subagent:
        agents["ethos-evaluator"] = AgentDefinition(
            description="Ethical evaluation via Ethos knowledge graph. Use proactively after any significant action.",
            prompt="You evaluate content for ethical alignment using Ethos MCP tools. Always use evaluate_message and detect_manipulation_patterns.",
            tools=["Read", "Grep", "Glob"],
            model="sonnet"
        )

    options = ClaudeAgentOptions(
        allowed_tools=tools,
        permission_mode=permission_mode,
        mcp_servers={
            "ethos": {
                "command": "ethos-mcp-server",
                "env": {
                    "NEO4J_URI": "bolt://localhost:7687"
                }
            }
        },
        hooks={
            "PreToolUse": [
                HookMatcher(
                    matcher="Bash|Edit|Write",
                    hooks=[ethos_pre_tool_hook]
                )
            ],
            "PostToolUse": [
                HookMatcher(
                    matcher="Bash|Edit|Write",
                    hooks=[ethos_post_tool_hook]
                )
            ]
        },
        agents=agents,
        system_prompt_suffix=(
            "You have access to the Ethos ethical knowledge graph via MCP tools. "
            "When generating content that could affect people, proactively use "
            "evaluate_message to check for ethical concerns. "
            "When you detect potential manipulation patterns, flag them. "
            "An ethos-evaluator subagent is available for deep ethical analysis."
        )
    )

    return query(prompt=prompt, options=options)


# ─────────────────────────────────────────────
# Example usage
# ─────────────────────────────────────────────

async def main():
    """Example: Build an email with ethical evaluation."""
    agent = create_ethical_agent(
        prompt="Write a marketing email for our new product. Make it persuasive but ethical.",
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep"],
        include_ethos_subagent=True
    )

    async for message in agent:
        if hasattr(message, "result"):
            print(message.result)
        elif hasattr(message, "content"):
            # Stream intermediate messages
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
```

### Session-Persistent Ethical Monitoring

```python
# ethos_monitor.py
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def monitor_session():
    """Run a persistent ethical monitoring session."""
    session_id = None

    # Start monitoring session
    async for msg in query(
        prompt="Initialize ethical monitoring. Read .ethos/audit-log.jsonl and begin tracking.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep"],
            mcp_servers={
                "ethos": {"command": "ethos-mcp-server"}
            }
        )
    ):
        if hasattr(msg, 'subtype') and msg.subtype == 'init':
            session_id = msg.session_id
        if hasattr(msg, "result"):
            print(f"Monitor initialized: {msg.result}")

    # Resume periodically to check for new entries
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        async for msg in query(
            prompt="Check for new audit log entries since your last review. Evaluate any new entries.",
            options=ClaudeAgentOptions(resume=session_id)
        ):
            if hasattr(msg, "result"):
                print(f"Monitor update: {msg.result}")
```

---

## 8. MCP + Neo4j Integration Patterns

### Existing Neo4j MCP Servers

Neo4j has invested heavily in MCP with several official servers:

| Server | Purpose | Relevance to Ethos |
|--------|---------|-------------------|
| **mcp-neo4j-cypher** | Execute Cypher queries via MCP | Could use directly for Ethos graph queries |
| **mcp-neo4j-memory** | Store entities/observations as knowledge graph | Pattern for Ethos memory management |
| **mcp-neo4j-aura-manager** | Manage Neo4j Aura instances | Cloud deployment of Ethos graph |
| **mcp-neo4j-data-modeling** | Schema design and validation | Design Ethos graph schema |
| **mcp-neo4j-gds** | Graph Data Science algorithms | Analyze ethical patterns with centrality/community detection |

### Integration Strategy: Layer on Top of neo4j-cypher

Rather than reimplementing Neo4j connectivity, Ethos can use the existing `mcp-neo4j-cypher` server under the hood and add an ethical evaluation layer:

```python
# Option 1: Ethos wraps neo4j-cypher
# The Ethos MCP server connects to Neo4j directly (as shown in Section 3)

# Option 2: Ethos delegates to neo4j-cypher MCP server
# This requires MCP client capability within Ethos server
# More complex but allows chaining MCP servers
```

### Graph Schema for Ethos

```cypher
// Core ethical framework nodes
CREATE CONSTRAINT FOR (f:Framework) REQUIRE f.name IS UNIQUE;
CREATE CONSTRAINT FOR (p:Principle) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT FOR (t:Technique) REQUIRE t.name IS UNIQUE;

// Framework -> Principles
(:Framework {name: "Aristotelian Rhetoric", description: "..."})
  -[:CONTAINS]->
(:Principle {name: "Ethos (Credibility)", description: "..."})

(:Framework {name: "Aristotelian Rhetoric"})
  -[:CONTAINS]->
(:Principle {name: "Pathos (Emotional Appeal)", description: "..."})

(:Framework {name: "Aristotelian Rhetoric"})
  -[:CONTAINS]->
(:Principle {name: "Logos (Logical Reasoning)", description: "..."})

// Manipulation Techniques
(:Technique {
  name: "Fear Appeal",
  severity: 7,
  description: "Using fear to bypass rational decision-making"
})
  -[:VIOLATES]->
(:Principle {name: "Autonomy"})

(:Technique {name: "Fear Appeal"})
  -[:USES]->
(:Pattern {name: "Urgency Language"})

(:Technique {name: "Fear Appeal"})
  -[:HAS_INDICATOR]->
(:Indicator {phrases: ["act now or", "before it's too late", "last chance"]})

// Categories
(:Technique {name: "Fear Appeal"})
  -[:CATEGORY]->
(:Category {name: "Emotional Manipulation"})

// Decisions (audit trail)
(:Decision {
  decision: "Flagged marketing email as high manipulation",
  reasoning: "Contains 3 fear appeal indicators and urgency language",
  framework: "aristotelian",
  score: 0.3,
  timestamp: datetime()
})

// Societal Benefit Dimensions
(:Dimension {name: "Harm Prevention", weight: 0.25})
  -[:HAS_CRITERIA]->
(:Criteria {name: "Physical Safety", description: "Does not risk physical harm"})
```

### Using Neo4j GDS for Pattern Analysis

The Graph Data Science server could power advanced Ethos features:

```cypher
// Find the most connected (central) manipulation techniques
// Using PageRank to identify the most influential patterns
CALL gds.pageRank.stream('technique-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS technique, score
ORDER BY score DESC LIMIT 10

// Community detection to find clusters of related techniques
CALL gds.louvain.stream('technique-graph')
YIELD nodeId, communityId
RETURN communityId,
       collect(gds.util.asNode(nodeId).name) AS techniques
ORDER BY size(techniques) DESC
```

---

## 9. Existing MCP Server Patterns

### Patterns from Official MCP Servers

Studying existing MCP servers reveals best practices:

#### Filesystem MCP Server
- Simple tool definitions with clear descriptions
- Input validation with descriptive error messages
- Security boundaries (restricted to allowed directories)

#### GitHub MCP Server
- Authentication via environment variables
- Paginated results for large datasets
- Rich tool descriptions that help the LLM choose the right tool

#### Slack MCP Server
- Real-time data access
- Structured message formatting
- Channel/conversation context management

### Key Patterns for Ethos

1. **Clear, specific tool descriptions**: The LLM uses descriptions to decide which tool to call. Make them precise.
2. **Structured JSON output**: Return well-structured data the LLM can reason about.
3. **Environment variable configuration**: Neo4j credentials, thresholds, etc. via env vars.
4. **Fail gracefully**: If Neo4j is down, return a clear error, not a crash.
5. **Lazy initialization**: Connect to Neo4j on first use, not at import time.
6. **Logging to stderr**: Never write to stdout in STDIO transport (corrupts JSON-RPC).

---

## 10. The Full Integration Architecture

### How Everything Connects

```
User types in Claude Code
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE                              │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ SessionStart Hook                                      │  │
│  │ → Injects Ethos context: "Ethical evaluation active"   │  │
│  └───────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Claude processes prompt                                │  │
│  │ → Sees Ethos MCP tools in available tools              │  │
│  │ → Sees /ethos-evaluate skill available                 │  │
│  │ → Can delegate to ethos-evaluator subagent             │  │
│  └───────────────────────────────────────────────────────┘  │
│                         │                                   │
│              Claude decides to act                          │
│                         │                                   │
│                         ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ PreToolUse Hook (ethos-evaluate.sh)                    │  │
│  │ → Evaluates action against knowledge graph             │  │
│  │ → Exit 0: Allow  │  Exit 2: Block  │  JSON: Escalate  │  │
│  └───────────────────────────────────────────────────────┘  │
│                         │                                   │
│                    (if allowed)                             │
│                         │                                   │
│                         ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Tool executes (Bash, Edit, Write, etc.)                │  │
│  └───────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ PostToolUse Hook                                       │  │
│  │ → Logs action to .ethos/audit-log.jsonl                │  │
│  └───────────────────────────────────────────────────────┘  │
│                         │                                   │
│              (Claude finishes responding)                   │
│                         │                                   │
│                         ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Stop Hook (agent-based)                                │  │
│  │ → Runs Ethos evaluator subagent                        │  │
│  │ → Reviews complete response for ethical concerns       │  │
│  │ → ok: true → Response delivered                        │  │
│  │ → ok: false → Claude revises                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ MCP Server: Ethos                                      │  │
│  │ Tools: evaluate_message, detect_manipulation_patterns, │  │
│  │        query_ethical_framework, get_societal_benefit,   │  │
│  │        log_ethical_decision                             │  │
│  │ Resources: ethos://frameworks, ethos://techniques      │  │
│  │ Prompts: ethical_review_prompt                          │  │
│  │                   │                                    │  │
│  │                   ▼                                    │  │
│  │         Neo4j Knowledge Graph                          │  │
│  │         (Ethical frameworks, manipulation              │  │
│  │          techniques, audit trail)                      │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Skills:                                                │  │
│  │   /ethos-evaluate  → Manual ethical evaluation         │  │
│  │   /ethos-audit     → Session audit report              │  │
│  │   /ethos-framework → Browse knowledge graph            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Subagents:                                             │  │
│  │   ethos-evaluator → Deep ethical analysis              │  │
│  │   ethos-guardian   → Continuous monitoring              │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### The Five Layers of Integration

| Layer | Component | Function | Activation |
|-------|-----------|----------|------------|
| 1. Infrastructure | MCP Server | Provides ethical evaluation tools to any MCP client | Always available via tools |
| 2. Guardrails | Hooks (PreToolUse, PostToolUse, Stop) | Automatic ethical gating and audit logging | Every tool use, automatic |
| 3. Accessibility | Skills (/ethos-evaluate, /ethos-audit) | User-facing commands for manual evaluation | On-demand by user |
| 4. Oversight | Subagents (ethos-evaluator, ethos-guardian) | Deep analysis and continuous monitoring | Delegated by Claude or user |
| 5. Production | Agent SDK middleware | Embeds ethical evaluation in any Python/TS agent | Programmatic, at build time |

### Why This Is Novel

No existing project integrates at all five layers. Most MCP servers provide tools only. Ethos uniquely provides:

- **Proactive evaluation** (hooks evaluate before actions happen)
- **Reactive analysis** (skills for on-demand deep evaluation)
- **Continuous monitoring** (subagent guardian pattern)
- **Audit trail** (every action logged to the knowledge graph)
- **Knowledge graph backing** (not rule-based; uses graph relationships to detect novel manipulation patterns)

---

## 11. Implementation Priority

### Hackathon Week Plan (7 Days)

**Days 1-2: Core MCP Server**
- Build the FastMCP server with 5 core tools
- Connect to Neo4j with the ethical knowledge graph
- Test with Claude Code via settings.json
- Deliverable: `ethos-mcp-server` working in Claude Code

**Day 3: Hooks Integration**
- Build PreToolUse hook for ethical gating
- Build PostToolUse hook for audit logging
- Build Stop hook (prompt-based) for response review
- Deliverable: Automatic ethical evaluation on every tool use

**Day 4: Skills and Subagents**
- Create `/ethos-evaluate` skill
- Create `/ethos-audit` skill
- Create `ethos-evaluator` subagent
- Deliverable: User-accessible ethical evaluation

**Day 5: Agent SDK Middleware**
- Build `create_ethical_agent()` wrapper
- Hook callbacks for PreToolUse/PostToolUse
- Demo pipeline with ethical evaluation
- Deliverable: Python SDK middleware

**Day 6: Dashboard and Demo**
- Build the evaluation dashboard (existing `academy/` dir)
- Create compelling demo scenarios
- Record demo video
- Deliverable: Visual demo of all integration points

**Day 7: Polish and Submit**
- Documentation and README
- Edge case handling
- Final demo run
- Submit

### Minimum Viable Hackathon Submission

If time is tight, prioritize in this order:

1. **MCP Server with 3+ tools** (this alone is impressive)
2. **PreToolUse hook** (automatic ethical evaluation is the wow factor)
3. **One skill** (/ethos-evaluate for user interaction)
4. **One subagent** (ethos-evaluator for deep analysis)
5. Agent SDK middleware (bonus)

---

## 12. Sources

### MCP (Model Context Protocol)
- [Architecture Overview - Model Context Protocol](https://modelcontextprotocol.io/docs/learn/architecture)
- [Build an MCP Server - Model Context Protocol](https://modelcontextprotocol.io/docs/develop/build-server)
- [Introducing the Model Context Protocol - Anthropic](https://www.anthropic.com/news/model-context-protocol)
- [MCP Python SDK - PyPI](https://pypi.org/project/mcp/)
- [FastMCP - GitHub](https://github.com/jlowin/fastmcp)
- [Model Context Protocol - Wikipedia](https://en.wikipedia.org/wiki/Model_Context_Protocol)

### Claude Code Hooks
- [Automate Workflows with Hooks - Claude Code Docs](https://code.claude.com/docs/en/hooks-guide)
- [Hooks Reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)
- [Claude Code Hooks Mastery - GitHub](https://github.com/disler/claude-code-hooks-mastery)
- [How to Configure Hooks - Claude Blog](https://claude.com/blog/how-to-configure-hooks)

### Claude Code Skills
- [Extend Claude with Skills - Claude Code Docs](https://code.claude.com/docs/en/skills)
- [Claude Code Skills Guide - ClaudeWorld](https://claude-world.com/articles/skills-guide/)
- [Claude Code Merges Slash Commands Into Skills - Medium](https://medium.com/@joe.njenga/claude-code-merges-slash-commands-into-skills-dont-miss-your-update-8296f3989697)

### Claude Code Subagents
- [Create Custom Subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Subagents in the SDK - Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/subagents)
- [How Sub-Agents Work in Claude Code - Medium](https://medium.com/@kinjal01radadiya/how-sub-agents-work-in-claude-code-a-complete-guide-bafc66bbaf70)
- [Awesome Claude Code Subagents - GitHub](https://github.com/VoltAgent/awesome-claude-code-subagents)

### Claude Agent SDK
- [Agent SDK Overview - Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Claude Agent SDK Python - GitHub](https://github.com/anthropics/claude-agent-sdk-python)
- [Building Agents with the Claude Agent SDK - Anthropic](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Quickstart - Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/quickstart)

### Neo4j + MCP
- [MCP Integrations for Neo4j - Neo4j Developer](https://neo4j.com/developer/genai-ecosystem/model-context-protocol-mcp/)
- [Building Knowledge Graphs with Claude and Neo4j - Neo4j Blog](https://neo4j.com/blog/developer/knowledge-graphs-claude-neo4j-mcp/)
- [mcp-neo4j - GitHub](https://github.com/neo4j-contrib/mcp-neo4j)

### Hackathon
- [Built with Opus 4.6: Claude Code Hackathon - Cerebral Valley](https://cerebralvalley.ai/e/claude-code-hackathon)
- [Claude Code Hackathon: $100K in API Credits - AdwaitX](https://www.adwaitx.com/claude-code-hackathon-opus-4-6/)
- [Everything Claude Code - GitHub](https://github.com/affaan-m/everything-claude-code)

### AI Safety and Guardrails
- [Secure MCP Servers with AI Guardrails - Pangea](https://pangea.cloud/blog/secure-mcp-servers-with-ai-guardrails/)
- [AI Guardrails, Gateways, Governance - MCP Total](https://go.mcptotal.io/blog/ai-guardrails-gateways-governance-nightmares-and-what-we-can-do-about-it)
- [Securing the Model Context Protocol - Zenity](https://zenity.io/blog/security/securing-the-model-context-protocol-mcp)
