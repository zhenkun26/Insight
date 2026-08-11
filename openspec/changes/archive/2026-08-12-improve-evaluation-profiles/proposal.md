## Why

当前评估脚本只运行 BM25-only 基线，虽然结果可复现，但无法比较确定性关键词重排和本地 Ollama 重排，也没有把关键词召回、重排和总耗时拆开记录。增加显式评估 profiles 后，项目可以用同一问题集真实比较不同检索配置，而不是把单一路径指标误认为完整 RAG 指标。

## What Changes

- 为评估脚本增加 `disabled`、`keyword` 和 `ollama` 三种重排模式，默认保持 `disabled`。
- 允许通过 CLI 指定重排模型、Ollama 地址、请求超时和 Top-K。
- 为混合检索记录关键词、向量、融合、重排和总耗时阶段信息。
- 评估输出记录 profile、模型配置、阶段平均耗时和每条问题的阶段数据。
- 保持 CI 使用默认无外部服务 profile；Ollama profile 仅由用户显式启用。
- 增加评估脚本回归测试和 README 使用示例。

## Capabilities

### New Capabilities

<!-- No new top-level capability; this improves the existing evaluation contract. -->

### Modified Capabilities

- `evaluation-and-delivery`: 扩展可复现评估 profile、阶段耗时和可选本地模型评估输出。

## Impact

- Affected code: `scripts/evaluate.py`、`HybridRetriever` 计时状态、测试、README 和评估规格。
- Runtime: 默认评估不访问 Ollama、Milvus 或外部 API；`ollama` profile 会按候选数量产生本地模型请求。
- Output compatibility: 保留现有 hit rate、MRR、拒答准确率和平均延迟字段，新增字段向后兼容 JSON 消费者。
- No database, document, or index migration is required.
