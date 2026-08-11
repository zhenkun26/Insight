## 1. 数据模型与配置迁移

- [x] 1.1 扩展 Settings，增加任务 worker 数、会话预算、索引版本、日志脱敏和默认分页配置。
- [x] 1.2 为 DocumentCatalog 增加幂等 SQLite 迁移，补充文档元数据/索引版本字段以及 index_jobs、sessions、session_messages 表。
- [x] 1.3 扩展 domain models 和 Pydantic schemas，统一表达任务、阶段事件、过滤条件、分页、trace_id 和会话字段。
- [x] 1.4 为迁移、旧数据兼容、标签更新和会话清理增加单元测试。

## 2. 索引任务与文档生命周期

- [x] 2.1 实现 IndexJobService 和受控 ThreadPoolExecutor，支持 queued/running/succeeded/failed/cancelled 状态、进度和脱敏错误。
- [x] 2.2 将上传和重建索引改为创建任务并立即返回 job_id，保留重复文档的幂等响应。
- [x] 2.3 实现任务查询与失败重试 API，处理进程启动时遗留 running 任务的恢复策略。
- [x] 2.4 让删除文档、重建索引和模型切换更新文档状态、索引版本和向量内容，避免孤立 chunk。
- [x] 2.5 增加任务并发、失败回滚、重试和重复提交测试。

## 3. 知识库元数据与过滤检索

- [x] 3.1 实现文档来源、标签、描述的更新和列表过滤能力。
- [x] 3.2 扩展 BM25、向量存储和 HybridRetriever 的统一过滤参数、稳定排序与 offset/limit 分页。
- [x] 3.3 在 Milvus 不支持本地过滤时实现 catalog 允许集合过滤，并报告过滤降级状态。
- [x] 3.4 增加双路召回过滤、空结果、分页和索引版本不匹配测试。

## 4. 可观测 RAG 工作流

- [x] 4.1 实现显式 WorkflowState、StageEvent 和 trace_id 生成/透传逻辑。
- [x] 4.2 将 query_analysis、retrieval、rerank、relevance_check、generation/fallback 阶段接入 QA 服务并保留阶段耗时。
- [x] 4.3 将向量不可用、rerank fallback、LLM 错误和拒答原因转换为稳定的状态字段。
- [x] 4.4 增加脱敏结构化日志，覆盖请求、任务和外部依赖错误，不写入完整 query、正文或密钥。
- [x] 4.5 增加工作流阶段顺序、trace 透传、fallback 和日志字段测试。

## 5. 会话与流式问答

- [x] 5.1 实现受轮数、字符数和单轮长度限制的 SessionService，支持追加、读取和删除。
- [x] 5.2 将 session_id 历史仅用于查询分析辅助，确保事实回答仍只使用本轮检索上下文。
- [x] 5.3 将 `/chat/stream` 改为 SSE，输出 start/retrieval/source/token/complete/error 事件并正确设置媒体类型。
- [x] 5.4 增加会话截断、历史不能替代证据、会话删除和 SSE 事件顺序测试。

## 6. HTTP API 完整化

- [x] 6.1 增加 `/jobs/{job_id}`、`/jobs/{job_id}/retry`、文档元数据更新和 `/sessions/{session_id}` 删除接口。
- [x] 6.2 扩展 `/documents`、`/search`、`/chat` 请求/响应，支持过滤、分页、session_id、trace_id 和结构化错误。
- [x] 6.3 保持现有 MVP 响应字段兼容，并为新错误返回稳定 error_code、request_id/trace_id 和安全 detail。
- [x] 6.4 更新 OpenAPI 示例与 API 集成测试，覆盖异步任务轮询和 mock 问答。

## 7. 评估、部署与文档

- [x] 7.1 扩展评估数据和脚本，真实统计 Recall@K、MRR、拒答准确性、阶段耗时和运行配置。
- [x] 7.2 更新 Dockerfile、Compose 和环境示例，持久化 SQLite/BM25/上传/Milvus Lite 路径并补充健康检查。
- [x] 7.3 更新 README 的完整版架构、任务 API、过滤搜索、SSE、会话、恢复策略和已知限制说明。
- [x] 7.4 增加 CI 中的迁移、API、评估 smoke test 与关键模块导入检查。

## 8. 验证与交付

- [x] 8.1 运行 ruff、pytest、OpenSpec strict validate、Docker Compose config 和 git diff --check。
- [x] 8.2 使用合成气象资料执行一次 BM25-only 评估并记录真实输出，不在 README 伪造指标。
- [x] 8.3 使用 Ollama/Milvus Lite（可用时）完成一次端到端上传、任务轮询、过滤搜索、问答和 SSE 验证。
- [x] 8.4 同步主规格、归档变更、提交并推送公开仓库，记录未完成的非目标能力。
