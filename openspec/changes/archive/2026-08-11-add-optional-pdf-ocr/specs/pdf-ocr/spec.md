## Purpose

为无文本层的扫描版气象 PDF 提供可控的本地 OCR 解析路径，使页面仍能进入切分、索引和来源引用链路，同时不改变默认轻量运行模式。

## ADDED Requirements

### Requirement: Opt-in scanned PDF OCR
系统 SHALL 仅在 OCR 配置显式开启时对 PDF 页面执行本地 OCR；配置关闭或未设置时，现有 PDF 文本层解析行为 SHALL 保持不变。

#### Scenario: Keep default parsing lightweight
- **WHEN** `OCR_ENABLED` 未设置或为 false，用户导入普通 PDF、Markdown 或 TXT
- **THEN** 系统不启动 OCR 工具，按现有解析流程返回文本和页码元数据

#### Scenario: OCR an empty PDF text page
- **WHEN** `OCR_ENABLED=true` 且 PDF 页面没有可提取文本
- **THEN** 系统使用配置的 OCR 语言识别页面，将识别文本作为该页正文返回，并保留对应页码

#### Scenario: Preserve native text pages
- **WHEN** 同一个 PDF 同时包含文本层页面和扫描页面
- **THEN** 系统优先使用文本层内容，仅对空文本页面执行 OCR，不重复覆盖已有正文

### Requirement: OCR runtime configuration
系统 SHALL 支持配置 OCR 语言、单页执行超时和临时工作目录策略，默认值 SHALL 适合本地演示且不要求用户安装 OCR 工具。

#### Scenario: Configure OCR language and timeout
- **WHEN** 用户设置 OCR 语言和超时环境变量并开启 OCR
- **THEN** OCR 调用使用这些配置，超时值必须为正数

#### Scenario: Reject invalid OCR timeout
- **WHEN** OCR 开启且超时配置为零或负数
- **THEN** 应用启动或文档解析返回明确的配置错误，不执行无超时 OCR 调用

### Requirement: Explicit OCR failure handling
系统 SHALL 在 OCR 工具缺失、执行超时或识别命令失败时返回可诊断错误，并 SHALL 清理本次解析创建的临时文件；不得将失败文档标记为成功索引。

#### Scenario: OCR tools unavailable
- **WHEN** OCR 开启但本地 OCR 运行时缺少必需工具
- **THEN** 文档任务失败并包含 `ocr_unavailable` 语义的错误信息，文档不会进入 indexed 状态

#### Scenario: OCR command timeout
- **WHEN** 单页 OCR 超过配置的超时时间
- **THEN** 当前解析失败并包含超时语义，临时目录在错误返回前后均不可继续累积本次文件
