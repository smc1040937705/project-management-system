# 企业级项目管理系统 (Enterprise Project Management System)

一个功能完整的企业级项目管理系统，支持多角色权限管理、项目跟踪、任务分配、工时记录、文档管理和报表统计。

## 技术栈

### 后端
- **Python 3.11+**
- **FastAPI** - 高性能异步 Web 框架
- **SQLAlchemy 2.0** - ORM 框架
- **SQLite** - 内置数据库（可轻松切换到 PostgreSQL/MySQL）
- **JWT** - 身份认证
- **pytest** - 单元测试框架

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全的 JavaScript
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Element Plus** - UI 组件库
- **Vitest** - 单元测试框架

## 功能特性

### 用户管理
- 多角色权限系统（管理员、项目经理、团队负责人、成员）
- JWT 身份认证
- 用户资料管理

### 项目管理
- 项目创建、编辑、删除
- 项目状态跟踪（规划中、进行中、暂停、已完成、已取消）
- 项目成员管理
- 项目预算和时间规划

### 任务管理
- 任务创建、分配、跟踪
- 任务优先级设置（低、中、高、紧急）
- 任务状态流转（待办、进行中、审核中、已完成）
- 子任务支持
- 任务依赖关系
- 截止日期管理

### 工时追踪
- 时间日志记录
- 工时统计分析
- 项目工时汇总

### 文档管理
- 项目文档上传下载
- 文档版本控制
- 文件类型限制和大小限制

### 通知系统
- 站内消息通知
- 未读消息计数
- 通知类型分类

### 报表统计
- 项目统计概览
- 用户工作量统计
- 工时报表（按日/周/月/用户/项目分组）
- 项目进度追踪

## 项目结构

```
project-management-system/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 应用入口
│   │   ├── database.py        # 数据库配置
│   │   ├── models.py          # SQLAlchemy 模型
│   │   ├── schemas.py         # Pydantic 数据模型
│   │   ├── auth.py            # 认证相关
│   │   ├── config.py          # 配置管理
│   │   └── routers/           # API 路由
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── projects.py
│   │       ├── tasks.py
│   │       ├── time_entries.py
│   │       ├── documents.py
│   │       ├── notifications.py
│   │       └── reports.py
│   ├── tests/                 # 测试文件
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_users.py
│   │   ├── test_projects.py
│   │   ├── test_tasks.py
│   │   └── test_time_entries.py
│   ├── requirements.txt
│   └── pytest.ini
│
└── frontend/                  # 前端项目
    ├── src/
    │   ├── api/              # API 客户端
    │   ├── components/       # Vue 组件
    │   ├── layouts/          # 布局组件
    │   ├── router/           # 路由配置
    │   ├── stores/           # Pinia 状态管理
    │   ├── types/            # TypeScript 类型
    │   ├── utils/            # 工具函数
    │   └── views/            # 页面视图
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    └── vitest.config.ts
```

## 快速开始

### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload
```

后端服务将在 http://localhost:8000 启动
API 文档地址：http://localhost:8000/docs

### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 http://localhost:5173 启动

### 运行测试

**后端测试：**
```bash
cd backend
pytest

# 查看覆盖率
pytest --cov=app --cov-report=html
```

**前端测试：**
```bash
cd frontend
npm run test:unit

# 查看覆盖率
npm run test:coverage
```

## API 概览

### 认证相关
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/refresh` - 刷新 Token
- `GET /api/v1/auth/me` - 获取当前用户信息

### 用户管理
- `GET /api/v1/users` - 获取用户列表
- `GET /api/v1/users/{id}` - 获取用户详情
- `POST /api/v1/users` - 创建用户
- `PUT /api/v1/users/{id}` - 更新用户
- `DELETE /api/v1/users/{id}` - 删除用户

### 项目管理
- `GET /api/v1/projects` - 获取项目列表
- `GET /api/v1/projects/{id}` - 获取项目详情
- `POST /api/v1/projects` - 创建项目
- `PUT /api/v1/projects/{id}` - 更新项目
- `DELETE /api/v1/projects/{id}` - 删除项目
- `POST /api/v1/projects/{id}/members/{user_id}` - 添加成员
- `DELETE /api/v1/projects/{id}/members/{user_id}` - 移除成员

### 任务管理
- `GET /api/v1/tasks` - 获取任务列表
- `GET /api/v1/tasks/{id}` - 获取任务详情
- `POST /api/v1/tasks` - 创建任务
- `PUT /api/v1/tasks/{id}` - 更新任务
- `DELETE /api/v1/tasks/{id}` - 删除任务

### 工时记录
- `GET /api/v1/time-entries` - 获取工时记录
- `POST /api/v1/time-entries` - 创建工时记录
- `PUT /api/v1/time-entries/{id}` - 更新工时记录
- `DELETE /api/v1/time-entries/{id}` - 删除工时记录
- `GET /api/v1/time-entries/summary` - 获取工时汇总

### 报表统计
- `GET /api/v1/reports/projects/statistics` - 项目统计
- `GET /api/v1/reports/projects/{id}/statistics` - 单个项目统计
- `GET /api/v1/reports/users/statistics` - 用户统计
- `GET /api/v1/reports/time/summary` - 工时报表

## 测试覆盖

本项目包含完整的单元测试覆盖：

### 后端测试
- **认证测试** - 登录、注册、Token 刷新、权限验证
- **用户测试** - CRUD 操作、角色权限、搜索过滤
- **项目测试** - 项目管理、成员管理、状态流转
- **任务测试** - 任务 CRUD、状态变更、依赖关系
- **工时测试** - 时间记录、统计汇总、数据关联

### 前端测试
- **Store 测试** - Pinia 状态管理、数据流
- **工具函数测试** - 格式化函数、工具方法
- **组件测试** - Vue 组件渲染、交互

## 开发规范

### 后端
- 遵循 PEP 8 代码规范
- 使用类型注解
- 编写完整的 docstring
- 测试覆盖率要求 > 80%

### 前端
- 使用 TypeScript 严格模式
- 组件使用 Composition API
- 遵循 Vue 3 风格指南
- 测试覆盖率要求 > 80%

## 部署建议

### 生产环境配置

1. **数据库** - 将 SQLite 替换为 PostgreSQL 或 MySQL
2. **环境变量** - 使用 `.env` 文件管理配置
3. **静态文件** - 使用 Nginx 托管前端静态文件
4. **HTTPS** - 配置 SSL 证书
5. **Docker** - 使用 Docker Compose 部署

### Docker 部署示例

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/pms
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=pms
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License
