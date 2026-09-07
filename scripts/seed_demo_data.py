"""Seed demo data for ResearchMind development.

Usage:
    python -m scripts.seed_demo_data
"""
import asyncio
from datetime import date

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from researchmind.config import get_settings
from researchmind.models import (
    Jurisdiction,
    Authority,
    RegulatoryDocument,
    DocumentType,
    JurisdictionLevel,
)


async def seed() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        # Jurisdictions
        india = Jurisdiction(name="India", code="IN", level=JurisdictionLevel.NATIONAL, country_code="IN")
        session.add(india)
        await session.flush()
        
        wb = Jurisdiction(name="West Bengal", code="IN-WB", level=JurisdictionLevel.STATE,
                         parent_id=india.id, country_code="IN", state_code="WB")
        session.add(wb)
        await session.flush()
        
        kgp = Jurisdiction(name="Kharagpur", code="IN-WB-KGP", level=JurisdictionLevel.MUNICIPAL,
                          parent_id=wb.id, country_code="IN", state_code="WB")
        session.add(kgp)
        await session.flush()
        
        # Authorities
        bis = Authority(name="Bureau of Indian Standards", abbreviation="BIS",
                       jurisdiction_id=india.id, authority_type="standards_body",
                       website="https://www.bis.gov.in")
        tcpo = Authority(name="Town and Country Planning Organisation", abbreviation="TCPO",
                        jurisdiction_id=india.id, authority_type="planning")
        kmc = Authority(name="Kharagpur Municipal Corporation", abbreviation="KMC",
                       jurisdiction_id=kgp.id, authority_type="municipal")
        session.add_all([bis, tcpo, kmc])
        await session.flush()
        
        # Documents (just the regulatory document, no versions yet)
        nbc = RegulatoryDocument(
            title="National Building Code of India",
            short_title="NBC",
            document_type=DocumentType.CODE,
            authority_id=bis.id,
            jurisdiction_id=india.id,
            subject_area="building_regulation",
        )
        session.add(nbc)
        
        await session.commit()
        print("✓ Demo data seeded successfully")
        print(f"  Jurisdictions: India → West Bengal → Kharagpur")
        print(f"  Authorities: BIS, TCPO, KMC")
        print(f"  Documents: NBC")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
