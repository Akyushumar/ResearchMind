import asyncio
from sqlalchemy import Column, String, Integer, Text, Computed
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.types import UserDefinedType

Base = declarative_base()

class TSVECTOR(UserDefinedType):
    cache_ok = True
    def get_col_spec(self, **kw):
        return "TSVECTOR"

class search_vector_expr(FunctionElement):
    type = TSVECTOR()
    name = 'search_vector_expr'

@compiles(search_vector_expr, 'postgresql')
def compile_search_vector_expr_postgresql(element, compiler, **kw):
    return "setweight(to_tsvector('english', coalesce(content, '')), 'A')"

@compiles(search_vector_expr, 'sqlite')
def compile_search_vector_expr_sqlite(element, compiler, **kw):
    return "''"

class TestTable(Base):
    __tablename__ = "test_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    sv = mapped_column(TSVECTOR, Computed(search_vector_expr()))

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
if __name__ == "__main__":
    asyncio.run(main())

