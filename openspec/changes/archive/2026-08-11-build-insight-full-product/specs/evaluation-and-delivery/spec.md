## MODIFIED Requirements

### Requirement: Deterministic automated tests
项目 SHALL 提供覆盖解析、切分、元数据、BM25、向量接口、混合融合、拒答、引用、健康检查、上传和 mock 问答的自动化测试，并覆盖任务生命周期、过滤、会话约束和流式事件。

#### Scenario: Run tests without external services
- **WHEN** CI 执行项目测试且 Ollama、Milvus 和外部 API 均不可用
- **THEN** 测试仍可完成核心逻辑验证，外部连接由 mock、fake 或内存实现替代

### Requirement: Reproducible retrieval evaluation
项目 SHALL 提供包含 10 至 20 条问题及期望命中内容的评估数据和脚本，计算至少一种命中率指标与平均响应时间，并记录模型、参数和测试日期；评估 SHALL 另外报告拒答样例和阶段耗时。

#### Scenario: Run evaluation
- **WHEN** 用户按 README 指令运行评估脚本
- **THEN** 脚本输出由实际运行计算得到的 Recall@K、MRR 或命中率、平均延迟和运行配置，不生成硬编码指标

### Requirement: Local delivery documentation
项目 SHALL 提供 README、`.env.example`、Dockerfile、Docker Compose 和 GitHub Actions CI，文档必须说明模型准备、Milvus 启动、导入、问答、测试、评估和已知限制；部署配置 SHALL 持久化目录并提供可验证的健康检查。

#### Scenario: Run CI
- **WHEN** GitHub Actions 在干净环境中运行
- **THEN** CI 安装依赖、执行格式检查、导入检查和 pytest，且不要求真实模型或向量数据库服务

#### Scenario: Persist local runtime state
- **WHEN** 用户重启 Docker Compose 服务
- **THEN** 文档目录、任务记录和向量数据从挂载目录恢复，不要求重新上传所有资料
