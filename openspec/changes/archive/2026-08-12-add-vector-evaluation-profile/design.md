## Context

现有 `HybridRetriever` 总是先执行 BM25，再根据是否注入 Embedding/VectorStore 执行向量召回；评估脚本只构建 BM25 index，不能真实验证 Ollama Embedding 和 Milvus Lite。项目依赖已包含 `pymilvus[milvus_lite]`，但默认配置刻意不连接外部服务。

## Goals / Non-Goals

**Goals:**

- 为检索器增加显式且向后兼容的关键词、向量、混合模式。
- 为评估脚本提供可 mock 的内存向量路径和显式 Milvus Lite 路径。
- 在评估结果中区分模式、后端、模型配置和实际向量阶段耗时。
- 在外部配置不完整时快速失败，不把空索引或 fallback 指标当作真实向量结果。

**Non-Goals:**

- 不改变默认 API 检索模式、RRF 公式、阈值或候选排序。
- 不在 CI 启动 Ollama、Milvus 或下载模型。
- 不将向量评估结果写入仓库或 README 固定指标。
- 不新增向量数据库抽象；复用现有 `VectorStore`、`OllamaClient` 和 `MilvusVectorStore` adapter。

## Decisions

### Add a keyword-enabled switch at the retriever boundary

在 `HybridRetriever` 增加末尾可选的 `keyword_enabled` 参数，默认 `True`，避免破坏现有位置参数调用。关闭时不调用 BM25，并将 keyword stage 标记为 disabled；向量依赖仍沿用现有注入方式。相比在评估脚本中塞入空 BM25 index，这能让状态和计时准确反映实际执行路径。

### Use explicit evaluation modes and backends

评估 CLI 增加 `--retrieval-mode bm25|vector|hybrid` 和 `--vector-backend memory|milvus`。`memory` 仅用于 fake/本地测试和快速实验；`milvus` 要求显式 `--milvus-uri`，并使用唯一或用户指定的 collection。vector/hybrid 统一使用 `OllamaClient.embed`，从而真实模式与应用生产 adapter 一致。

### Fail fast before evaluation

选择 vector/hybrid 时验证 Embedding 模型、向量 backend 和 Milvus URI（Milvus backend）后再构建索引。Embedding 或 Milvus 初始化/upsert/search 的异常保留原始异常类别并终止该次评估；只有 BM25 模式允许在无外部服务环境成功完成。

### Preserve existing JSON compatibility

继续保留 `profile`、`hit_rate`、`mrr`、`refusal_accuracy`、`average_latency_ms` 和已有 stage timing 字段；新增 `retrieval_mode`、`vector_backend`、`models.embedding` 和向量参数。默认 BM25 的旧命令和指标语义不变。

## Risks / Trade-offs

- [Risk] Ollama Embedding 首次加载使延迟和结果波动 → 输出记录模型、日期、超时和阶段耗时，不写固定性能承诺。
- [Risk] Milvus Lite collection 残留影响重复运行 → 支持显式 collection 名称；真实 smoke 使用临时 URI/collection，失败后清理临时文件。
- [Risk] vector-only 模式误执行 BM25 → 由 `keyword_enabled=False` 和状态断言测试保护。
- [Risk] 向量维度变化导致已有 collection 不兼容 → 用户切换 Embedding 模型后使用新的 URI/collection 或重建，错误快速暴露。

## Migration Plan

1. 先加入检索器开关和离线 fake/memory 测试，确认默认路径无行为变化。
2. 加入 CLI 参数、结果字段和 README 命令；默认 CI 不变。
3. 在本机显式启动 Ollama，使用临时 Milvus Lite URI 执行一次真实 hybrid smoke；服务停止后保留结果摘要，不提交数据库文件。
4. 回滚时删除新增 CLI/开关和评估字段，不需要数据迁移；应用现有 BM25/hybrid API 继续可用。
