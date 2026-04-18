# Resume Optimization Agent

一个基于 DeepSeek 的简历优化应用。用户输入或上传简历、输入目标岗位 JD 后，系统会先分析匹配情况，再按简历各个 section 逐段判断是否需要优化，最后重组生成一份可直接查看和导出的中文简历成品。

## 功能简介

- 支持粘贴简历文本
- 支持上传 `TXT` / `PDF` 简历
- 输入目标岗位描述（JD）
- 自动识别简历 section
- 分析每个 section 是否需要优化
- 生成：
  - 匹配亮点
  - 主要缺口
  - 优化建议
  - section 级诊断结果
- 仅针对需要优化的部分进行改写
- 重组输出完整简历成品
- 支持页面预览与导出 `.md` / `.txt`

## 目录结构

```text
.
├── backend/
│   └── app/
│       ├── api/          # FastAPI 路由
│       ├── core/         # 配置
│       ├── prompts/      # LLM 提示词
│       ├── schemas/      # Pydantic 数据结构
│       └── services/     # 简历分析、优化、文件解析等服务
├── frontend/
│   ├── src/              # Vue 页面与样式
│   ├── package.json
│   └── vite.config.js
├── tests/                # API 测试
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## 启动方式

### 1. 配置环境变量

先复制示例文件：

```bash
cp .env.example .env
```

然后在 `.env` 中至少配置：

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
- API Key 必须通过环境变量配置，不能硬编码

### 2. 使用 Docker Compose 启动

```bash
docker compose up -d
```

启动后访问：

```text
http://localhost:8000
```

## 基本使用流程

1. 打开首页并进入简历优化流程
2. 输入或上传简历
3. 输入目标职位 JD
4. 等待系统完成 section 识别与匹配分析 (大约需要2分钟)
5. 查看整体分析结果和 section 级诊断
6. 生成优化后的简历 （大约需要2分钟）
7. 查看最终简历成品并导出
