# LLM Starter

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.139+-009688" alt="FastAPI" />
  <img src="https://img.shields.io/badge/LangChain-1.3+-green" alt="LangChain" />
  <img src="https://img.shields.io/badge/LangGraph-1.2+-yellow" alt="LangGraph" />
  <img src="https://img.shields.io/badge/SQLite-3+-003B57" alt="SQLite" />
  <img src="https://img.shields.io/badge/Docker-ready-2496ED" alt="Docker" />
</p>

<p align="center">
  <strong>一个基于 Python + FastAPI + LangChain + LangGraph 的 LLM 应用开发脚手架</strong>
  <br/>
  集成 Chat、RAG、Agent、Skill、MCP 五大核心能力
</p>

## 目录

- [项目特性](#项目特性)
- [技术栈](#技术栈)
- [架构设计](#架构设计)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [API 接口](#api-接口)
- [核心功能](#核心功能)
- [Docker 部署](#docker-部署)
- [开发计划](#开发计划)

---

## 项目特性

- 💬 **智能对话** - 支持同步/流式对话，多轮上下文记忆
- 📚 **RAG 知识库** - 混合检索（向量 + BM25），重排序检索，引用来源溯源
- 🤖 **Agent 智能体** - 基于 LangGraph 的工具调用、任务规划
- 🧠 **Skill 技能系统** - SKILL.md 文件定义，渐进式披露，按需加载技能   
- 🔌 **MCP 远程工具** - 通过 MCP 协议调用远程服务工具，动态扩展 Agent 能力
- 🔌 **多模型支持** - 阿里云/豆包等主流 LLM，启动时可切换
- 🛡️ **生产就绪** - CORS、认证、速率限制、日志、异常处理
- 📊 **链路追踪** - 集成 LangSmith，全链路可观测
- 🐳 **容器化** - Docker + docker-compose 一键部署

---

## 技术栈

| 分类 | 技术 | 版本 | 说明 |
|------|------|------|------|
| Web 框架 | FastAPI | 0.139+ | 高性能异步框架 |
| LLM 框架 | LangChain | 1.3+ | LLM 应用开发框架 |
| Agent 框架 | LangGraph | 1.2+ | 状态机式 Agent |
| 向量数据库 | Chroma | 1.5+ | 轻量级向量存储 |
| 嵌入模型 | bge-reranker-v2-m3 | - | 开源重排序模型 |
| 数据库 | SQLite | - | 会话持久化 |
| ORM | SQLAlchemy | 2.0+ | 数据访问 |
| 配置管理 | Pydantic Settings | 2.14+ | 类型安全配置 |
| 链路追踪 | LangSmith | 0.9+ | LLM 应用可观测性 |
| 部署 | Docker | - | 容器化部署 |

---

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                      API 层 (api/)                      │
│  /chat  /rag  /agent  /session  /health                │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Service 层 (application/service/)      │
│  ChatService  │  RAGService  │  AgentService            │
─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                Adapter 层 (infra/adapter/)              │
│  OpenAIAdapter  │  ChromaAdapter  │  McpAdapter         │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│               Infrastructure 层 (infra/)                │
│  文档处理  │ 检索器  │ 存储  │ Prompt  │ 外部服务  │ 配置 │
─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                 Skill 层 (application/skills/)          │
│  SKILL.md 定义  │  渐进式披露  │  动态加载               │
└─────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
llm-starter/
├── api/                              # API 层
│   ├── main.py                       # FastAPI 入口
│   ├── middleware/                   # 中间件
│   │   ├── auth.py                   # 认证中间件
│   │   └── rate_limit.py            # 速率限制中间件
│   ├── routers/                      # 路由
│   │   ├── chat.py                   # 对话接口
│   │   ├── rag.py                    # RAG 接口
│   │   ├── agent.py                  # Agent 接口
│   │   └── session.py                # 会话接口
│   ── schemas/                      # 请求/响应模型
│       ├── chat.py
│       ├── rag.py
│       └── agent.py
├── application/                      # 业务层
│   ├── agents/                       # Agent 实现
│   │   ├── flow_agent.py             # 带意图识别的流程 Agent
│   │   └── simple_agent.py           # 简单工具调用 Agent
│   ├── ports/                        # 端口（接口定义）
│   │   ├── llm_client_port.py        # LLM 客户端端口
│   │   ├── document_port.py          # 文档处理端口
│   │   ├── prompt_port.py            # Prompt 端口
│   │   ├── retriever_port.py         # 检索器端口
│   │   └── vector_store_port.py      # 向量存储端口
│   ├── service/                      # 服务
│   │   ├── chat_service.py           # 对话服务
│   │   ├── rag_service.py            # RAG 服务
│   │   └── agent_service.py          # Agent 服务
│   ├── skills/                       # Skill 技能系统
│   │   ├── base_skill.py             # Skill 基类 + SkillManager
│   │   ├── SKILL.md                  # 技能定义规范
│   │   ├── weather/                  # 天气技能目录
│   │   │   └── SKILL.md              # 天气技能定义
│   │   └── weather_skill.py          # 天气技能实现
│   ├── tools/                        # 工具实现
│   │   ├── calculator.py             # 计算器
│   │   ├── time_tool.py              # 时间查询
│   │   └── weather.py                # 天气查询
│   ├── middleware/                    # 中间件
│   │   ├── custom_middleware.py       # 自定义中间件
│   │   └── wrap_middleware.py         # 包装中间件
│   └── dependency_injection.py       # 依赖注入容器
├── infra/                            # 基础设施层
│   ├── adapter/                      # 适配器
│   │   ├── openai_adapter.py         # LLM 适配器
│   │   ├── chroma_adapter.py         # Chroma 适配器
│   │   └── mcp_adapter.py            # MCP 远程工具适配器
│   ├── document/                     # 文档处理
│   │   ├── loader.py                 # 文档加载
│   │   ├── cleaner.py                # 文档清洗
│   │   ├── splitter.py               # 文档切分
│   │   └── formatter.py              # 文档格式化
│   ├── retriever/                    # 检索器
│   │   └── retriever.py              # 混合/重排序检索
│   ├── storage/                      # 存储
│   │   ├── database.py               # 数据库连接
│   │   ├── models.py                 # 数据模型
│   │   └── session_storage.py        # 会话存储
│   ├── prompt/                       # Prompt 管理
│   │   ├── prompt_manager.py
│   │   └── template/                  # Prompt 模板
│   ├── external/                     # 外部服务
│   │   └── weather_client.py         # 天气 API 客户端
│   ├── utils/                        # 工具类
│   │   ├── log_util.py
│   │   ├── file_util.py
│   │   └── str_util.py
│   ├── settings.py                   # 配置管理
│   └── exceptions.py                 # 自定义异常
├── docs/                             # 知识库文档
├── chroma_db/                        # 向量数据库存储
├── sqlite_db/                       # SQLite 数据库存储
├── logs/                             # 日志目录
├── .env                              # 环境变量
├── requirements.txt                  # 依赖
├── Dockerfile                        # Docker 配置
├── docker-compose.yml                # Docker Compose 配置
└── README.md
```

---

## 快速开始

### 环境要求

- Python 3.10+
- pip
- (可选) Docker Desktop

### 1. 克隆项目

```bash
git clone https://github.com/your-username/llm-starter.git
cd llm-starter
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制模板（如果提供）
# 或直接编辑 .env 文件
```

在 `.env` 文件中配置：

```env
# 选择默认模型提供商
DEFAULT_LLM_PROVIDER=aliyun

# 阿里云配置
ALIYUN_API_KEY=your-api-key
ALIYUN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ALIYUN_CHAT_MODEL=qwen3.7-plus
ALIYUN_EMBEDDING_MODEL=text-embedding-v4

# 豆包配置（可选）
DOUBAO_API_KEY=your-api-key
DOUBAO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_CHAT_MODEL=doubao-seed-2-1-pro-260628
DOUBAO_EMBEDDING_MODEL=text-embedding-v4

# LangSmith 配置（可选，用于链路追踪）
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=my-llm-app
```

### 5. 启动服务

```bash
# 开发模式（支持热重载）
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 6. 访问服务

- API 文档（Swagger）：http://localhost:8000/docs
- API 文档（ReDoc）：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/health

---

## 配置说明

### 模型切换

修改 `.env` 中的 `DEFAULT_LLM_PROVIDER`：

```env
# 使用阿里云
DEFAULT_LLM_PROVIDER=aliyun

# 使用豆包
DEFAULT_LLM_PROVIDER=doubao
```

### RAG 参数调优

在 `infra/settings.py` 中调整：

```python
# 检索参数
RAG_VECTOR_TOP_K: int = 10           # 向量检索返回数量
RAG_BM25_TOP_K: int = 10              # BM25 检索返回数量
RAG_RERANK_TOP_K: int = 3             # 重排序返回数量
RAG_HYBRID_WEIGHTS: List[float] = [0.6, 0.4]  # 混合权重
```

### 速率限制

```python
RATE_LIMIT_MAX_REQUESTS: int = 60      # 最大请求数
RATE_LIMIT_WINDOW_SECONDS: int = 60    # 时间窗口（秒）
```

---

## API 接口

### 对话接口

#### 同步对话

```http
POST /chat/base
Content-Type: application/json

{
    "message": "你好，请介绍一下自己",
    "system_content": "你是一个专业的AI助手",
    "session_id": "optional-session-id"
}
```

**响应**：
```json
{
    "content": "你好！我是一个AI助手...",
    "finish_reason": "stop",
    "token_usage": {
        "prompt_tokens": 20,
        "completion_tokens": 50,
        "total_tokens": 70
    }
}
```

#### 流式对话

```http
POST /chat/stream
Content-Type: application/json

{
    "message": "写一首关于春天的诗"
}
```

### RAG 接口

#### 上传文档到知识库

```http
POST /rag/documents
Content-Type: multipart/form-data

# 选择文件上传（支持 .md, .txt, .pdf, .docx）
```

#### RAG 查询

```http
POST /rag/query
Content-Type: application/json

{
    "question": "文档中提到的核心功能有哪些？"
}
```

**响应**：
```json
{
    "content": "根据文档内容，核心功能包括...",
    "sources": [
        {
            "source": "docs.md",
            "file_path": "/path/to/docs.md",
            "page": 1
        }
    ]
}
```

### Agent 接口

```http
POST /agent/run
Content-Type: application/json

{
    "question": "帮我计算123*456，然后查询今天天气",
    "thread_id": "optional-thread-id"
}
```

### 会话接口

#### 创建会话

```http
POST /sessions
Content-Type: application/json

{
    "session_type": "chat",
    "title": "新会话"
}
```

#### 获取会话列表

```http
GET /sessions?session_type=chat&limit=50
```

#### 获取会话消息历史

```http
GET /sessions/{session_id}/messages
```

---

## 核心功能

### 1. 智能对话

支持同步和流式两种对话模式，通过 `session_id` 实现多轮上下文记忆：

```python
# 第一次对话
POST /chat/base
{"message": "我叫张三"}

# 继续对话（LLM 能记住上下文）
POST /chat/base
{"message": "我刚才说我叫什么名字？", "session_id": "xxx"}
# 响应: "你刚才说你叫张三"
```

### 2. RAG 知识库

文档入库流程：

```
用户上传文件 → 文档加载 → 内容清洗 → 文本切分 → 向量化 → 存储到 Chroma
```

查询流程：

```
用户问题 → 向量检索 + BM25 检索 → 混合排序 → 重排序（可选）→ LLM 生成 → 返回引用来源
```

### 3. Agent 智能体

基于 LangGraph 构建的 Agent，支持：

- **工具调用**：计算器、天气查询、时间查询
- **任务规划**：自动拆解复杂任务
- **对话记忆**：基于线程的多轮对话
- **路由决策**：根据问题选择合适的工具

### 4. Skill 技能系统

采用 SKILL.md 文件定义方式（知识驱动型），支持渐进式披露：

- **启动时**：只加载所有 SKILL.md 的 YAML frontmatter（name + description），约几百 token
- **匹配后**：按需加载完整 SKILL.md 内容（执行步骤、注意事项等）
- **执行时**：调用具体 Python 实现

目录结构：
```
skills/
└── weather/
    ├── SKILL.md           # 技能定义（YAML frontmatter + Markdown）
    └── weather_skill.py   # 技能实现（继承 Skill 基类）
```

### 5. MCP 远程工具

通过 MCP（Model Context Protocol）协议调用远程服务工具：

- **动态扩展**：不修改代码，通过配置新增 MCP 服务即可扩展 Agent 能力
- **异步管理**：支持异步上下文管理，正确管理连接生命周期
- **降级处理**：MCP 服务不可用时自动降级为本地工具

---

## Docker 部署

### 1. 构建镜像

```bash
docker-compose build
```

### 2. 启动服务

```bash
docker-compose up -d
```

### 3. 查看日志

```bash
docker-compose logs -f
```

### 4. 停止服务

```bash
docker-compose down
```

### 数据持久化

以下目录会自动挂载到本地：

| 容器路径 | 本地路径 | 说明 |
|---------|---------|------|
| `/app/chroma_db` | `./chroma_db` | 向量数据库 |
| `/app/sqlite_db` | `./sqlite_db` | 会话数据库 |
| `/app/logs` | `./logs` | 日志文件 |
| `/app/docs` | `./docs` | 知识库文档 |

---

## 开发计划

- [x] 基础架构搭建
- [x] 对话服务（同步/流式）
- [x] RAG 知识库（混合检索）
- [x] Agent 智能体（LangGraph）
- [x] 多模型支持（阿里云/豆包）
- [x] 会话持久化（SQLite）
- [x] 引用来源溯源
- [x] Docker 部署
- [x] LangSmith 链路追踪
- [x] Skill 技能系统（SKILL.md 定义，渐进式披露）
- [x] MCP 远程工具支持
- [ ] 问题改写优化
- [ ] 重排序检索器
- [ ] 单元测试
- [ ] 前端界面

---

## 常见问题

### Q: 如何切换 LLM 模型？

修改 `.env` 文件中的 `DEFAULT_LLM_PROVIDER` 为 `aliyun` 或 `doubao`，重启服务即可。

### Q: RAG 支持哪些文件格式？

支持 `.md`, `.txt`, `.pdf`, `.docx`, `.doc` 格式。

### Q: 如何启用 LangSmith 追踪？

在 `.env` 中配置 `LANGSMITH_API_KEY` 并设置 `LANGSMITH_TRACING=true`。

### Q: 数据存在哪里？

- 向量数据库：`./chroma_db/`
- 会话数据库：`./sqlite_db/llm_app.db`
- 日志：`./logs/`

---

## License

MIT License

---

## 联系方式

如有问题或建议，请提交 Issue。
