## Purpose

让本地知识库能够按来源和标签组织资料，并在搜索、索引版本和文档生命周期之间保持一致的可追溯关系。

## ADDED Requirements

### Requirement: Document metadata management

系统 SHALL 支持为文档保存来源、标签和描述等可选元数据，并在文档列表、搜索结果和引用来源中返回这些字段。

#### Scenario: Update document metadata
- **WHEN** 客户端为已存在文档设置来源或标签
- **THEN** 系统保存元数据且不改变文档内容指纹与文本块标识

### Requirement: Metadata-filtered retrieval

系统 SHALL 支持按文档标识、来源和标签过滤搜索候选，过滤条件必须同时作用于关键词和向量召回结果。

#### Scenario: Search within a tagged subset
- **WHEN** 客户端提交带标签过滤条件的搜索请求
- **THEN** 返回结果只包含满足条件的文档，且无结果时使用正常的空结果语义

### Requirement: Index version visibility

系统 SHALL 为文档记录当前索引版本、Embedding 模型标识和索引状态，并在模型或分块配置变化后标记需要重建。

#### Scenario: Embedding model changed
- **WHEN** 当前 Embedding 模型与文档索引记录不一致
- **THEN** 文档状态明确表示需要重建，搜索不得把旧版本误报为当前版本结果
