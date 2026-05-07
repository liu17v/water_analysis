"""Milvus 向量数据库操作"""
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from app.config.settings import get_settings
from app.utils.log_config import get_logger

logger = get_logger("services.milvus")
settings = get_settings()

COLLECTION_NAME = "task_features"
DIM = 13

_collection = None


def connect():
    connections.connect(host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)


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
    _collection.create_index("feature_vector", {"metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 128}})
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
    col = get_collection()
    col.load()
    results = col.search(
        data=[vector], anns_field="feature_vector",
        param={"metric_type": "L2", "params": {"nprobe": 16}},
        limit=top_k, output_fields=["task_id", "created_at", "reservoir_name"],
    )
    return [
        {"task_id": h.entity.get("task_id"), "distance": h.distance,
         "created_at": h.entity.get("created_at"), "reservoir_name": h.entity.get("reservoir_name")}
        for h in results[0]
    ]


def delete(task_id: str):
    col = get_collection()
    col.delete(f'task_id == "{task_id}"')
    logger.info(f"Milvus 向量删除 | task_id={task_id}")
