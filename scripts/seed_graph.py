"""Seed Phronesis (the Neo4j graph layer) with taxonomy and real evaluations.

Seeds the full semantic layer first (dimensions, traits, indicators,
constitutional values, hard constraints, legitimacy tests, patterns,
constraints, indexes), then evaluates moltbook posts through the full
evaluate() pipeline and stores results in the graph.

Default: reads data/moltbook/sample_posts.json (10 hand-picked posts).
Use --all to read curated_posts.json (~500 posts) instead.
Use --limit N to cap the number of posts evaluated.
Use --skip-existing to skip posts already evaluated (by message_hash).
"""

import argparse
import asyncio
import hashlib
import json
import logging
import os
import signal
import sys
from pathlib import Path


def _load_dotenv() -> None:
    """Load .env file from project root into os.environ (simple parser)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()

from ethos.tools import evaluate_outgoing  # noqa: E402
from ethos.graph.service import GraphService  # noqa: E402
from ethos.taxonomy.constitution import (  # noqa: E402
    ANTHROPIC_ASSESSMENTS,
    CONSTITUTIONAL_VALUES,
    HARD_CONSTRAINTS,
    INDICATOR_ASSESSMENT_MAPPINGS,
    LEGITIMACY_TESTS,
    SABOTAGE_PATHWAYS,
)
from ethos.taxonomy.indicators import INDICATORS  # noqa: E402
from ethos.taxonomy.traits import TRAIT_METADATA, TRAITS  # noqa: E402

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "moltbook"
SAMPLE_FILE = DATA_DIR / "sample_posts.json"
CURATED_FILE = DATA_DIR / "curated_posts.json"

# ─── Dimension definitions ────────────────────────────────────────────────
DIMENSIONS = [
    {
        "name": "ethos",
        "greek": "ηθος",
        "description": "Trust, credibility, and moral character",
    },
    {
        "name": "logos",
        "greek": "λόγος",
        "description": "Reasoning, accuracy, and logical integrity",
    },
    {
        "name": "pathos",
        "greek": "πάθος",
        "description": "Emotional intelligence, empathy, and compassion",
    },
]

# Dimension → ConstitutionalValue MAPS_TO relationships
DIMENSION_CV_MAPPINGS = [
    ("ethos", "ethics"),
    ("logos", "soundness"),
    ("pathos", "helpfulness"),
]

# Graceful shutdown flag
_interrupted = False


def _handle_sigint(signum: int, frame: object) -> None:
    """Handle Ctrl+C gracefully."""
    global _interrupted
    _interrupted = True
    print("\n\nInterrupted — saving progress and exiting cleanly...")


async def _create_constraints(service: GraphService) -> None:
    """Create uniqueness constraints per neo4j-schema.md."""
    constraints = [
        "CREATE CONSTRAINT agent_id_unique IF NOT EXISTS FOR (a:Agent) REQUIRE a.agent_id IS UNIQUE",
        "CREATE CONSTRAINT evaluation_id_unique IF NOT EXISTS FOR (e:Evaluation) REQUIRE e.evaluation_id IS UNIQUE",
        "CREATE CONSTRAINT trait_name_unique IF NOT EXISTS FOR (t:Trait) REQUIRE t.name IS UNIQUE",
        "CREATE CONSTRAINT indicator_id_unique IF NOT EXISTS FOR (i:Indicator) REQUIRE i.id IS UNIQUE",
        "CREATE CONSTRAINT dimension_name_unique IF NOT EXISTS FOR (d:Dimension) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT pattern_id_unique IF NOT EXISTS FOR (p:Pattern) REQUIRE p.pattern_id IS UNIQUE",
        "CREATE CONSTRAINT constitutional_value_name_unique IF NOT EXISTS FOR (cv:ConstitutionalValue) REQUIRE cv.name IS UNIQUE",
        "CREATE CONSTRAINT hard_constraint_id_unique IF NOT EXISTS FOR (hc:HardConstraint) REQUIRE hc.id IS UNIQUE",
        "CREATE CONSTRAINT legitimacy_test_name_unique IF NOT EXISTS FOR (lt:LegitimacyTest) REQUIRE lt.name IS UNIQUE",
        "CREATE CONSTRAINT anthropic_assessment_id_unique IF NOT EXISTS FOR (aa:AnthropicAssessment) REQUIRE aa.id IS UNIQUE",
    ]
    for c in constraints:
        await service.execute_query(c)
    print(f"  Created {len(constraints)} uniqueness constraints")


async def _create_indexes(service: GraphService) -> None:
    """Create performance indexes per neo4j-schema.md."""
    indexes = [
        "CREATE INDEX eval_created IF NOT EXISTS FOR (e:Evaluation) ON (e.created_at)",
        "CREATE INDEX eval_phronesis IF NOT EXISTS FOR (e:Evaluation) ON (e.phronesis)",
        "CREATE INDEX eval_message_hash IF NOT EXISTS FOR (e:Evaluation) ON (e.message_hash)",
        "CREATE INDEX agent_phronesis IF NOT EXISTS FOR (a:Agent) ON (a.phronesis_score)",
        "CREATE INDEX indicator_trait IF NOT EXISTS FOR (i:Indicator) ON (i.trait)",
        "CREATE INDEX assessment_category IF NOT EXISTS FOR (aa:AnthropicAssessment) ON (aa.category)",
    ]
    for idx in indexes:
        await service.execute_query(idx)
    print(f"  Created {len(indexes)} performance indexes")


async def _seed_dimensions(service: GraphService) -> None:
    """Seed 3 Dimension nodes."""
    for dim in DIMENSIONS:
        await service.execute_query(
            "MERGE (d:Dimension {name: $name}) "
            "ON CREATE SET d.greek = $greek, d.description = $description",
            {
                "name": dim["name"],
                "greek": dim["greek"],
                "description": dim["description"],
            },
        )
    print(f"  Seeded {len(DIMENSIONS)} Dimension nodes")


async def _seed_traits(service: GraphService) -> None:
    """Seed 12 Trait nodes with BELONGS_TO→Dimension relationships."""
    for name, trait in TRAITS.items():
        await service.execute_query(
            "MERGE (t:Trait {name: $name}) "
            "ON CREATE SET t.dimension = $dimension, t.polarity = $polarity, "
            "t.definition = $definition "
            "WITH t "
            "MATCH (d:Dimension {name: $dimension}) "
            "MERGE (t)-[:BELONGS_TO]->(d)",
            {
                "name": name,
                "dimension": trait["dimension"],
                "polarity": trait["polarity"],
                "definition": trait["description"],
            },
        )
    print(f"  Seeded {len(TRAITS)} Trait nodes with BELONGS_TO→Dimension")


async def _seed_indicators(service: GraphService) -> None:
    """Seed Indicator nodes with BELONGS_TO→Trait relationships."""
    for ind in INDICATORS:
        await service.execute_query(
            "MERGE (i:Indicator {id: $id}) "
            "ON CREATE SET i.name = $name, i.trait = $trait, "
            "i.description = $description, i.source = $source "
            "WITH i "
            "MATCH (t:Trait {name: $trait}) "
            "MERGE (i)-[:BELONGS_TO]->(t)",
            {
                "id": ind["id"],
                "name": ind["name"],
                "trait": ind["trait"],
                "description": ind["description"],
                "source": ind.get("source", ""),
            },
        )
    print(f"  Seeded {len(INDICATORS)} Indicator nodes with BELONGS_TO→Trait")


async def _seed_constitutional_values(service: GraphService) -> None:
    """Seed 4 ConstitutionalValue nodes."""
    for name, cv in CONSTITUTIONAL_VALUES.items():
        await service.execute_query(
            "MERGE (cv:ConstitutionalValue {name: $name}) "
            "ON CREATE SET cv.priority = $priority, cv.definition = $definition, "
            "cv.source = $source",
            {
                "name": name,
                "priority": cv["priority"],
                "definition": cv["definition"],
                "source": cv["source"],
            },
        )
    print(f"  Seeded {len(CONSTITUTIONAL_VALUES)} ConstitutionalValue nodes")


async def _seed_trait_cv_relationships(service: GraphService) -> None:
    """Seed Trait→ConstitutionalValue UPHOLDS relationships."""
    count = 0
    for trait_name, meta in TRAIT_METADATA.items():
        await service.execute_query(
            "MATCH (t:Trait {name: $trait_name}), "
            "(cv:ConstitutionalValue {name: $cv_name}) "
            "MERGE (t)-[:UPHOLDS {relationship: $relationship}]->(cv)",
            {
                "trait_name": trait_name,
                "cv_name": meta["constitutional_value"],
                "relationship": meta["relationship"],
            },
        )
        count += 1
    print(f"  Seeded {count} Trait→ConstitutionalValue UPHOLDS relationships")


async def _seed_dimension_cv_relationships(service: GraphService) -> None:
    """Seed Dimension→ConstitutionalValue MAPS_TO relationships."""
    for dim_name, cv_name in DIMENSION_CV_MAPPINGS:
        await service.execute_query(
            "MATCH (d:Dimension {name: $dim_name}), "
            "(cv:ConstitutionalValue {name: $cv_name}) "
            "MERGE (d)-[:MAPS_TO]->(cv)",
            {"dim_name": dim_name, "cv_name": cv_name},
        )
    print(
        f"  Seeded {len(DIMENSION_CV_MAPPINGS)} Dimension→ConstitutionalValue MAPS_TO"
    )


async def _seed_hard_constraints(service: GraphService) -> None:
    """Seed 7 HardConstraint nodes."""
    for hc in HARD_CONSTRAINTS:
        await service.execute_query(
            "MERGE (hc:HardConstraint {id: $id}) "
            "ON CREATE SET hc.name = $name, hc.definition = $definition, "
            "hc.severity = $severity, hc.source = 'anthropic_constitution'",
            {
                "id": hc["id"],
                "name": hc["name"],
                "definition": hc["definition"],
                "severity": hc["severity"],
            },
        )
    print(f"  Seeded {len(HARD_CONSTRAINTS)} HardConstraint nodes")


async def _seed_legitimacy_tests(service: GraphService) -> None:
    """Seed 3 LegitimacyTest nodes."""
    for lt in LEGITIMACY_TESTS:
        await service.execute_query(
            "MERGE (lt:LegitimacyTest {name: $name}) "
            "ON CREATE SET lt.definition = $definition, "
            "lt.source = 'anthropic_constitution'",
            {"name": lt["name"], "definition": lt["definition"]},
        )
    print(f"  Seeded {len(LEGITIMACY_TESTS)} LegitimacyTest nodes")


def _map_frequency_to_severity(frequency: str) -> str:
    """Map sabotage pathway frequency to severity: high→warning, else→info."""
    if frequency == "high":
        return "warning"
    return "info"


async def _seed_patterns(service: GraphService) -> None:
    """Seed 8 Pattern nodes from SABOTAGE_PATHWAYS with COMPOSED_OF→Indicator."""
    for sp in SABOTAGE_PATHWAYS:
        severity = _map_frequency_to_severity(sp["frequency"])
        stage_count = len(sp["relevant_indicators"])

        await service.execute_query(
            "MERGE (p:Pattern {pattern_id: $pattern_id}) "
            "ON CREATE SET p.name = $name, p.description = $description, "
            "p.severity = $severity, p.stage_count = $stage_count",
            {
                "pattern_id": sp["id"],
                "name": sp["name"],
                "description": sp["description"],
                "severity": severity,
                "stage_count": stage_count,
            },
        )

        # Link pattern to its indicators
        for ind_id in sp["relevant_indicators"]:
            await service.execute_query(
                "MATCH (p:Pattern {pattern_id: $pattern_id}), "
                "(i:Indicator {id: $ind_id}) "
                "MERGE (p)-[:COMPOSED_OF]->(i)",
                {"pattern_id": sp["id"], "ind_id": ind_id},
            )

    print(f"  Seeded {len(SABOTAGE_PATHWAYS)} Pattern nodes with COMPOSED_OF→Indicator")


async def _seed_anthropic_assessments(service: GraphService) -> None:
    """Seed 16 AnthropicAssessment nodes with ASSESSED_BY relationships from Indicators."""
    for aa in ANTHROPIC_ASSESSMENTS:
        await service.execute_query(
            "MERGE (aa:AnthropicAssessment {id: $id}) "
            "ON CREATE SET aa.name = $name, aa.category = $category, "
            "aa.section = $section, aa.description = $description, "
            "aa.source = $source",
            {
                "id": aa["id"],
                "name": aa["name"],
                "category": aa["category"],
                "section": aa["section"],
                "description": aa["description"],
                "source": aa["source"],
            },
        )

    # Create ASSESSED_BY relationships from Indicators to Assessments
    for mapping in INDICATOR_ASSESSMENT_MAPPINGS:
        await service.execute_query(
            "MATCH (i:Indicator {id: $indicator_id}), "
            "(aa:AnthropicAssessment {id: $assessment_id}) "
            "MERGE (i)-[:ASSESSED_BY {mapping_type: $mapping_type, notes: $notes}]->(aa)",
            {
                "indicator_id": mapping["indicator_id"],
                "assessment_id": mapping["assessment_id"],
                "mapping_type": mapping["mapping_type"],
                "notes": mapping["notes"],
            },
        )

    print(
        f"  Seeded {len(ANTHROPIC_ASSESSMENTS)} AnthropicAssessment nodes "
        f"with {len(INDICATOR_ASSESSMENT_MAPPINGS)} ASSESSED_BY relationships"
    )


async def seed_semantic_layer(service: GraphService) -> None:
    """Seed the full semantic layer — taxonomy, constitution, patterns."""
    print("\nSeeding semantic layer...")
    await _create_constraints(service)
    await _create_indexes(service)
    await _seed_dimensions(service)
    await _seed_traits(service)
    await _seed_indicators(service)
    await _seed_constitutional_values(service)
    await _seed_trait_cv_relationships(service)
    await _seed_dimension_cv_relationships(service)
    await _seed_hard_constraints(service)
    await _seed_legitimacy_tests(service)
    await _seed_patterns(service)
    await _seed_anthropic_assessments(service)
    print("Semantic layer complete.\n")


async def _get_existing_hashes(service: GraphService) -> set[str]:
    """Get all existing message_hash values from Evaluation nodes."""
    records, _, _ = await service.execute_query(
        "MATCH (e:Evaluation) WHERE e.message_hash IS NOT NULL "
        "RETURN e.message_hash AS h"
    )
    return {r["h"] for r in records}


async def evaluate_posts(
    posts: list[dict],
    skip_existing: bool = False,
    service: GraphService | None = None,
) -> int:
    """Evaluate posts through the full pipeline, storing results in the graph.

    Returns the number of API calls made.
    """
    global _interrupted

    existing_hashes: set[str] = set()
    if skip_existing and service and service.connected:
        existing_hashes = await _get_existing_hashes(service)
        print(f"Found {len(existing_hashes)} existing evaluations in graph")

    total = len(posts)
    api_calls = 0
    skipped = 0
    failed = 0

    for i, post in enumerate(posts):
        if _interrupted:
            print(f"\nStopped at {i}/{total}. {api_calls} API calls made.")
            break

        post_id = post.get("id", f"post-{i}")
        content = post.get("content", "")
        author = post.get("author") or {}
        author_id = author.get("id", post_id)
        author_name = author.get("name", "")

        # Check skip-existing
        if skip_existing and existing_hashes:
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            if content_hash in existing_hashes:
                skipped += 1
                print(
                    f"  {i + 1}/{total} skipped (already evaluated): {post_id[:20]}..."
                )
                continue

        print(f"  {i + 1}/{total} evaluating: {post_id[:20]}...", end=" ", flush=True)

        try:
            await evaluate_outgoing(
                content, source=author_name or author_id, source_name=author_name
            )
            api_calls += 1
            print("done")
        except Exception as exc:
            failed += 1
            print(f"FAILED: {exc}")
            logger.warning("Evaluation failed for post %s: %s", post_id, exc)

        # Rate limit — 1 API call per second
        if i < total - 1 and not _interrupted:
            await asyncio.sleep(1)

    print(
        f"\nEvaluation complete: {api_calls} API calls, {skipped} skipped, {failed} failed"
    )
    return api_calls


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed Neo4j with taxonomy and real evaluations"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Use curated_posts.json (~500 posts) instead of sample_posts.json (10 posts)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of posts to evaluate (0 = no limit)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip posts already evaluated (by message_hash)",
    )
    parser.add_argument(
        "--no-seed",
        action="store_true",
        help="Skip seeding the semantic layer",
    )
    args = parser.parse_args()

    # Set up Ctrl+C handler
    signal.signal(signal.SIGINT, _handle_sigint)

    logging.basicConfig(level=logging.WARNING)

    # ── Connect to Neo4j ──────────────────────────────────────────────
    service = GraphService()
    await service.connect()

    if not service.connected:
        print("ERROR: Cannot connect to Neo4j. Aborting.", file=sys.stderr)
        sys.exit(1)

    print("Connected to Neo4j")

    try:
        # ── Step 1: Seed semantic layer ───────────────────────────────
        if not args.no_seed:
            await seed_semantic_layer(service)

        if _interrupted:
            return

        # ── Step 2: Load posts ────────────────────────────────────────
        input_file = CURATED_FILE if args.all else SAMPLE_FILE
        if not input_file.exists():
            print(f"ERROR: {input_file} not found", file=sys.stderr)
            sys.exit(1)

        print(f"Loading posts from {input_file.name}...")
        with open(input_file) as f:
            posts = json.load(f)
        print(f"  Loaded {len(posts)} posts")

        if args.limit > 0:
            posts = posts[: args.limit]
            print(f"  Limited to {len(posts)} posts")

        # ── Step 3: Evaluate posts ────────────────────────────────────
        print(f"\nEvaluating {len(posts)} posts...")
        api_calls = await evaluate_posts(
            posts,
            skip_existing=args.skip_existing,
            service=service,
        )

        print(f"\nTotal API calls: {api_calls}")

    finally:
        await service.close()
        print("Neo4j connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
