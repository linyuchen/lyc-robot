from pathlib import Path

from src.db.alembic_tools.tool import upgrade, gen_migration, re_write_config
from src.db import DB_PATH

cur_path = Path(__file__).parent
ini_path = cur_path / 'alembic.ini'


def upgrade_common_db():
    temp_ini_path = re_write_config(ini_path, DB_PATH)
    upgrade(temp_ini_path)
    temp_ini_path.unlink()


def gen_common_db_migrations():
    temp_ini_path = re_write_config(ini_path, DB_PATH)
    gen_migration(temp_ini_path)
    temp_ini_path.unlink()


if __name__ == '__main__':
    gen_common_db_migrations()
