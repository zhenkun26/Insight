## ADDED Requirements

### Requirement: Serve the local web console
系统 SHALL 在与 JSON API 相同的 FastAPI 应用中提供根路径控制台及其静态资源，静态资源缺失时 SHALL 返回清晰的服务端错误而不是静默成功。

#### Scenario: Serve console entry point
- **WHEN** 客户端请求 `GET /`
- **THEN** API 返回 HTML 控制台页面并使用 200 状态码

#### Scenario: Serve console assets
- **WHEN** 浏览器请求控制台引用的 CSS 或 JavaScript 资源
- **THEN** API 返回对应静态内容和可识别的媒体类型，且不需要额外认证或外部服务

#### Scenario: Preserve API routes
- **WHEN** 客户端请求已有的 `/health`、`/documents`、`/search` 或 `/chat` 路由
- **THEN** API 继续按既有 JSON 或 SSE 契约响应，不被根路径静态资源处理器拦截
