# Resume Optimization Agent

一个可通过 Docker 运行的全栈应用：用户输入或上传简历、输入目标 JD，系统先分析匹配情况，再在用户确认后生成优化后的简历，并支持导出结果。

## 技术栈

- 后端：FastAPI + Pydantic + `uv`
- 前端：Vue 3 + Vite
- 部署：Docker / Docker Compose
- LLM：DeepSeek（通过环境变量配置 API Key）

## 功能

- 粘贴简历文本
- 上传 `TXT` / `PDF` 简历并解析为文本
- 输入目标岗位 JD
- 分析并展示：
  - 匹配亮点
  - 主要缺口
  - 优化建议
  - 匹配度评分
- 用户确认后生成优化后的简历
- 页面内查看优化结果
- 导出为 `.md` 或 `.txt`

## 环境变量

可先复制 `.env.example` 为 `.env`，至少包含：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
APP_HOST=0.0.0.0
APP_PORT=8000
MAX_UPLOAD_SIZE_MB=5
```

说明：

- `DEEPSEEK_API_KEY` 必填
- 不要把 API Key 硬编码到代码中
- `DEEPSEEK_BASE_URL` 和 `DEEPSEEK_MODEL` 提供默认值，可按需覆盖

## 本地开发

### 后端

```bash
uv sync
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

开发模式下：

- 后端默认：`http://localhost:8000`
- 前端默认：`http://localhost:5173`

## Docker 构建与启动

### 方式一：docker compose

```bash
docker compose up --build
```

启动后访问：

```text
http://localhost:8000
```

### 方式二：docker build

```bash
docker build -t resume-optimization-agent .
docker run --rm -p 8000:8000 --env-file .env resume-optimization-agent
```

## 基本验收流程

1. 启动服务后打开 `http://localhost:8000`
2. 通过以下任一方式提供简历：
   - 直接粘贴简历文本
   - 上传 `TXT` 或 `PDF`
3. 在 JD 输入框中粘贴目标职位描述
4. 点击 `Analyze Match`
5. 检查页面展示的：
   - `Match Score`
   - `Strengths`
   - `Gaps`
   - `Suggestions`
6. 点击 `Generate Optimized Resume`
7. 查看优化后的简历与改动摘要
8. 点击导出按钮，下载 `.md` 或 `.txt`

## API 概览

- `GET /healthz`
- `POST /api/v1/parse-resume`
  - `multipart/form-data`
  - 字段：`file`
- `POST /api/v1/analyze`
  - JSON：`resume_text`, `job_description`
- `POST /api/v1/optimize`
  - JSON：`resume_text`, `job_description`, `analysis_context`

## 测试

```bash
uv run pytest
```

## 常见问题

### 1. 页面提示缺少 API Key

确认 `.env` 中配置了：

```env
DEEPSEEK_API_KEY=...
```

### 2. PDF 上传失败

- 检查文件是否为有效 PDF
- 某些扫描版 PDF 无法直接提取文本，建议先转为可复制文本或使用 TXT

### 3. 模型返回解析错误

系统要求模型以结构化 JSON 返回分析结果。如果出现偶发解析失败，请重试；服务端会返回可读错误信息。

## 项目结构

```text
.
├── backend/
│   └── app/
├── frontend/
│   └── src/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```
