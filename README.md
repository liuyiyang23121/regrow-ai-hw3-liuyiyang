# ReGrow AI

作业 3｜刘懿洋

## 老师如何查看

请先双击根目录里的 `ReGrow-AI-作业3-双击打开.html`。页面会直接在浏览器里打开，不需要安装 Python、Node.js，也不需要访问 `127.0.0.1`。这个版本可以查看界面和主要交互，适合快速验收。

如果需要检查 FastAPI、SQLite 和 SQL 自动修复，请再双击 `启动作业.bat`。脚本启动完成后，会在当前电脑打开完整版本。第一次运行如果缺少依赖，准备时间会稍长一些。

本次提交没有公网地址。README 中出现的 `http://127.0.0.1:8000` 只是完整版本启动后的本机入口，不是交给老师点击的链接。提交时请发送整个 `HW3-刘懿洋-提交版.zip`。

## 提交内容

最终提交文件是同级目录下的 `HW3-刘懿洋-提交版.zip`。解压后可以看到源码、启动脚本、离线预览、测试文件和部署配置。压缩包没有包含虚拟环境、`node_modules`、缓存或本地数据库，体积较小，也不会带入本机运行记录。

ReGrow AI 是一个电商召回任务工作台。产品经理或用户运营输入一句业务目标，例如“提升高流失、高客单用户的 30 天复购率”，系统会继续整理客群规则、执行 SQL、检查数据质量、生成 A/B 文案，并在上线前做风险审核。

完整版本内置 SQLite 模拟数据库，SQL 会实际执行。示例任务第一次会查询不存在的 `pay_amount` 字段，沙盒返回错误后，工作流将它改为 `paid_amount` 并重试。普通任务会生成实验方案；计划触达超过 50,000 人时，流程停在人工审核节点，等待确认后再继续。

项目根目录保留了 `Dockerfile` 和 `railway.json`，便于之后部署完整服务。本次提交不依赖云端地址。

## 这次作业做了什么

- 把一句模糊的增长目标整理成指标、人群、观察周期和约束条件。
- 根据数据字典生成只读 SQL，并在 SQLite 沙盒中检查表、字段和执行结果。
- SQL 报错后最多自动修复两次。本项目提供了一条固定可复现的修复路径。
- 到达数据清洗节点时，注册并调用 `exclude_recent_contacts`，排除最近 7 天已经触达的用户。
- 生成两版召回文案，由红方关注转化、蓝方检查用户感受和合规风险。
- 检查客群规模、授权、频控和文案。高风险任务进入人工审核。
- 输出客群规则、SQL、数据质量结果、A/B 文案和灰度实验方案。

## 页面说明

### 任务

任务页是主要操作区。点击“确认并执行”后，可以看到六个节点的实时状态。中间区域保存每一步产生的内容，右侧显示客群规模、SQL 修复次数、数据质量和风险等级。

### 知识库

知识库列出了工作流会读取的资料：

- 数据字典：`users`、`orders` 和 `campaign_touch_logs` 的可用字段。
- 指标口径：30 天复购率、高客单用户和流失预警用户的定义。
- 查询指南：只读 SQL 白名单、字段检查和查询建议。
- 文案与护栏：禁用表达、触达频控和人工审核阈值。

### 测试

测试中心提供三个可以直接运行的场景：

1. 正常营销任务：完整生成客群、文案和实验方案。
2. SQL 自动修复：复现 `pay_amount → paid_amount` 的报错和重试。
3. 高风险审核：模拟 55,000 人批量召回，检查流程能否停下，并在批准后继续。

## 技术结构

```text
Vue 3 工作台
    │  REST + SSE
FastAPI Orchestrator
    ├─ Goal Planner
    ├─ SQL Audience Agent ── SQLite 沙盒
    ├─ Data Quality Agent ── 动态工具注册表
    ├─ Strategy & Copy Agent
    ├─ Red / Blue Evaluator
    └─ Guardrail + 人工审核
```

前端使用 Vue 3、Vite 和 Phosphor Icons。后端使用 FastAPI、Pydantic、SQLite 与 Agno。SSE 用来推送节点状态，任务结果以结构化 JSON 保存，前端不解析模型的自由文本来拼界面。

## 运行项目

### 接收作业后直接运行

环境要求：Windows 10/11、Python 3.11 或更高版本。运行演示版不需要 Node.js，也不需要 OpenAI API Key。

1. 解压完整文件夹。
2. 双击根目录下的 `启动作业.bat`。
3. 第一次启动会自动创建 Python 环境并下载依赖，需要保持网络连接。
4. 浏览器自动打开后即可演示；命令窗口需要保持打开。
5. 演示结束后，在命令窗口按 `Ctrl+C` 停止服务。

如果浏览器没有自动打开，手动访问 [http://127.0.0.1:8000](http://127.0.0.1:8000)。

### 开发模式

需要修改 Vue 源码时，再分别启动后端和 Vite：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端：

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

开发模式访问 [http://127.0.0.1:5173](http://127.0.0.1:5173)，Vite 会把 `/api` 请求转发到 FastAPI。

## 使用 Agno 模型

不填模型密钥时，项目使用确定性演示模式。数据、报错和审核结果固定，课堂演示不会因为网络或模型输出波动而中断。

如需调用真实模型，把 `backend/.env.example` 复制为 `backend/.env`，然后填写：

```env
OPENAI_API_KEY=你的密钥
MODEL_NAME=gpt-4.1-mini
```

配置成功后，目标解析、SQL 生成与文案生成会切换到 Agno Agent。SQL 仍需通过本地只读沙盒，安全审核也仍由确定性规则执行。

云端部署时不要把密钥写进源码或压缩包，应在托管平台的环境变量中设置 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 和 `MODEL_NAME`。不设置密钥时，云端使用与本地相同的确定性演示模式，SQLite、SQL 沙盒、动态工具注册和人工审核仍会实际运行。

## 建议演示顺序

1. 在任务页运行默认目标，停留在 SQL 页观察字段报错和自动修复。
2. 打开数据质量页，查看工具注册信息、排除人数和五项检查。
3. 打开 A/B 文案页，对比两版表达以及蓝方的修改意见。
4. 打开实验方案页，说明分组比例、灰度节奏和停止条件。
5. 从测试中心运行高风险场景。流程停下后，点击“批准并继续”，确认它从安全审核节点恢复。

## 验证

后端测试：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

前端构建：

```powershell
cd frontend
npm run build
```

当前结果为 4 项后端测试通过，前端生产构建通过。测试覆盖 SQL 沙盒修复、工具白名单、正常任务和高风险人工审核。

## 目录

```text
HW3-刘懿洋/
├─ backend/                 FastAPI、Agent、SQLite 与测试
├─ frontend/                Vue 源码和已构建页面
├─ design/                  参考稿、设计规范与验收截图
├─ Dockerfile               完整前后端云端镜像
├─ railway.json             Railway 部署与健康检查配置
├─ design-qa.md             视觉和交互验收记录
├─ ReGrow-AI-作业3-双击打开.html  无需安装的离线演示
├─ 启动作业.bat             Windows 一键启动脚本
├─ 启动说明.txt             给接收者的简版说明
└─ README.md
```

设计参考见 `design/reference-option-1.png`，最终验收记录见 `design-qa.md`。
