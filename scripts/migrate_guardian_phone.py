"""One-time migration: rename counselor_* -> guardian_*, encrypt phones.

Run once after deploying the guardian phone feature:
  uv run python -m scripts.migrate_guardian_phone

What it does:
  1. Renames counselor_name -> guardian_name on all Agent nodes
  2. Encrypts counselor_phone into guardian_phone_encrypted
  3. Sets guardian_phone_verified=true for existing numbers (grandfathered)
  4. Removes old plaintext counselor_phone and counselor_name properties
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def migrate():
    from ethos_academy.crypto import encrypt
    from ethos_academy.graph.service import graph_context

    async with graph_context() as service:
        if not service.connected:
            logger.error("Cannot connect to Neo4j. Check NEO4J_URI in .env.")
            sys.exit(1)

        # Step 1: Rename counselor_name -> guardian_name
        logger.info("Renaming counselor_name -> guardian_name...")
        records, _, _ = await service.execute_query(
            """
            MATCH (a:Agent) WHERE a.counselor_name IS NOT NULL
            SET a.guardian_name = a.counselor_name
            REMOVE a.counselor_name
            RETURN count(a) AS migrated
            """
        )
        count = records[0]["migrated"] if records else 0
        logger.info("Renamed guardian_name on %d agents", count)

        # Step 2: Encrypt counselor_phone -> guardian_phone_encrypted
        logger.info("Encrypting counselor_phone -> guardian_phone_encrypted...")
        records, _, _ = await service.execute_query(
            """
            MATCH (a:Agent) WHERE a.counselor_phone IS NOT NULL AND a.counselor_phone <> ''
            RETURN a.agent_id AS agent_id, a.counselor_phone AS phone
            """
        )
        phone_count = 0
        for record in records or []:
            agent_id = record["agent_id"]
            plaintext = record["phone"]
            encrypted = encrypt(plaintext)
            await service.execute_query(
                """
                MATCH (a:Agent {agent_id: $agent_id})
                SET a.guardian_phone_encrypted = $encrypted,
                    a.guardian_phone_verified = true,
                    a.guardian_notifications_opted_out = false
                REMOVE a.counselor_phone
                """,
                {"agent_id": agent_id, "encrypted": encrypted},
            )
            phone_count += 1
            logger.info("Encrypted phone for %s", agent_id)

        logger.info("Encrypted %d phone numbers", phone_count)

        # Step 3: Clean up any remaining counselor_phone with empty string
        await service.execute_query(
            """
            MATCH (a:Agent) WHERE a.counselor_phone IS NOT NULL
            REMOVE a.counselor_phone
            """
        )

        # Step 4: Clean up guardian_phone plaintext (from renamed but not encrypted)
        await service.execute_query(
            """
            MATCH (a:Agent) WHERE a.guardian_phone IS NOT NULL
            REMOVE a.guardian_phone
            """
        )

        logger.info("Migration complete.")

        # Verify
        has_key = bool(os.environ.get("ETHOS_ENCRYPTION_KEY"))
        if not has_key:
            logger.warning(
                "ETHOS_ENCRYPTION_KEY not set. Phone numbers stored unencrypted. "
                "Set the key and re-run to encrypt."
            )


if __name__ == "__main__":
    asyncio.run(migrate())
