## Context

当前应用的 API、任务服务和 SSE 问答链路已经可独立运行；本变更只增加一个同源展示层。项目需要保持 Python-only 的本地部署特性，Docker 镜像也不应新增 Node 或构建阶段。

## Goals / Non-Goals

**Goals:**

- 用一个轻量、可读、可直接查看源码的页面串起现有核心 API。
- 覆盖上传与任务轮询、文档列表、搜索、流式问答、来源和工作流状态展示。
- 在浏览器取消请求时释放当前请求，并保留已接收内容。
- 通过 FastAPI 测试验证入口页、静态资源和既有 API 路由的兼容性。

**Non-Goals:**

- 不引入 React/Vue、打包器、前端路由、用户认证或多用户权限。
- 不在浏览器中实现检索、切分、模型调用等后端逻辑。
- 不把控制台做成独立部署的生产前端，也不新增跨域代理。

## Decisions

### Same-origin static assets

页面放在 `app/web/`，由 FastAPI 在 `/` 提供入口、在 `/assets/` 提供 CSS 和 JavaScript。选择同源静态服务而不是独立前端服务，是因为所有 API 本来就在同一个本地进程中，能够避免 CORS 配置和额外运行时。

### Browser Fetch for JSON and SSE

JavaScript 使用 `fetch` 调用现有 JSON API；问答流使用 `fetch` 的 `ReadableStream` 读取 POST 返回的 SSE，因为浏览器原生 `EventSource` 不支持 POST 请求体。客户端只解析 `event:`/`data:` 块并根据已有事件类型更新界面，不复制后端 RAG 逻辑。

### Explicit workspace state

页面使用三个独立工作区：文档、搜索、问答。每个工作区维护加载中、成功、空结果和错误状态，避免把网络请求异常误显示成无依据回答。上传后仅轮询任务状态，最终文档列表仍从服务端刷新。

### Dependency-free progressive enhancement

HTML 在无 JavaScript 时仍显示项目说明和 API 提示；交互通过原生 DOM、FormData 和 AbortController 实现。样式采用本地 CSS，保证离线或无外网时仍可使用。

## Risks / Trade-offs

- [Risk] 浏览器无法访问模型或 Milvus 时问答/索引失败 → 将后端错误和任务失败状态原样转成可读提示，保留 API 诊断信息，不伪造成功。
- [Risk] 长回答流中途断开 → 保留已收到的内容并标记连接中断；用户可以重新提交问题。
- [Risk] 纯原生 JavaScript 的复杂交互可维护性有限 → 将 DOM 更新和 SSE 解析拆成小函数，并用页面入口测试覆盖关键资源；后续若需求显著增长再评估前端框架。
- [Risk] 静态资源路径和 API 路由冲突 → 使用独立 `/assets/` 前缀，并先注册 API 路由再注册根入口，测试 `/health` 等既有接口仍可访问。

## Migration Plan

1. 添加 `app/web/` 静态资源和 FastAPI 静态入口。
2. 在本地运行现有测试及页面入口测试。
3. 重新构建 Docker 镜像；镜像无需额外安装前端依赖。
4. 回滚时删除静态入口和 `app/web/` 文件即可，不涉及数据库或索引格式迁移。
