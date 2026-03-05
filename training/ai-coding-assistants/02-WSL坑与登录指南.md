# WSL 常见坑与登录指南（百官必读）

## 1) `gh auth login` 浏览器打开但页面无法连接
- 现象：浏览器被拉起，但打开的 URL（常是 `http://127.0.0.1:xxxxx/`）连接失败。
- 原因：回调服务在 WSL 的 localhost，浏览器在 Windows 打开，Windows 的 127.0.0.1 指向 Windows 自己。

### 推荐解决方案（按优先级）
1. **PAT 粘贴登录（最稳）**
   - 生成 token（Classic）：https://github.com/settings/tokens/new
   - scopes：`repo`, `read:org`, `gist`
   - WSL 执行：`gh auth login --with-token`，粘贴 token
2. **Device Code 登录**
   - 运行 `gh auth login`
   - 按提示在 Windows 浏览器输入 code

## 2) 端口/服务跑在两边导致“看得见点不动”
- 原则：服务和控制尽量在同一环境内（你当前选择 WSL 原生运行是最稳的）。

## 3) Docker 拉镜像超时（可选）
- 若使用 Docker Desktop/WSL docker daemon，可能需要 daemon 配代理；否则 `docker pull` 超时。
- 日常开发不强制用容器时，可以直接不用。
