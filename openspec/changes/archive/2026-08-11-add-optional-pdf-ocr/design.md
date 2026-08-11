## Context

当前 `pypdf` 负责 PDF 文本层抽取，解析结果随后进入通用切分和索引服务。项目默认环境需要保持轻量，CI 不应依赖 OCR 二进制；OCR 只为扫描 PDF 提供 opt-in 扩展。

## Goals / Non-Goals

**Goals:**

- 在不新增默认 Python 依赖的前提下支持本地扫描 PDF OCR。
- 只对空文本页 OCR，保留原有文本页的内容、页码和切分行为。
- 将外部进程超时、缺失和非零退出统一成可诊断的解析错误。
- 通过临时目录隔离每次 PDF 转图片和 OCR 产物，并确保异常路径清理。

**Non-Goals:**

- 不在 Docker 镜像中强制安装 Poppler、Tesseract 或语言包。
- 不支持图片、Office 文档或远程 OCR API。
- 不承诺复杂表格、手写文字或版面结构的高质量识别。

## Decisions

### Use optional system tools

使用系统已有的 PDF 转图片工具和 Tesseract 命令行，通过 Python `subprocess.run` 传递参数列表，不引入重量级 Python OCR 依赖。这样默认安装和 CI 不变，用户可以按本机平台自行安装 OCR 运行时。

### OCR only blank pages

先执行现有文本抽取；只有页面清洗后为空才进入 OCR。OCR 结果按页顺序回填到对应 `ParsedPage`，避免重复内容和破坏已有可检索正文。

### Bounded external execution

每个 OCR 页面调用使用 `timeout`，语言和超时来自配置；命令不存在、超时、非零退出或无输出都转换为明确的 OCR 错误。输入 PDF 和生成图片放在 `TemporaryDirectory` 中，依赖上下文管理器自动清理。

### Preserve asynchronous task semantics

不改变后台索引任务协议。解析错误沿现有任务异常链路进入 failed/index_failed 状态；同步调用由 API 映射为明确 4xx/5xx 错误，不能继续调用索引回调。

## Risks / Trade-offs

- [Risk] OCR 工具和语言包在不同操作系统上的命令行为不同 → 启动/解析前探测工具，错误信息包含安装提示，文档记录 macOS/Linux/Windows 的准备方式。
- [Risk] 大型 PDF 产生大量临时 PNG → 单文档使用临时目录，逐页 OCR 并及时删除页图；超时终止当前命令并由上下文管理器清理目录。
- [Risk] OCR 文本质量低于文本层抽取 → 默认关闭、只用于空文本页，并在文档元数据/README 中明确 OCR 是辅助能力。
- [Risk] 外部工具调用难以在 CI 真实验证 → 单元测试 mock 工具探测和 subprocess，另提供本机探测命令作为运行时冒烟证据。

## Migration Plan

1. 增加 OCR 配置字段、解析适配器和 API/健康状态映射，默认 `OCR_ENABLED=false`。
2. 在本地无 OCR 工具的 CI 环境运行默认路径与 mock 失败路径测试。
3. 用户安装 Poppler/Tesseract 后设置环境变量并重新启动应用即可启用，无需数据库或索引迁移；启用后建议重建已有扫描资料索引。
4. 回滚时关闭配置或移除 OCR 适配器，不影响既有文本层文档。
