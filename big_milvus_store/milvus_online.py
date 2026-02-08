
import os
import sys
from dotenv import load_dotenv
from langchain_core.tools import Tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_milvus import Milvus,BM25BuiltInFunction
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_unstructured import UnstructuredLoader
from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import DataType, RRFRanker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker

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


# ======================== Tool 定义（核心逻辑） ========================
def rag_res(query: str) -> str:
    """
    RAG 知识库查询核心函数
    
    Args:
        query: 用户查询字符串
        
    Returns:
        格式化后的检索结果字符串
    """
    try:
        print(f"[RAG Tool] 收到查询: {query}")
        results = compression_retriever.invoke(query)
        print(f"[RAG Tool] 检索到 {len(results)} 条结果")

        if not results:
            return "未在知识库中找到相关结果。"

        # 格式化结果，限制长度避免token溢出
        formatted_results = []
        for idx, doc in enumerate(results, 1):
            content = doc.page_content[:300] if len(doc.page_content) > 300 else doc.page_content
            formatted_results.append(f"结果{idx}:\n{content}\n")
        
        result_text = "\n".join(formatted_results)
        print(f"[RAG Tool] 返回结果长度: {len(result_text)} 字符")
        return result_text

    except Exception as e:
        error_msg = f"知识库查询失败: {str(e)}"
        print(f"[RAG Tool Error] {error_msg}")
        return error_msg


# 创建 Tool 实例
rag_tool = Tool(
    name="search_knowledge_base",
    description="查询知识库中相关信息,根据知识库中信息回答问题",
    func=rag_res,
    return_direct=False
)

