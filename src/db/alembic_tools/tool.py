import configparser
import subprocess
from pathlib import Path

from alembic.config import Config
from alembic import command


def re_write_config(ini_path: Path, db_path: Path) -> Path:
    """
    return new config path
    """
    config = configparser.ConfigParser()
    config.read(ini_path)
    config['alembic']['sqlalchemy.url'] = f'sqlite:///{db_path}'
    config['alembic']['script_location'] = str(Path(ini_path).parent / 'migrations')
    new_file_name = 'new.' + ini_path.name
    new_path = ini_path.parent / new_file_name
    with open(new_path, 'w') as f:
        config.write(f)
    return new_path


def upgrade(ini_path: Path):
    alembic_cfg = Config(ini_path)
    command.upgrade(alembic_cfg, 'head')



def gen_migration(ini_path: Path):
    alembic_cfg = Config(ini_path)
    command.revision(alembic_cfg, autogenerate=True)

