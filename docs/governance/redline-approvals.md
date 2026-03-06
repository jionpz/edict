# 红线动作 Telegram 按钮审批（推荐方案落地）

> 目标：任何高风险动作必须由皇上在 Telegram 一键确认；同时对“安全且高频”的 host exec 命令支持永久放行。

## 0) 推荐方案（已拍板）
- 红线范围：**exec + 配置变更 + 删除/覆盖 + 外发动作** 全部需要审批。
- 按钮：`拒绝 / 允许一次 / 永久允许`
- **永久允许仅对 exec 生效**（写入 exec approvals allowlist）；其它红线不提供永久允许（最多允许一次）。

## 1) 触发条件（何时必须弹出审批）
满足任一项即视为红线：

### 1.1 Exec（主机命令）
- 任意 `sudo` / `su` / 提权
- 任意包管理安装：`apt/yum/dnf/pacman/brew`、`pip`、`npm/pnpm/yarn` 安装/全局安装
- 任意服务/进程控制：`systemctl`、`service`、`kill`、`pkill`、`docker`（运行/删除）
- 任意删除/覆盖：`rm`（尤其 `-rf`）、`truncate`、重定向覆盖 `>`
- 任意网络外联：`curl/wget`（下载/上传/发请求）

### 1.2 配置变更
- `openclaw config set` / `gateway config.patch/apply` / 修改 allowFrom/groupPolicy

### 1.3 删除/覆盖文件
- 删除关键目录、覆盖配置文件、批量替换

### 1.4 外发动作
- 群发、跨群发送、编辑/删除消息、代表皇上发公告

## 2) 按钮交互协议（Telegram inline buttons）
大臣在触发红线时必须给皇上发一条审批消息，包含：
- 任务ID（JJC-xxxx），若无写 N/A
- 风险说明（1-2 句）
- 计划执行动作（命令/配置diff/目标对象）
- 回滚方案（1 句）

并附三个按钮：
- `拒绝` → deny
- `允许一次` → allow-once
- `永久允许` → allow-always（**仅限 exec**）

> Telegram 回调以文本形式回到 agent：`callback_data: <value>`

### 2.1 callback_data 规范（建议）
- `redline|<reqId>|deny`
- `redline|<reqId>|allow-once`
- `redline|<reqId>|allow-always`

## 3) 永久允许的落点（exec approvals）
- 仅对 exec：把可执行文件路径模式写入 `~/.openclaw/exec-approvals.json` allowlist。
- 粒度：优先允许“固定脚本路径/已审计工具”，避免允许解释器/壳层。

## 4) 回执与证据
- 允许一次/永久允许后：大臣必须回报执行输出（≤10行）+ 证据路径。
- 拒绝后：大臣回报“已拒绝，未执行”。

## 5) 测试用例（验收）
- 触发一条红线（如 `systemctl restart ...`）→ 皇上收到按钮 → 点“允许一次”→ 执行成功并回报证据。
- 对同类 exec 再触发 → 点“永久允许”→ 后续同一可执行文件路径命中 allowlist 不再弹框（仍记录）。
