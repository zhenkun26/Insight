## Purpose

为本地运行的 Insight 提供一个无需额外前端构建工具的浏览器操作入口，让用户可以直观看到文档索引、检索结果、流式问答和来源引用。

## ADDED Requirements

### Requirement: Local console access
系统 SHALL 在同源浏览器页面提供 Insight 控制台，并展示应用名称、知识库状态和主要工作区。

#### Scenario: Open the console
- **WHEN** 用户访问应用根路径 `/`
- **THEN** 浏览器获得可渲染的 Insight 控制台页面，页面资源由当前应用提供

#### Scenario: Use the console without frontend tooling
- **WHEN** 用户仅启动 FastAPI 应用而未安装 Node.js 或运行前端构建命令
- **THEN** 控制台仍可加载并使用，不依赖外部 CDN 或第三方运行时服务

### Requirement: Document and indexing workspace
控制台 SHALL 允许用户选择 PDF、Markdown 或 TXT 文件上传，显示上传结果和索引任务状态，并支持刷新文档列表。

#### Scenario: Upload and index a document
- **WHEN** 用户在控制台选择支持的文件并提交上传
- **THEN** 控制台调用文档上传接口、展示返回的任务标识，并持续查询任务直到 succeeded、failed 或 cancelled

#### Scenario: Show document state
- **WHEN** 用户打开或刷新文档工作区
- **THEN** 控制台展示文件名、文档标识、块数量、索引状态和更新时间；接口错误以可读提示显示

### Requirement: Search workspace
控制台 SHALL 提供非空问题搜索入口，并展示每条结果的相关性分数、文本片段和来源元数据。

#### Scenario: Search the knowledge base
- **WHEN** 用户提交搜索词
- **THEN** 控制台调用 `/search` 并按接口返回顺序显示结果、来源和检索耗时

#### Scenario: Search with no results
- **WHEN** 搜索没有命中结果
- **THEN** 控制台显示明确的无结果状态，不伪造答案或来源

### Requirement: Grounded streaming chat workspace
控制台 SHALL 支持提交问答问题、显示流式生成过程、来源引用和无依据拒答结果。

#### Scenario: Receive a streamed answer
- **WHEN** 用户提交问题且后端返回 SSE 流
- **THEN** 控制台增量拼接 token 事件，在流结束后显示完整回答、来源和工作流阶段

#### Scenario: Display grounded fallback
- **WHEN** 后端返回信息不足的 fallback 或错误事件
- **THEN** 控制台显示当前知识库中没有足够信息或可读错误，不把 fallback 当作有依据的答案

#### Scenario: Stop a pending request
- **WHEN** 用户在问答流仍未结束时点击停止
- **THEN** 控制台取消当前浏览器请求并保留已收到的文本，同时将状态标记为已停止
