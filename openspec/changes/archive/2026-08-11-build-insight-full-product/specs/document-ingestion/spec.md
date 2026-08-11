## MODIFIED Requirements

### Requirement: Supported document ingestion
系统 SHALL 接受 PDF、Markdown 和 TXT 文件，并为每个成功导入的文件生成稳定的文档标识；导入记录 SHALL 保存内容指纹、解析器版本和索引配置版本。

#### Scenario: Import supported file
- **WHEN** 用户上传扩展名为 PDF、MD、MARKDOWN 或 TXT 的有效文件
- **THEN** 系统解析正文，创建文档记录，并返回文档标识、文件名和索引状态

#### Scenario: Reject unsupported file
- **WHEN** 用户上传不支持的文件类型
- **THEN** 系统返回明确的 4xx 错误，并且不创建部分文档记录

### Requirement: Chunk metadata preservation
系统 SHALL 按标题、段落和配置的最大字符数切分文本，并为每个文本块保留文档标识、文件名、页码（可用时）、章节标题和唯一文本块标识；文本块 SHALL 关联索引任务和索引版本。

#### Scenario: Split a document
- **WHEN** 文档包含多个标题和超过最大长度的段落
- **THEN** 系统生成不超过配置上限的文本块，并保持标题和相邻段落的可追溯元数据

### Requirement: Duplicate and lifecycle handling
系统 SHALL 使用文件内容指纹检测重复文档，并支持列出文档、删除指定文档和重新建立索引；生命周期操作 SHALL 对索引任务保持可追踪且不得留下孤立的检索内容。

#### Scenario: Upload duplicate
- **WHEN** 用户再次上传内容指纹相同的文档
- **THEN** 系统返回已存在文档的信息，不重复创建索引内容

#### Scenario: Delete document
- **WHEN** 用户删除已存在文档
- **THEN** 系统删除文档目录、文本块及其检索索引内容，后续搜索不得返回该文档

#### Scenario: Recover from failed indexing
- **WHEN** 文档索引任务失败
- **THEN** 文档保持可识别的 failed 状态，失败内容不得参与搜索，并可通过重试任务恢复
