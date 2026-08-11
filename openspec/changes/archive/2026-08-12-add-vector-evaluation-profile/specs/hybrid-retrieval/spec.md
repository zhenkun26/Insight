## ADDED Requirements

### Requirement: Explicit retrieval mode selection
系统 SHALL 支持显式选择 `bm25`、`vector` 或 `hybrid` 检索模式；`bm25` SHALL 只执行关键词召回，`vector` SHALL 只执行向量召回，`hybrid` SHALL 执行两路召回并按既有融合规则合并结果。

#### Scenario: BM25 mode preserves the offline path
- **WHEN** 调用方选择 `bm25` 模式
- **THEN** 系统不调用 Embedding 或向量存储，并返回与现有关键词路径一致的结果和状态

#### Scenario: Vector-only mode disables keyword retrieval
- **WHEN** 调用方选择 `vector` 模式且向量依赖可用
- **THEN** 系统不执行关键词召回，只返回向量候选及其向量分数

#### Scenario: Hybrid mode combines both sources
- **WHEN** 调用方选择 `hybrid` 模式且两路依赖可用
- **THEN** 系统执行关键词和向量召回，并使用既有 RRF 去重、排序、阈值和分页行为

#### Scenario: Invalid mode is rejected
- **WHEN** 调用方提供未支持的检索模式
- **THEN** 系统快速返回配置错误，不执行任何外部模型或向量存储调用
