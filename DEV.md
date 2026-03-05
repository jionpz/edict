# Edict（三省六部）本地迭代开发指南

## 1. 代码仓库
- upstream（原作者）：`cft0808/edict`
- origin（你的 fork）：`jionpz/edict`

常用命令：
```bash
git remote -v
# 拉取上游
git fetch upstream
# 合并上游 main
git merge upstream/main
```

## 2. 开发模式（推荐：本地跑，改完即生效）
这套最适合你“实时不断迭代”。

### 2.1 启动数据刷新循环（终端 A）
```bash
bash scripts/run_loop.sh
```

### 2.2 启动看板服务（终端 B）
```bash
python3 dashboard/server.py --host 0.0.0.0 --port 7891
```

访问： http://127.0.0.1:7891

> 备注：前端 dev（可选）
```bash
cd edict/frontend
npm install
npm run dev
# http://localhost:5173
```

## 3. 容器模式（推荐：本地改代码立即生效）
如果你希望“容器跑起来，但本地改代码马上生效”，用 `docker-compose.hot.yml`。

### 3.1 启动（看板 + 刷新循环 + 前端热更新）
```bash
docker compose -f docker-compose.hot.yml up --build
```

- 看板：http://127.0.0.1:7891
- 前端 dev：http://127.0.0.1:5173

### 3.2 热更新行为
- `dashboard/server.py`：容器内用 `watchfiles` 自动重启，改完即生效。
- `edict/frontend`：Vite dev server 热更新，改完即生效。
- 数据刷新：`edict-loop` 容器持续运行 `scripts/run_loop.sh`。

### 3.3 Docker daemon 说明
- WSL 下需要 Docker Desktop（开启 WSL Integration）或本机 docker daemon 正常运行，否则 `docker compose` 会提示无法连接。

## 4. 常见问题
- 端口被占用：`ss -lntp | grep :7891`
- 看板卡死/无响应：优先确认 server 是否为多线程（ThreadingHTTPServer）版本
