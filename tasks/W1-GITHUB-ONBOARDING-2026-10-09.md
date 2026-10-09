# W1 → GitHub 公共任务读取与接入预检（2026-10-09）

> 任务类型：一次性接入测试；公开指令，无敏感配置。  
> 对象：W1（Reasonix + DeepSeek，Windows）。  
> 发布位置：`zdmor/public-lab-01@master`。  
> 此文件不是 Meta-System 的正式任务登记，也不是自动执行授权。

## 目标

让 W1 自主通过 GitHub 读取本文件，实际验证“公开仓库提供任务指令”可行，并给出进入现有 ChatGPT 主导的多 Agent 工作流所需的**最小下一步**。不要创建第二套架构。

## 现在执行

1. **验证真实读取**：通过无需登录的 HTTPS/GitHub Contents API 读取此文件，记录 HTTP 状态、仓库、分支、路径、内容标题、读取时间；不能用推测代替测试。
2. **确认访问边界**：匿名访问只代表公开仓库可读。只读检测 `zdmor/Meta-System`、`zdmor/agent-capabilities`、`zdmor/Stock-Analysis`、`zdmor/Semiconductor-Filter-Lab` 的匿名可访问性。若返回 404/403，标为 `PRIVATE_OR_INACCESSIBLE`，禁止声称已经读到内部 Manifest/Checklist 或推测其当前规则。
3. **核对 W1 执行能力**：用现有 Reasonix CLI 和 PowerShell，验证能否从公开文件提取任务并执行一个**无副作用**的本地测试（例如读取本文件标题并生成内存中的 JSON 响应）。不要安装工具、开端口、创建计划任务或修改正式项目。
4. **最小对接建议**：区分两条链路：① GitHub 公开任务“读取”已实测；② W1 自动领取正式任务和回传执行证据尚需受控认证的写入/调度通道。优先建议复用现有通道，但未获得内部规则前，不假设 Supabase 表结构、API、权限或运行状态。
5. **如需权限或配置**：仅列出字段类型和由 Owner 通过安全渠道配置的步骤，不请求在公开仓库、聊天输出、日志或任务报告中暴露 Token、密钥、私有数据。

## 禁止事项

- 不得把公开任务当作修改私有仓库、生产任务或系统权限的授权。
- 不得绕过本地文件授权范围、审批或读取/打印密钥。
- 不得发布 W1 本地环境详情、内网 IP、账户凭据或私人仓库内容到公开 GitHub。
- 没有实际完成远程双向链路前，不得宣称“ChatGPT 已能自动给 W1 下任务”。
- 本轮仅做只读远程验证和本地无副作用测试；不更改 GitHub、Meta-System 或任何生产系统。

## 输出（直接在 W1 当前会话中回复，供 Owner 转交 ChatGPT）

```json
{
  "task": "W1-PUBLIC-GITHUB-BOOTSTRAP-20261009",
  "status": "PASS | PARTIAL | BLOCKED",
  "public_task_read": {
    "result": "PASS | FAIL",
    "url": "https://github.com/zdmor/public-lab-01/blob/master/tasks/W1-GITHUB-ONBOARDING-2026-10-09.md",
    "http_status": null,
    "title_verified": false
  },
  "private_repositories": "每个仓库的匿名 HTTP 状态与判断，不含私有内容",
  "local_test": "执行方法与真实结果；未执行必须写 NOT_RUN",
  "communication": "当前已验证的任务输入方式与结果输出方式",
  "blocker": "唯一最关键缺口",
  "next": "一个最小、可执行、可验证的下一步"
}
```

**验收约束**：只有 GitHub 读取、W1 本地调用和输出都存在真实证据时，才能标记 `PASS`；即使本任务 `PASS`，也仅表示“单次公开任务读取闭环”，不等于长期自动调度或生产验收。
