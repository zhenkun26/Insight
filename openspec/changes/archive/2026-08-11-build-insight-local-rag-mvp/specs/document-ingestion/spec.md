## Purpose

让本地气象资料能够被稳定解析、切分、追踪和重新索引，同时保留回答所需的文件、页码、章节与文本块来源信息。

## ADDED Requirements

### Requirement: Supported document ingestion
系统 SHALL 接受 PDF、Markdown 和 TXT 文件，并为每个成功导入的文件生成稳定的文档标识。

#### Scenario: Import supported file
- **WHEN** 用户上传扩展名为 PDF、MD、MARKDOWN 或 TXT 的有效文件
- **THEN** 系统解析正文，创建文档记录，并返回文档标识、文件名和索引状态

#### Scenario: Reject unsupported file
- **WHEN** 用户上传不支持的文件类型
- **THEN** 系统返回明确的 4xx 错误，并且不创建部分文档记录

### Requirement: Chunk metadata preservation
系统 SHALL 按标题、段落和配置的最大字符数切分文本，并为每个文本块保留文档标识、文件名、页码（可用时）、章节标题和唯一文本块标识。

#### Scenario: Split a document
- **WHEN** 文档包含多个标题和超过最大长度的段落
- **THEN** 系统生成不超过配置上限的文本块，并保持标题和相邻段落的可追溯元数据

### Requirement: Duplicate and lifecycle handling
系统 SHALL 使用文件内容指纹检测重复文档，并支持列出文档、删除指定文档和重新建立索引。

#### Scenario: Upload duplicate
- **WHEN** 用户再次上传内容指纹相同的文档
- **THEN** 系统返回已存在文档的信息，不重复创建索引内容

#### Scenario: Delete document
- **WHEN** 用户删除已存在文档
- **THEN** 系统删除文档目录、文本块及其检索索引内容，后续搜索不得返回该文档
