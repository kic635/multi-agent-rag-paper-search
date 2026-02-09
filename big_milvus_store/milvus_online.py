
import os
import sys
from dotenv import load_dotenv
from langchain_core.tools import Tool
from langchain_milvus import Milvus,BM25BuiltInFunction
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from gptcache import cache
from gptcache.manager import get_data_manager, CacheBase, VectorBase
from gptcache.similarity_evaluation import SearchDistanceEvaluation


# ======================== 关键优化：全局初始化资源（只加载一次） ========================
# 1. 初始化 Embedding 模型（全局只加载一次）
model_name = "BAAI/bge-small-zh-v1.5"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': True}
dense_embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# 2. 初始化 Milvus 相关配置（全局只加载一次）
vector_field_names = ["dense_vector", "sparse_vector"]
index_param = [
    {"index_type": "HNSW", "metric_type": "L2", "params": {"M": 8, "efConstruction": 64}},
    {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "BM25"}
]
bm25_func = BM25BuiltInFunction(output_field_names="sparse_vector")
# 3. 初始化 Milvus 连接和 Retriever（全局只加载一次）
try:
    store = Milvus(
        embedding_function=dense_embeddings,
        collection_name="test_nike_final_v3",
        connection_args={
            "host": "localhost",
            "port": "19530"
        },
        index_params=index_param,
        vector_field=["dense_vector", "sparse_vector"],
        text_field="text",
        builtin_function=bm25_func,
        drop_old=False,
        auto_id=True
    )

    # 基础检索器
    base_retriever = store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 20,
            "vector_fields": ["dense_vector", "sparse_vector"],
        }
    )

    # 精排 Reranker（全局只加载一次）
    reranker_model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
    compressor = CrossEncoderReranker(model=reranker_model, top_n=3)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever
    )
except Exception as e:
    raise RuntimeError(f"初始化 RAG 资源失败：{str(e)}")



#缓存相关配置
evaluation =SearchDistanceEvaluation(max_distance=0.1, positive=False)
cache.init(
    pre_embedding_func=dense_embeddings.embed_query,
    data_manager=get_data_manager(
        cache_base=CacheBase('sqlite'),
        vector_base=VectorBase('faiss', dimension=512)
    ),
    similarity_evaluation=evaluation,
)



# ======================== Tool 定义（核心逻辑） ========================


def rag_res(query: str) -> str:
    """
    不依赖 cache.search 的通用兼容版
    """
    try:
        print(f"[RAG Tool] 收到查询: {query}")

        # 1. 手动向量化查询语句
        query_embedding = dense_embeddings.embed_query(query)

        cached_results = cache.data_manager.search(query_embedding, count=1)

        if cached_results:
            if cached_results:
                score = cached_results[0][0]
                THRESHOLD = 0.05
                if score < THRESHOLD:
                    cached_answer = cached_results[0][1]
                    print(f"[GPTCache] 命中语义缓存！分数: {score:.4f}")
                    return cached_answer
                else:
                    print(f"[GPTCache] 距离太远 (分数: {score:.4f}), 判定为未命中。")
        # --- 缓存未命中，执行向量库检索 ---
        print(f"[RAG Tool] 缓存未命中，开始执行向量检索...")
        results = compression_retriever.invoke(query)

        if not results:
            return "未在知识库中找到相关结果。"

        # 格式化检索结果
        formatted_results = []
        for idx, doc in enumerate(results, 1):
            content = doc.page_content[:300] if len(doc.page_content) > 300 else doc.page_content
            formatted_results.append(f"结果{idx}:\n{content}\n")

        result_text = "\n".join(formatted_results)

        # 3. 回写缓存 (参数名保持你之前跑通的 answer 和 embedding_data)
        cache.data_manager.save(
            question=query,
            answer=result_text,
            embedding_data=query_embedding
        )
        print(f"[RAG Tool] 已更新语义缓存。")

        return result_text

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"知识库查询失败: {str(e)}"

# 创建 Tool 实例
rag_tool = Tool(
    name="search_knowledge_base",
    description="查询知识库中相关信息,根据知识库中信息回答问题",
    func=rag_res,
    return_direct=False
)

