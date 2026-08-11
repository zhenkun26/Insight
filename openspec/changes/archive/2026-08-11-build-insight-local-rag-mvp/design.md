## Context

仓库目前只有 OpenSpec 配置，没有应用代码或既有数据模型。项目需要在本地优先运行，同时允许以后切换到独立 Milvus、真实 Ollama 和可选 Rerank 服务；核心行为必须能在无外部服务的 CI 中测试。详细行为约束见本 change 下的 capability specs。

## Goals / Non-Goals

**Goals:**

- 形成一条从文档导入到带引用问答的可运行 MVP 链路。
- 将解析、索引、检索、重排、生成和 API 解耦，方便 mock 与替换。
- 默认使用环境变量配置模型、地址、Top-K、阈值和持久化目录。
- 保留可追溯的文档、页码、章节和文本块信息。

**Non-Goals:**

- 不实现多用户权限、在线 SaaS、复杂前端或多智能体协作。
- 不承诺未经评估的准确率、延迟或生产容量。
- 不把 LangGraph 作为启动必需依赖；只有当显式状态图能改善可观测性时才引入。

## Decisions

### 1. SQLite 作为文档目录，Milvus 作为向量索引

文档记录、内容指纹、文本块和索引状态放在 SQLite，向量数据放入 Milvus/Milvus Lite。这样删除、重建和列出文档不依赖向量库的元数据查询能力。相较只使用 Milvus，SQLite 更容易测试和迁移；相较只使用本地文件，SQLite 能提供一致的生命周期状态。

### 2. 使用显式 RAG 服务编排，保留 LangGraph 扩展点

MVP 采用 `QuestionAnsweringService` 组织 query analysis、retrieve、rerank、relevance check、answer/fallback 五个步骤，每一步通过协议或接口隔离。直接使用 LangGraph 会增加依赖和状态序列化复杂度；后续如果需要节点重试、可视化或持久化状态，可在不改变 HTTP 契约的情况下替换为 LangGraph adapter。

### 3. Ollama 使用 HTTP adapter，不在业务代码中硬编码模型

LLM 和 Embedding 通过独立客户端读取 `LLM_BASE_URL`、`LLM_MODEL`、`EMBEDDING_MODEL` 等环境变量。测试使用 fake adapter；生产本地运行连接 Ollama。这样可以避免 import 或启动阶段要求模型存在，也能清晰区分服务不可用与无依据拒答。

### 4. BM25 与向量结果采用 RRF 融合

两路结果先按稳定文本块 ID 去重，再使用 RRF 产生统一排序，最终应用 `TOP_K` 和 `SCORE_THRESHOLD`。RRF 不要求不同检索器的分数可直接比较，适合 BM25 与向量分数尺度不同的情况；候选结果仍保留各路分数以支持调试和评估。

### 5. Rerank 是可选能力且必须可降级

Reranker 通过协议注入，默认关闭或使用环境变量开启。模型不可用时保持混合检索顺序并记录 fallback 状态，不返回伪造的重排分数。MVP 不强制下载大模型，避免 Docker 和 CI 失去可运行性。

### 6. 测试分层并隔离外部服务

解析、切分、BM25、RRF 和 schema 使用纯单元测试；向量、Ollama、上传和问答使用 fake/mock adapter 与 FastAPI TestClient；可选集成测试单独标记。CI 只执行默认无外部依赖的测试。

## Risks / Trade-offs

- [Risk] PDF 的标题和页码结构因文件格式差异而不稳定 → 保留页码（可用时）并将章节识别设计为启发式，README 明确限制。
- [Risk] Milvus Lite 与独立 Milvus 的行为或 URI 配置存在差异 → 统一向量存储协议，并在 Docker Compose 和本地模式分别提供配置示例。
- [Risk] BM25 索引和 SQLite 文档目录可能不同步 → 所有索引操作通过统一 IndexManager，重建时先生成临时索引再切换状态。
- [Risk] LLM 仍可能生成超出上下文的内容 → 使用严格系统提示词、来源标识、上下文阈值和拒答分支，并在测试中 mock 验证。
- [Risk] 评估结果受模型和示例语料影响 → 输出运行日期、模型、参数和数据集版本，README 不预填指标。

## Migration Plan

1. 创建运行时目录和 SQLite schema，导入示例文档并建立本地索引。
2. 通过 `.env` 配置 Ollama 与 Milvus Lite；需要独立服务时切换 `MILVUS_URI` 并重新索引。
3. 运行单元测试和评估脚本，确认结果后再启用可选 Rerank。
4. 回滚时停止容器并删除本地运行时索引目录；源文档与代码不受影响，随后可重新导入和索引。

## Open Questions

- 独立 Milvus 的生产部署参数可以在 MVP 完成后根据实际 Docker 运行结果微调，不改变 API 或检索契约。
