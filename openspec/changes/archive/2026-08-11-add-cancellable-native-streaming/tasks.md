## 1. 任务取消

- [x] 1.1 扩展 IndexJobService 保存 Future 引用并实现 queued 任务取消、running 任务不可取消和幂等状态处理。
- [x] 1.2 增加 `POST /jobs/{job_id}/cancel` 及结构化错误响应。
- [x] 1.3 增加任务取消、竞态和取消后不执行索引回调测试。

## 2. 原生模型流式

- [x] 2.1 为 OllamaClient 增加 NDJSON `stream_generate`，逐片段校验 response/done 字段并脱敏处理异常。
- [x] 2.2 为 QA 服务增加一次检索、多片段生成和安全 fallback 的流式结果。
- [x] 2.3 更新 `/chat/stream` SSE 事件，支持 stream_mode、片段序号和首片段延迟。
- [x] 2.4 增加 fake stream、断流 fallback、拒答不调用模型和 SSE 顺序测试。

## 3. 文档与交付

- [x] 3.1 更新 README 的取消接口、原生流式与 fallback 说明。
- [x] 3.2 运行 ruff、pytest、评估、OpenSpec strict、Docker Compose config 和 diff 检查。
- [x] 3.3 使用本地 Ollama 验证多片段 SSE；无服务时明确记录 BLOCKED。
- [x] 3.4 同步主规格、归档变更、提交并推送公开仓库。
