## Why

`HybridRetriever` 已经记录了关键词、向量、融合、重排和总耗时，但 `/search` 仍返回固定的零耗时阶段，Web Console 也只能看到总耗时。把真实阶段信息透传到 API 和控制台，可以让本地运行者区分慢在哪一步以及是否发生降级。

## What Changes

- 让 `/search` 返回每个检索阶段的真实耗时和状态。
- 保持现有搜索字段、排序、过滤、分页和 trace_id 行为不变。
- 在 Web Console 的检索区域展示阶段状态和耗时，包括未启用阶段。
- 增加 API 和静态控制台回归测试，并补充 README 的响应说明。
- 不改变检索算法、阈值语义或默认外部服务依赖。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `http-api`：扩展搜索响应中的阶段状态与耗时契约。
- `workflow-observability`：让检索子阶段的实际计时和降级状态出现在搜索响应中。
- `web-console`：在搜索结果区域展示检索阶段信息。

## Impact

- Affected code: `app/api/routes.py`、`app/schemas/api.py`、`app/web/app.js`、测试和 README。
- Runtime: 仅增加响应字段和前端展示，不新增依赖，不主动连接外部服务。
- Compatibility: 新字段为扩展字段，保留原有 `/search` 响应结构和检索行为。
