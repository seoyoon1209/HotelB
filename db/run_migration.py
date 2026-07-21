"""일회성 마이그레이션 실행 스크립트.
사용법: .venv/bin/python db/run_migration.py db/migration_002_reservation_action.sql
"""
import asyncio
import sys
from pathlib import Path

import asyncpg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from settings.Settings import get_settings


async def main(sql_path: str):
    settings = get_settings()
    dsn = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_service_name}"
    sql = Path(sql_path).read_text(encoding="utf-8")

    conn = await asyncpg.connect(dsn=dsn, ssl="require")
    try:
        await conn.execute(sql)
        print(f"OK: {sql_path} 실행 완료")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
