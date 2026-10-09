# W1 → Supabase 安全接入预检（一次性任务，2026-10-09）

> FROM: ChatGPT
> TO: W1 / Reasonix
> TASK: W1-SUPABASE-PREFLIGHT-20261009
> STATUS: READ-ONLY NETWORK PREFLIGHT
>
> GitHub 在本轮**仅用于读取这份启动说明**。之后的任务收发拟改走 Supabase，不在 GitHub Issue 留言，不配置 GitHub PAT。

## 目标

验证 W1 自身能够连到现有 Supabase 队列接口，并准备独立 Worker 身份的安全配置。**现在还不领取、执行或回传任何远程任务。**

现有 Supabase 项目：`chatgpt-workbuddy-queue`；其 Edge Function `workbuddy-queue` 已实测从腾讯云 GET /health 返回 HTTP 200，但 **W1 所处网络还没有验证**。

只读探测 URL：

`https://bzzjbbuosmpifrtgoaya.supabase.co/functions/v1/workbuddy-queue/health`

## 立即执行的步骤

1. 在 W1 Windows 环境下，通过 Python 标准库或 PowerShell 发起**一次无凭据 GET** 到上述 `/health`，报告 HTTP 状态、响应中 `status` 的值和耗时。只需要公共 health，不添加任何 Token。
2. 检查现有 `D:\WorkSpace\Reasonix\worker\` 内本地 worker 的运行方式（只在授权目录操作）；记录是否能作为无人值守进程启动以及已有单次本地任务测试是否仍 PASS。
3. 预选 W1 专用身份 `w1-reasonix-01`；检查本机是否已有 `W1_WORKBUDDY_TOKEN`，**只返回 PRESENT/ABSENT**，不要显示密钥值或长度。**本次不要自己生成、覆盖或保存新凭据**；令牌配置由下一轮 Owner 授权后完成。
4. 只在本地作静态检查：现有 worker 是否能基于单一 `expected_worker` 精确任务目标来过滤；是否对可执行动作有白名单。可以提出最小代码改动建议，但不启动领取/自动运行。

## 核心安全约束

现有 Supabase `claim_workbuddy_task` 允许领取没有 `expected_worker` 的泛用排队任务。因此 W1 **现在严禁调用 /claim、/finish，严禁访问其他 worker 的任务**；必须等 ChatGPT 完成服务端 W1 严格隔离，且 Owner 安全配置独立 Worker 身份后，才能做正式 E2E。

不修改 GitHub / Meta-System / WTOS / 数据库，不暴露任何凭据、设备身份、私人路径、业务敏感数据；不开放公网入站。

## 回复格式（只在 W1 本地会话中回复 Owner）

```text
TASK: W1-SUPABASE-PREFLIGHT-20261009
STATUS: PASS | PARTIAL | BLOCKED
SUPABASE_HEALTH: HTTP <code> / status <value> / latency <ms>
W1_WORKER_ID: w1-reasonix-01 (proposed only; not enrolled)
W1_TOKEN: PRESENT | ABSENT
LOCAL_WORKER: <single-run callable / blocked + exact reason>
AUTO_CLAIM: NOT_STARTED
REMOTE_WRITE: NOT_ATTEMPTED
BLOCKER: <concrete>
NEXT: <single next action>
```

**验收说明**：本任务 PASS 只证明 W1 → Supabase 公共健康接口可达和本地执行器预检通过，绝不代表 Worker 已登记、任务隔离或无人值守通信验收通过。
