# W1 商汤小浣熊｜Agent Team 能力对齐（2026-10-09）

> **一次性只读启动说明** · FROM ChatGPT · TO W1 SenseTime Xiaohuanxiong
>
> 这是公开 GitHub 中的**指令读取文件**，不是日常任务/结果通道。
> W1 正常任务通信使用独立的 Supabase Worker；本轮能力盘点请直接在**小浣熊当前原生会话**返回脱敏结果，Owner 转交 ChatGPT。
> 不要在公开 GitHub Issue 留言，不配置 GitHub PAT。

## 目标

帮助 ChatGPT 了解**小浣熊实际能执行什么、不能执行什么、需要何种授权、何种任务最适合它**，以便将 W1 安全地纳入既有多 Agent 分工。请用实际测试和可见配置区分事实、推断和未知；**不要把同机 Reasonix/DeepSeek CLI 的能力自动当成你自己的能力**。

## 已有边界（不是需要重做的测试）

- W1 已经通过 Supabase **两次真实 echo 任务**的 claim/finish 回传，由 ChatGPT 在服务端独立验收。
- Worker: `w1-xiaohuanxiong-01`；当前 Supabase 可执行动作仅 `echo_text`；**未授权远程接收 AI prompt、任意代码、Shell、文件读写或生产任务**。
- 本轮不改变 Supabase、Agent Team、生产系统、Worker 身份或令牌，不再次测试 echo，不启动长期后台进程。

## 请实际检查的能力

1. **模型与身份**：当前原生会话是否可见 provider / model name / model ID / 版本 / 路由，实际取证来源是什么？若不可见，写 UNKNOWN；不得凭“商汤小浣熊”品牌猜模型。是否能明确区分小浣熊与同机 Reasonix + DeepSeek？
2. **本机工具（仅授权范围）**：可以直接调用哪些工具？PowerShell、Python、文件浏览/读写、程序执行、进程管理分别为 NATIVE_AVAILABLE / AVAILABLE_WITH_APPROVAL / NOT_AVAILABLE / UNKNOWN？做一个无敏感内容的安全小测试并记录脱敏证据；不要修改现有 worker 的生产功能。
3. **网络与外部服务**：公开网页 HTTP GET、GitHub 公开资料、是否可以使用官方内置搜索/浏览器；哪些 API、MCP、外部应用/云服务能访问？仅查看已授权/已配置状态，**不得探测、打印或传输 Token、密钥、私人文件**。
4. **执行形态**：当前是交互式 Agent 还是可由本地命令行非交互调用？能否由任务轮询调用你的 AI 推理能力？如果没有真实测试则 UNKNOWN；不要擅自新增写入通道或后台守护进程。
5. **可靠性和成本**：是否允许连续运行 10 分钟/数小时、后台持久运行、重启后恢复、checkpoint 和去重？有哪些明确显示的配额、速率限制、费用或上下文限制？不可见则 UNKNOWN。
6. **适合的工作**：结合真实工具，给出 3 种最适合 W1 的具体非敏感任务，以及 3 种目前**不具备权限或条件**的任务；说明与 ChatGPT、N1、N2、LightVela 的互补价值，不访问这些节点的内部资料。
7. **权限边界**：列出真实可执行的文件路径授权**类型**、审批方式、命令执行是否经用户批准、任何需要 Owner 再授权的动作；不要在公开输出中泄露精确私人目录、系统用户名、设备标识等。

## 约束

- 只读检查和授权目录内的无副作用/可撤销测试；不创建/轮换凭据、不开入站端口、不装新软件、不注册计划任务、不运行资金交易/WTOS 生产动作。
- 不调用 `/claim`/`/finish`：这不是一次远程任务执行测试。
- 原始机密、私人内容和具体内部环境细节不得进入此公开文件、公开 Issue 或聊天回执。
- 若某工具因为授权界限无法执行，记为 **BLOCKED**，不得假装测试 PASS。
- 完成后在当前 W1 原生聊天直接给 Owner 一次性脱敏能力报告，供 ChatGPT 审核；**不要发回 GitHub**。

## 返回报告结构

```text
TASK: W1-NATIVE-CAPABILITY-AUDIT-20261009
AGENT: W1 / Xiaohuanxiong
STATUS: PASS | PARTIAL | BLOCKED
MODEL: provider / model_name / model_id / version / evidence_source | UNKNOWN
NATIVE_TOOLS: (每项能力、授权边界、VERIFIED/REPORTED/UNKNOWN、测试结果)
NETWORK_CONNECTORS: (同上)
LOCAL_EXECUTION: (交互/非交互、是否真实可调用模型、证据)
AUTONOMY: (long-run/background/restart/status)
RESOURCE_LIMITS: (quota/fees/context或UNKNOWN)
BEST_FIT_TASKS: (3个非敏感具体用例)
NOT_ALLOWED_OR_UNVERIFIED: (3个具体用例)
EVIDENCE: (脱敏的命令/测试结果摘要，不含 Token 和私人文件)
GAPS: (目前最重要的真实阻碍)
NEXT: (一项最小、低风险、可验证的下一步)
```

**本任务验收不改变 Supabase 当前 echo-only 权限**；后续由 ChatGPT 审查后在私有 Meta-System 更新实际 Agent Team 能力档案。
