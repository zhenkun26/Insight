## Why

当前评估脚本默认只验证 BM25，虽然线上检索器已经支持向量召回和 RRF 融合，但没有一个可复现入口证明 Ollama Embedding 与 Milvus Lite 的真实链路能够参与评估。增加显式的向量和混合 profile 后，项目可以分别测量关键词、语义和联合召回，而不会把外部服务依赖带入默认 CI。

## What Changes

- 为评估脚本增加 `bm25`、`vector` 和 `hybrid` 检索模式，默认保持 `bm25`。
- 为检索器增加可选的关键词召回开关，使 vector-only 评估不执行 BM25。
- 允许显式配置 Ollama Embedding 地址、模型、Milvus URI 和集合名。
- 向评估输出增加检索模式、向量后端和 Embedding 配置，并复用现有阶段计时。
- 增加 fake embedding + 内存向量库测试、Milvus adapter 契约测试和配置校验。
- README 增加离线、内存向量和真实 Milvus Lite 评估命令，明确外部服务 caveat。
- 保持默认 CI 不调用 Ollama、Milvus 或外部网络。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `hybrid-retrieval`：支持可解释的 BM25-only、vector-only 和 hybrid 检索模式。
- `evaluation-and-delivery`：支持显式向量评估 profile 和真实本地向量链路记录。

## Impact

- Affected code: `app/retrieval/hybrid.py`、`scripts/evaluate.py`、向量相关测试、README 和 OpenSpec。
- Runtime: vector/hybrid profile 显式使用 Ollama Embedding；Milvus backend 写入用户指定的本地 URI 或远程集合。
- Compatibility: 默认命令、默认 JSON 指标和现有 API 检索行为保持不变；不需要数据库 schema migration。
