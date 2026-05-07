"""ORM模型 — 自动扫描导入，按依赖顺序建表"""
import os
import importlib
from typing import Callable
from app.config.database import Base, engine


def _import_modules(func: Callable[[str], bool]):
    current_dir = os.path.dirname(__file__)
    for filename in sorted(os.listdir(current_dir)):
        if filename.endswith(".py") and filename != "__init__.py":
            if func(filename):
                module_name = filename[:-3]
                importlib.import_module(f".{module_name}", package=__name__)


async def init_tables():
    _import_modules(lambda f: True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Import all models at package load time
_import_modules(lambda f: True)
