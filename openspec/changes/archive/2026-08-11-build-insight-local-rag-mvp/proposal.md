## Why

气象业务资料通常分散在 PDF、Markdown 和文本文件中，人工查找规范、预警说明和流程信息成本较高。需要一个可在本地运行、可测试、可公开发布的 RAG MVP，将文档导入、混合检索和带来源问答串成一条真实可运行的链路，同时在缺乏依据时明确拒答。

## What Changes

- 创建 Python 3.11+ FastAPI 应用与环境变量配置体系。
- 支持 PDF、Markdown、TXT 文档解析、清洗、分块、元数据保留、重复检测、重建索引和删除文档。
- 建立基于 Ollama Embedding 与 Milvus/Milvus Lite 的向量索引，以及可持久化的 BM25 关键词索引。
- 实现可解释的 BM25 + 向量 RRF 混合检索、可选 Rerank、相关性阈值和检索结果来源信息。
- 实现 `/chat`、`/chat/stream`、`/search`、文档管理和健康检查接口，回答必须受检索上下文约束并返回引用。
- 为模型调用、向量数据库和 Rerank 提供可替换接口，使核心测试不依赖 Ollama、Milvus 或外部 API。
- 提供示例气象文档、pytest 测试、检索评估脚本、Docker Compose、Dockerfile、README 和 GitHub Actions CI。

## Capabilities

### New Capabilities

- `document-ingestion`: 解析、清洗、分块、元数据保留、重复检测和索引生命周期管理。
- `hybrid-retrieval`: 向量召回、BM25 召回、RRF 融合、去重、Top-K、阈值和可选重排序。
- `grounded-question-answering`: 基于检索上下文生成带来源回答，并在证据不足时拒答。
- `http-api`: 通过 FastAPI 暴露文档管理、搜索、问答和健康检查接口。
- `evaluation-and-delivery`: 提供无外部服务依赖的自动化测试、真实评估脚本、容器化运行和 CI。

### Modified Capabilities

- 无。当前 `openspec/specs/` 尚无既有能力规格。

## Impact

- 新增 `app/` 应用包、`tests/`、`scripts/`、`data/sample_docs/` 和项目配置文件。
- 新增 FastAPI、Pydantic、Uvicorn、PDF 解析、BM25、Milvus、Ollama 客户端及测试相关依赖。
- 新增 SQLite 文档目录、Milvus 向量集合、BM25 索引文件等本地运行时状态；运行时目录需加入 `.gitignore`。
- 新增 Docker Compose 与 GitHub Actions 配置；CI 只运行 mock/内存测试，不依赖真实 Ollama、Milvus 或外部 API。
