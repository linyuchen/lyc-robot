import os
import importlib
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from src.common import DATA_DIR
from src.db.models.base import Base

DB_PATH = DATA_DIR / "db.sqlite"
engine = create_engine(f'sqlite:///{DB_PATH}')


def __import_models():
    directory = Path(__file__).parent / 'models'
    # 获取目录下的所有文件和文件夹
    for filename in os.listdir(directory):
        # 构建完整的文件路径
        full_path = os.path.join(directory, filename)

        # 检查是否是文件并且是Python模块（以.py结尾）
        if os.path.isfile(full_path) and filename.endswith('.py'):
            # 去掉.py后缀，获取模块名
            module_name = filename[:-3]

            # 构建模块的完整导入路径
            module_path = f"src.db.models.{module_name}"

            try:
                # 动态导入模块
                module = importlib.import_module(module_path)
            except ImportError as e:
                print(f"导入模块 {module_path} 失败: {e}")

__import_models()

def init_db():
    inspector = inspect(engine)
    if not inspector.get_table_names():
        print(f'需要新建数据库{DB_PATH}')
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    return session
