import asyncio
from sqlalchemy import select
from researchmind.db.engine import create_engine
from researchmind.db.session import create_session_factory
from researchmind.models.evidence_chunk import EvidenceChunk

async def main():
    engine = create_engine('postgresql+asyncpg://researchmind:researchmind@localhost:5432/researchmind')
    session_factory = create_session_factory(engine)
    async with session_factory() as db:
        res = await db.execute(select(EvidenceChunk).limit(1))
        print("RESULT:", res.first())

if __name__ == "__main__":
    asyncio.run(main())

