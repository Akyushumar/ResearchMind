import asyncio
from qdrant_client import AsyncQdrantClient
from researchmind.config.settings import get_settings

async def main():
    settings = get_settings()
    client = AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    info = await client.get_collection(settings.qdrant_collection)
    print(f"Collection: {settings.qdrant_collection}")
    print(f"Vectors Config: {info.config.params.vectors}")
    print(f"Points Count: {info.points_count}")

if __name__ == '__main__':
    asyncio.run(main())
