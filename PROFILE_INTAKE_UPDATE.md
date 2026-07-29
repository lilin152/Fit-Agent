# 身体资料采集 Agent 更新说明

## 本次新增

- 新增 DeepSeek 驱动的身体资料采集 Agent，入口为 `app/Agent/profile_agent.py`。
- 新增终端交互程序 `app/cli/profile_chat.py`，所有用户输入、模型回复和保存确认都在终端完成。
- 新增 `app/Agent/deepseek_provider.py`，统一从环境变量创建 `ChatDeepSeek`，不再在源码里写 API Key。
- 新增 `app/schemas/profile.py`，定义身体资料、伤病、改善部位、校验结果和基础评估的 Pydantic 模型。
- 新增 `app/services/profile_service.py`，负责确定性字段校验、资料合并、训练经验等级、BMI 和安全状态计算。
- 新增 `app/repositories/profile_repository.py`，负责 SQLite 表初始化、资料读取、保存和变更审计。
- 重写 `app/Agent/tools/profiles.py`，提供 `get_body_profile`、`validate_profile_patch`、`save_body_profile`、`assess_body_profile` 四个 LangChain 工具。
- 新增 `app/prompts/profile_intake_prompt.txt`，约束模型只做资料采集，不做医疗诊断或训练计划生成。
- 新增 `tests/test_profile_service.py`，覆盖必填字段、经验等级、安全阻断和持久化。
- 根目录 `main.py` 改为启动终端 Profile Agent。

## 设计边界

- `user_id` 不再由模型传入，改为通过 LangChain `runtime.context.user_id` 注入。
- 受伤部位使用 `injuries`，希望改善部位使用 `improvement_areas`，两者分开存储。
- 单项伤病或改善部位更新按 `body_part` 合并，不会删除未提及的其他记录；显式空列表表示清空。
- 体能速测等级暂不生成；当前只返回 `fitness_assessment_status=pending` 或 `blocked`。
- 伤病、疼痛、医生限制等安全相关信息由函数规则判断，模型只负责追问和解释。
- 写入资料前通过 `HumanInTheLoopMiddleware` 暂停，并在终端要求 `approve` 或 `reject`。

## 环境变量

复制 `.env.example` 为 `.env` 后填写：

```dotenv
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
FITNESS_DB_PATH=app/database/fitness.db
```

如果你的 DeepSeek 账号暂不支持 `deepseek-v4-pro`，可把 `DEEPSEEK_MODEL` 改成账号可用且支持工具调用的模型。

## 运行方式

```powershell
uv sync
uv run python main.py
```

启动后选择已有 `user_id`，然后在终端输入用户身体资料。保存时终端会展示待写入工具调用，输入 `approve` 后才会真正写入数据库。

## 安全注意

- 旧版 `app/Agent/base.py` 曾硬编码 DeepSeek API Key。该密钥应视为已暴露，请在 DeepSeek 控制台轮换。
- `.env` 当前已被 Git 跟踪；建议后续执行 `git rm --cached .env`，并确认 `.gitignore` 生效。
- `fitness.db` 当前也被 Git 跟踪；如果不希望提交本地数据，建议同样从 Git 索引移除。

## 验证结果

- 离线单元测试覆盖资料补全、经验等级、安全阻断、SQLite 保存和局部伤病更新。
- 在现有数据库副本上完成幂等迁移，原用户和左膝伤病数据保持可读。
- 完整 LangChain Agent 图可成功组装，包含 DeepSeek、工具、可信上下文、checkpointer 和 Human-in-the-loop。
- 已完成真实 DeepSeek API 只读调用：模型能读取已有资料并优先追问伤病状态、疼痛评分和触发动作。
