# http-api Specification

## Purpose

通过稳定、可测试的 HTTP 接口提供文档管理、搜索、问答和服务健康状态，使本地应用能够被 CLI、Web UI 或其他客户端复用。

## Requirements

### Requirement: Document management API
系统 SHALL 提供文档上传、列表、删除和重建索引接口，并对非法文件、未知文档和索引失败返回结构化错误。

#### Scenario: Upload document through API
- **WHEN** 客户端向 `POST /documents/upload` 提交有效文档
- **THEN** API 返回成功状态、文档标识、文件名、块数量和索引状态

#### Scenario: List and delete documents
- **WHEN** 客户端请求 `GET /documents` 或 `DELETE /documents/{document_id}`
- **THEN** API 返回文档状态或删除结果，并使用一致的 JSON 错误结构处理未知标识

### Requirement: Search and chat API
系统 SHALL 提供 `POST /search`、`POST /chat` 和 `POST /chat/stream`，响应至少包含 query、answer（问答时）、sources、retrieval_results 和 latency_ms。

#### Scenario: Search request
- **WHEN** 客户端提交非空 query 到 `/search`
- **THEN** API 返回按相关性排序的检索结果及来源元数据

#### Scenario: Chat request
- **WHEN** 客户端提交非空 query 到 `/chat`
- **THEN** API 返回受上下文约束的 answer、来源、检索结果、原始 query 和毫秒级延迟

### Requirement: Health endpoint
系统 SHALL 提供 `GET /health`，返回应用状态以及可配置的依赖检查结果，不得因测试环境没有真实模型而伪报依赖健康。

#### Scenario: Health check
- **WHEN** 客户端请求 `/health`
- **THEN** API 返回服务状态、版本或运行信息，以及依赖状态字段
