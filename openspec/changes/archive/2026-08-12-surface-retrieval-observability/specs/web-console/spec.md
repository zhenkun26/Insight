## MODIFIED Requirements

### Requirement: Search workspace
控制台 SHALL 提供非空问题搜索入口，并展示每条结果的相关性分数、文本片段、来源元数据和本次检索的阶段状态与耗时。

#### Scenario: Search the knowledge base
- **WHEN** 用户提交搜索词
- **THEN** 控制台调用 `/search` 并按接口返回顺序显示结果、来源、检索耗时和阶段信息

#### Scenario: Search with no results
- **WHEN** 搜索没有命中结果
- **THEN** 控制台显示明确的无结果状态，不伪造答案或来源，但仍可显示本次检索阶段状态
