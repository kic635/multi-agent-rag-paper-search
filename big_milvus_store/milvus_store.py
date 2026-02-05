#rag的离线加载过程，不要轻易动代码，后续提供file_path 还有对外检索的接口
import os
import sys
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_milvus import Milvus,BM25BuiltInFunction
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_unstructured import UnstructuredLoader
from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import DataType, RRFRanker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
if sys.platform == 'win32':
    os.environ["CONDA_DLL_SEARCH_MODIFICATION_ENABLE"] = "1"
# 加载环境变量
load_dotenv()

# 1. 加载与切割
loader =UnstructuredLoader(
        file_path='nke-10k-2023.pdf',
        strategy="fast",
        infer_table_structure=False,
        languages=["eng"],
        ocr_engine="paddleocr",
    )
pdf_doc = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", "。", ".", "？", "?", "！", "!", "；", ";", " ", ""],
    chunk_size=1000,
    chunk_overlap=200,
    add_start_index=True,
)
all_splits = text_splitter.split_documents(pdf_doc)
# 2. 向量模型配置
# 稠密向量
model_name = "BAAI/bge-small-zh-v1.5" # 选 small 版本速度快，效果好
model_kwargs = {'device': 'cpu'}      # 强制走 CPU，避开 GPU 的 DLL 报错
encode_kwargs = {'normalize_embeddings': True} # 归一化，适合 L2 距离
dense_embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)
vector_field_names = ["dense_vector", "sparse_vector"]
# 4. 索引参数
index_param = [
    {"index_type": "HNSW", "metric_type": "L2", "params": {"M": 8, "efConstruction": 64}},
    {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "BM25"}
]
######

bm25_func = BM25BuiltInFunction(output_field_names="sparse_vector")
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
    drop_old=True,
    auto_id=True
)

# 写入数据
# ... 前面的加载代码 ...

# --- 核心修复代码：清洗元数据 ---
# --- 升级版：清洗元数据并补全缺失字段 ---
print(f"正在清洗并对齐 {len(all_splits)} 个文档的元数据...")
for doc in all_splits:
    # 1. 补全缺失的 languages 字段，防止 Milvus 报错 DataNotMatch
    if "languages" not in doc.metadata:
        doc.metadata["languages"] = "unknown"  # 给个默认值
    else:
        # 如果有，确保它是字符串
        if isinstance(doc.metadata["languages"], list):
            doc.metadata["languages"] = ", ".join(doc.metadata["languages"])

    # 2. 对齐其他字段（把所有 list/dict 转成字符串，防止其他列也报错）
    # 尤其是 Unstructured 产生的 coordinates 字段，一定要转字符串
    keys_to_fix = [k for k, v in doc.metadata.items() if isinstance(v, (list, dict))]
    for key in keys_to_fix:
        doc.metadata[key] = str(doc.metadata[key])

# --- 现在再执行写入 ---
print("正在写入 Milvus...")
store.add_documents(all_splits[0:2])

# 6. 构建检索链
# 基础检索：混合检索 + RRF 重排
base_retriever = store.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 20,
       #"reranker": RRFRanker()
    }
)

# 精排阶段 (Reranker)
# 注意：如果本地加载 BGE 模型依然报 DLL 错误，建议检查是否安装了 torch

model = HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-base")
compressor = CrossEncoderReranker(model=model, top_n=3)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)

# 7. 运行检索
try:
    query = "When was Nike incorporated?"
    results = compression_retriever.invoke(query)
    for i, doc in enumerate(results):
        print(f"Result {i+1}:\n{doc.page_content[:20]}...\n")
except Exception as e:
    print(f"检索出错: {e}")
res=base_retriever.invoke("When was Nike incorporated?")
print(res)