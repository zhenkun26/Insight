## Why

气象业务资料中可能包含扫描版或无文本层的 PDF，当前解析器会把这类页面当成空内容，导致后续检索和问答无法命中。需要提供一个明确 opt-in 的 OCR 路径，同时保持默认安装轻量、文本型 PDF 行为稳定，并在运行环境缺少 OCR 工具时给出可诊断的失败信息。

## What Changes

- 增加通过环境变量开启的 PDF OCR 解析能力，默认关闭。
- 对文本层为空的 PDF 页面调用本地 Poppler `pdftoppm` 和 Tesseract，将 OCR 文本保留原页码元数据。
- 支持配置 OCR 语言和单页/任务超时，清理所有临时文件。
- OCR 工具不可用、超时或返回错误时，返回结构化的可诊断错误，不伪造索引成功。
- 在健康检查、README、`.env.example` 和测试中说明 OCR 状态、安装方式与限制。

## Capabilities

### New Capabilities

- `pdf-ocr`: 为无文本层 PDF 提供可选的本地 OCR 解析与明确降级行为。

### Modified Capabilities

<!-- No existing requirement needs replacement; OCR is an opt-in parser capability with its own contract. -->

## Impact

- Affected code: PDF parser, ingestion settings/service, health response, API error mapping, tests and documentation.
- Runtime: 默认不需要新 Python 包；启用 OCR 时需要系统安装 Poppler 和 Tesseract，且模型语言包需由用户自行准备。
- Compatibility: `OCR_ENABLED=false` 保持现有 PDF、Markdown 和 TXT 行为；OCR 只补充空文本页。
- Operational risk: OCR 可能消耗 CPU、磁盘和时间，因此必须有超时、临时目录清理和明确失败状态。
