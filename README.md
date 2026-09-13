# 项目财务台账

适用于多人维护的项目财务记录：按年度和项目管理主合同金额、分包支出、其他成本、开票进度和预计毛利。

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ADMIN_PASSWORD='请设置强密码' flask --app app run
```

首次启动会创建管理员。默认用户名为 `admin`；请务必通过环境变量 `ADMIN_PASSWORD` 设置初始密码。

## 部署到 Render

1. 将此目录推送到 GitHub。
2. 在 Render 中选择 **New → Blueprint**，连接该仓库，Render 会读取 `render.yaml` 并创建 Web Service 和 PostgreSQL 数据库。
3. 部署前填写 `ADMIN_PASSWORD`，并保管好自动生成的 `SECRET_KEY`。
4. 使用管理员账号登录，在“用户管理”中创建团队成员账号。

> 使用托管 PostgreSQL 可让多位成员访问同一份数据；不要在生产环境使用默认 SQLite 数据库。
