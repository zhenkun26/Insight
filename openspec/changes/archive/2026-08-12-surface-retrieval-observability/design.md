## Context

`HybridRetriever.search` 已在每次调用后写入 `last_status` 和 `last_timings`。当前 `/search` 只读取状态，并把单一 retrieval stage 的 `latency_ms` 固定为 0；控制台也只显示响应总耗时，因此已经存在的诊断信息没有被客户端使用。

## Goals / Non-Goals

**Goals:**

- 在不改变检索结果的前提下，将检索器阶段信息转换为稳定的 API 响应结构。
- 让未启用阶段与真实快速阶段可区分，并保留向量失败时的 fallback 状态。
- 在无前端构建工具的控制台中展示阶段状态和耗时。

**Non-Goals:**

- 不新增指标存储、追踪系统或前端依赖。
- 不修改 BM25、向量召回、RRF、阈值或 Rerank 算法。
- 不把完整用户问题、文档正文或模型响应写入日志。

## Decisions

### Use the retriever timing boundary as the source of truth

`/search` 在 `retriever.search` 返回后复制 `last_status` 和 `last_timings`，将五个固定阶段映射为 `stages` 条目。这样阶段耗时与评估脚本、检索器本身使用同一计时边界；不额外在路由层重复测量子阶段。

### Keep the existing response additive

保留原有 `latency_ms`、`retrieval_status` 和结果字段，继续用 `stages` 返回扩展信息。旧客户端可以忽略新条目，新客户端可以按 `name` 读取；未启用阶段的 `latency_ms` 使用 `null`，状态使用 `disabled`。

### Render stages as compact diagnostic chips

控制台在结果列表上方显示阶段 chips，包含状态和耗时；结果为空时仍显示 chips。前端只消费 API 已返回的数据，不重新推断依赖是否可用。

## Risks / Trade-offs

- [Risk] 不同客户端可能假设 `stages[].latency_ms` 总是数字 → 保留 Pydantic 宽松字典结构，并在 README 明确 disabled 阶段使用 null。
- [Risk] `last_timings` 是单次请求状态，不适合跨请求统计 → API 只在当前检索调用后立即复制，不保存长期聚合数据。
- [Risk] 外部服务失败信息可能过于具体 → 继续复用现有降级状态，仅返回异常类别，不暴露地址凭据。

## Migration Plan

1. 扩展 `/search` 响应构造和控制台渲染，增加 API/静态资源回归测试。
2. 保持现有客户端兼容；升级后无需数据库或索引迁移。
3. 若需回滚，只删除新增 `stages` 展示和映射，检索算法与持久化数据不受影响。
