# Future TODOs

Ideas worth building after MVP ships.

## Ship alignment skill with `ethos init`

Bundle the `/alignment` Claude Code skill in the `ethos-ai` npm package. When users run `npx ethos init`, copy `.claude/skills/alignment/` and `.claude/commands/alignment.md` into their project so `/alignment` works in their Claude Code environment.

**Requires:**
- Implement `ethos init` CLI command (currently stubbed)
- Create an external-facing version of the skill — current one references Ethos internals (`ethos_academy/shared/models.py`, etc.) that consumers won't have. External version should focus on alignment principles, scoring concepts, and how to interpret Ethos results.
- Ship skill files inside the npm package (add to `files` in `package.json`)

**Why it matters:**
- "Install ethos, run init, Claude Code becomes your alignment advisor" — strong demo moment
- Hits Opus 4.6 Use criterion (creative integration beyond basic)
- Makes the research actionable for the community, not just us

## Langfuse for pipeline observability

Add Langfuse (open-source, MIT, built on OTel) to trace the `evaluate()` pipeline and monitor Claude API costs. Langfuse scores Ethos's performance; Ethos scores agent messages — complementary, not competing.

**What it gives us:**
- Per-evaluation traces: scanner → prompt builder → Claude API → scoring → Neo4j write
- Automatic Claude token/cost tracking (prompts are large — need visibility)
- Prompt version management and A/B testing for `prompts.py`
- Golden datasets for regression testing when prompts change
- Score consistency monitoring (LLM non-determinism)

**Integration path (~1-2 hours):**
1. `pip install langfuse opentelemetry-instrumentation-anthropic`
2. Add `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` to `.env`
3. Add `@observe()` decorators to `evaluate()`, `scan_keywords()`, `build_evaluation_prompt()`, and the Claude call
4. Push Ethos's 12 trait scores as Langfuse custom scores for dashboard visualization

**Why not now:** `evaluate()` is still a placeholder. Build the pipeline first, instrument it later. Judges want Phronesis and Academy, not an ops dashboard.
