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

## 3. 容器模式（适合对外演示/统一环境）
当前仓库的 Dockerfile 是“构建前端 + Python server + 注入 demo_data”的方式，更偏演示镜像。

### 3.1 构建并运行
```bash
docker compose -f docker-compose.dev.yml up --build
```

访问： http://127.0.0.1:7891

### 3.2 说明（热更新）
- 目前 `docker-compose.dev.yml` 没做代码卷挂载，因此容器内不会自动热更新。
- 若你需要“容器里热更新”，下一步可以把 compose 改成挂载本地目录到容器，并用 `python -u dashboard/server.py` 直接跑源码；前端则用 `npm run dev` 走宿主机或另起 node 容器。

## 4. 常见问题
- 端口被占用：`ss -lntp | grep :7891`
- 看板卡死/无响应：优先确认 server 是否为多线程（ThreadingHTTPServer）版本
