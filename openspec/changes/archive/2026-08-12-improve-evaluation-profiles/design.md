## Context

现有 `scripts/evaluate.py` 构建 BM25-only 检索器并输出总延迟；`HybridRetriever` 已有可选向量和 Rerank，但没有公开阶段计时。评估需要继续在没有外部服务的 CI 中稳定运行，同时允许用户显式启用本地 Ollama profile。

## Goals / Non-Goals

**Goals:**

- 用一个脚本入口比较关闭重排、关键词重排和 Ollama 重排。
- 保留现有 JSON 字段，新增 profile、阶段耗时和可选模型参数。
- 让检索器在每次 search 后暴露本次调用的阶段计时，不保存跨请求累计状态。
- 对未执行的阶段使用明确的 `disabled` 状态，避免把缺失服务误当成零延迟。

**Non-Goals:**

- 不把评估脚本变成线上任务调度器或持久化评估数据库。
- 不在 CI 默认运行 Ollama、Milvus 或耗时模型评估。
- 不改变检索排序算法、阈值语义或文档样本内容。

## Decisions

### Explicit profile selection

CLI 使用 `--reranker-mode disabled|keyword|ollama`，默认 disabled；ollama 模式要求显式模型名或读取环境变量，并复用生产服务的 `OllamaClient`/`OllamaReranker`。这样 CI 命令不会因用户环境变量意外访问外部服务。

### Timings at the retrieval boundary

`HybridRetriever.search` 在关键词、向量、融合、重排和总流程边界使用 `perf_counter`，将毫秒值写入 `last_timings`。评估脚本在每条问题完成后复制该字典，随后计算每个阶段的平均值。

### Separate status from timing

阶段是否执行由 `last_status` 表示，耗时只表示已执行阶段。未启用阶段不伪造 `0`，评估输出使用 `null` 或 `disabled`，从而能区分未执行和真实快速完成。

### Preserve output compatibility

继续输出 `hit_rate`、`mrr`、`refusal_accuracy`、`average_latency_ms` 和 `rows`；新增字段只扩展 JSON。旧的 README/CI 命令不带新参数时，结果仍是 BM25-only baseline。

## Risks / Trade-offs

- [Risk] 计时会受模型加载、系统调度和本地缓存影响 → 每次运行记录日期、profile、模型和参数，不把一次结果写成固定性能承诺。
- [Risk] Ollama profile 产生较多本地调用 → 必须显式选择，并让候选数量受 `CANDIDATE_K`/Top-K 控制。
- [Risk] 阶段字段被错误消费 → 保留已有字段，新增字段使用稳定的字典结构并添加 JSON 回归测试。
- [Risk] 模型服务不可用 → profile 运行前快速失败并保留清晰错误；默认 profile 不依赖该服务。

## Migration Plan

1. 更新检索器计时和评估脚本，默认行为保持不变。
2. 运行现有 CI smoke test，确认无外部服务依赖。
3. 本地按需运行 keyword 或 ollama profile，并将输出文件作为实验记录而不是仓库固定指标。
4. 回滚时删除新增 CLI 参数和 timing 字段即可，不涉及数据迁移。
