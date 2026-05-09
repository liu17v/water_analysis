"""
Milvus 向量数据库操作 —— 四层防御策略，防止线程池耗尽和启动阻塞。

## 策略
1. **启动不加载数据**：init_collection() 只创建/获取 Collection 对象（毫秒级），不调用 col.load()。
   col.load() 是同步 gRPC 调用，会阻塞调用线程加载全部向量到内存——放在启动路径会卡死整个服务。
2. **懒加载**：search() 首次调用时执行 col.load()。正常运行时只加载一次，后续 search 复用。
3. **熔断器**：TCP 探活（3s 超时）→ connect → 失败后缓存 5 分钟快速失败。
   pymilvus 的 connections.connect() 无超时参数，C 层 socket 可能无限阻塞，必须预先 TCP 探测。
4. **独立线程池**：report.py 中 _MILVUS_EXECUTOR（max_workers=2）+ future.result(timeout=N) 形成外层超时隔离。
   Milvus 阻塞线程与 FastAPI 默认线程池隔离，防止耗尽影响其他请求。

所有 I/O 操作默认带超时，每层都有失败降级路径。
"""
import socket
import time
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from app.config.settings import get_settings
from app.config.logging import get_logger

logger = get_logger("services.milvus")
settings = get_settings()

COLLECTION_NAME = "task_features"
DIM = 13

_collection = None

# 熔断器：首次连接失败后 5 分钟内快速失败，避免阻塞线程池
_available = True
_last_check: float = 0
_CHECK_TTL = 300
_PROBE_TIMEOUT = 3.0


def _probe() -> bool:
    """TCP 探活，3 秒超时。pymilvus 的 connect() 无超时参数，必须提前探测。"""
    try:
        sock = socket.create_connection(
            (settings.MILVUS_HOST, settings.MILVUS_PORT), timeout=_PROBE_TIMEOUT
        )
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def connect():
    global _available, _last_check

    if not _available and time.time() - _last_check < _CHECK_TTL:
        raise ConnectionError(
            f"Milvus 不可用（缓存至 {_last_check + _CHECK_TTL:.0f}）"
        )

    if not _probe():
        _available = False
        _last_check = time.time()
        raise ConnectionError(
            f"Milvus TCP 探活失败 {settings.MILVUS_HOST}:{settings.MILVUS_PORT}"
        )

    try:
        connections.connect(host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)
        _available = True
    except Exception as e:
        _available = False
        _last_check = time.time()
        raise ConnectionError(f"Milvus 连接失败: {e}") from e


def init_collection():
    global _collection
    if utility.has_collection(COLLECTION_NAME):
        _collection = Collection(COLLECTION_NAME)
        logger.info("Milvus 集合已存在，直接加载")
        return
    fields = [
        FieldSchema(name="task_id", dtype=DataType.VARCHAR, max_length=36, is_primary=True),
        FieldSchema(name="feature_vector", dtype=DataType.FLOAT_VECTOR, dim=DIM),
        FieldSchema(name="created_at", dtype=DataType.INT64),
        FieldSchema(name="reservoir_name", dtype=DataType.VARCHAR, max_length=64),
    ]
    schema = CollectionSchema(fields, "Task feature vectors")
    _collection = Collection(COLLECTION_NAME, schema)
    _collection.create_index(
        "feature_vector",
        {"metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 128}},
    )
    logger.info("Milvus 集合创建完成")


def get_collection() -> Collection:
    if _collection is None:
        init_collection()
    return _collection


def insert(task_id: str, vector: list[float], created_at: int, reservoir_name: str):
    col = get_collection()
    col.insert([[task_id], [vector], [created_at], [reservoir_name]])
    logger.info(f"Milvus 向量入库 | task_id={task_id}")


def search(vector: list[float], top_k: int = 5) -> list[dict]:
    global _available, _last_check
    if not _available and time.time() - _last_check < _CHECK_TTL:
        raise ConnectionError(f"Milvus 搜索不可用（缓存至 {_last_check + _CHECK_TTL:.0f}）")

    col = get_collection()
    try:
        col.load()
        results = col.search(
            data=[vector],
            anns_field="feature_vector",
            param={"metric_type": "L2", "params": {"nprobe": 16}},
            limit=top_k,
            output_fields=["task_id", "created_at", "reservoir_name"],
        )
        _available = True
        return [
            {
                "task_id": h.entity.get("task_id"),
                "distance": h.distance,
                "created_at": h.entity.get("created_at"),
                "reservoir_name": h.entity.get("reservoir_name"),
            }
            for h in results[0]
        ]
    except Exception as e:
        _available = False
        _last_check = time.time()
        raise ConnectionError(f"Milvus 搜索失败: {e}") from e


def delete(task_id: str):
    col = get_collection()
    col.delete(f'task_id == "{task_id}"')
    logger.info(f"Milvus 向量删除 | task_id={task_id}")
