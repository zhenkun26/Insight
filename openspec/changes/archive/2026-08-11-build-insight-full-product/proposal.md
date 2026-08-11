## Why

MVP 已证明本地文档导入、混合检索和有依据问答链路可以运行，但索引过程仍是同步调用，检索与问答缺少可观测的工作流状态，知识库规模扩大后难以管理和诊断。现在需要将 MVP 推进为一个可长期本地运行、可重试、可评估、可扩展的完整后端产品，同时保持 local-first、无外部服务也能完成核心测试的特性。

## What Changes

- 将文档解析、切分、Embedding 和向量写入改造成可追踪的索引任务，支持状态查询、失败重试和幂等重建。
- 增强知识库管理，支持按文档来源、标签和状态过滤，并为删除、重建和模型切换提供一致的生命周期语义。
- 将问答链路显式化为可观测工作流：查询分析、混合检索、重排序、相关性判断、生成或拒答，并保留阶段耗时与降级原因。
- 完善搜索与问答 API 的分页、过滤、结构化错误、流式事件和请求追踪字段。
- 增加可选的多轮会话上下文，但上下文必须经过长度限制且不能绕过检索证据约束。
- 增强离线评估，支持 Recall@K、MRR、拒答准确性、阶段耗时和模型配置记录。
- 补充本地部署的持久化目录、健康检查、日志脱敏和运维说明。

## Capabilities

### New Capabilities

- `indexing-jobs`: 可追踪、可重试、幂等的文档索引任务及状态查询。
- `knowledge-base-management`: 文档标签、来源过滤、索引版本和知识库管理语义。
- `workflow-observability`: RAG 阶段状态、耗时、降级原因和脱敏请求追踪。
- `conversation-context`: 有长度约束且仍受检索证据约束的多轮会话上下文。

### Modified Capabilities

- `document-ingestion`: 增加索引任务生命周期、失败恢复和模型版本元数据。
- `hybrid-retrieval`: 增加过滤条件、候选分页和可解释的阶段结果。
- `grounded-question-answering`: 增加工作流阶段、流式事件和多轮上下文约束。
- `http-api`: 增加任务、过滤、分页、会话和统一错误响应接口。
- `evaluation-and-delivery`: 增加拒答评估、阶段延迟统计和持久化部署验证。

## Impact

- 影响 `app/services`、`app/retrieval`、`app/api`、`app/schemas` 和新增 workflow/job 模块。
- 需要扩展 SQLite catalog schema，并为索引任务与会话增加持久化表。
- 可能增加轻量本地依赖，但不引入运行时必须的云服务；LangGraph 仅在工作流可测试且确有收益时加入。
- API 将新增字段和端点；现有 MVP 端点保持向后兼容，除非在实现前明确标记 breaking change。
- 测试、评估脚本、Docker Compose、`.env.example` 和 README 需要同步更新。
