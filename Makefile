.PHONY: help install init worker dev test lint clean

help:
	@echo "可用命令:"
	@echo "  make install  安装依赖"
	@echo "  make init     初始化数据库"
	@echo "  make worker   启动 Celery Worker"
	@echo "  make dev      启动开发服务器"
	@echo "  make test     运行测试"
	@echo "  make clean    清理临时文件"

install:
	pip install -r requirements.txt

init:
	python init_db.py

worker:
	celery -A app.services.celery_tasks worker --loglevel=info --concurrency=4

dev:
	python main.py

test:
	pytest -v --asyncio-mode=auto

lint:
	ruff check app/ main.py init_db.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
