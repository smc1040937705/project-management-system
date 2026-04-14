# 测试说明文档

## 前端测试

### 技术栈
- **测试框架**: Vitest
- **测试工具**: @vue/test-utils
- **环境**: jsdom
- **Mock**: vi.mock

### 测试文件结构
```
frontend/
├── vitest.config.ts          # Vitest 配置文件
├── src/
│   └── tests/
│       ├── setupTests.ts     # 测试环境初始化
│       ├── stores/
│       │   ├── auth.test.ts      # 认证状态管理测试
│       │   ├── projects.test.ts  # 项目状态管理测试
│       │   └── tasks.test.ts     # 任务状态管理测试
│       └── api/
│           └── index.test.ts     # API 模块测试
```

### 运行测试命令

```bash
cd frontend

# 安装依赖
npm install

# 运行所有测试
npm run test:unit

# 运行测试并生成覆盖率报告
npm run test:coverage

# 运行特定测试文件
npx vitest run src/tests/stores/auth.test.ts

# 监听模式运行测试
npx vitest watch
```

### 测试覆盖范围

#### auth store 测试
- 初始状态验证
- 登录成功/失败场景
- 注册成功/失败场景
- 登出功能
- 用户信息获取
- 计算属性
- 初始化逻辑

#### projects store 测试
- 初始状态验证
- 获取项目列表（带参数/不带参数）
- 获取单个项目
- 创建项目
- 更新项目
- 删除项目
- 添加/移除项目成员
- loading 状态管理

#### tasks store 测试
- 初始状态验证
- 获取任务列表（带各种过滤参数）
- 获取单个任务
- 创建任务（含依赖）
- 更新任务
- 删除任务
- 添加/移除任务依赖
- loading 状态管理

#### API 模块测试
- authApi: login, register, getMe, refreshToken
- projectsApi: CRUD 操作, 成员管理
- tasksApi: CRUD 操作, 依赖管理
- timeEntriesApi: CRUD 操作, 汇总查询
- documentsApi: CRUD 操作, 文件上传

---

## 后端测试

### 技术栈
- **测试框架**: pytest
- **异步支持**: pytest-asyncio
- **HTTP 客户端**: httpx / FastAPI TestClient
- **数据库**: 内存 SQLite

### 测试文件结构
```
backend/
├── pytest.ini                 # pytest 配置文件
└── tests/
    ├── conftest.py            # 测试配置和 fixtures
    ├── test_auth.py           # 认证路由测试
    ├── test_projects.py       # 项目路由测试
    ├── test_tasks.py          # 任务路由测试
    ├── test_time_entries.py   # 工时记录路由测试
    └── test_documents.py      # 文档管理路由测试
```

### 运行测试命令

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行所有测试
pytest

# 运行测试并显示详细信息
pytest -v

# 运行特定测试文件
pytest tests/test_auth.py

# 运行特定测试类
pytest tests/test_auth.py::TestLogin

# 运行特定测试方法
pytest tests/test_auth.py::TestLogin::test_login_success

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html

# 运行测试并显示打印输出
pytest -s
```

### 测试覆盖范围

#### auth 路由测试
- **登录**: 成功登录、密码错误、用户不存在、账户已停用
- **注册**: 成功注册、邮箱重复、用户名重复、密码过短、邮箱格式错误
- **获取当前用户**: 成功获取、无 token、无效 token、过期 token
- **刷新 Token**: 成功刷新、无效 token、用户不存在
- **认证工具**: 密码哈希、创建/解码 token

#### projects 路由测试
- **列表查询**: 管理员/普通用户查询、状态过滤、搜索、分页
- **获取单个项目**: 成功获取、项目不存在、无权限访问
- **创建项目**: PM/管理员创建、带成员创建、无权限创建
- **更新项目**: 所有者更新、状态更新、项目不存在、无权限更新
- **删除项目**: 所有者/管理员删除、项目不存在、无权限删除
- **成员管理**: 添加成员、成员已存在、用户不存在、移除成员

#### tasks 路由测试
- **列表查询**: 管理员查询、项目/状态/优先级/指派人过滤、搜索、分页
- **获取单个任务**: 成功获取、任务不存在、无权限访问
- **创建任务**: 成功创建、带指派人/预估工时、项目不存在、指派人不存在
- **更新任务**: 指派人更新、状态更新为完成、优先级更新、清除指派人
- **删除任务**: 所有者/管理员删除、任务不存在、无权限删除
- **依赖管理**: 添加依赖、跨项目依赖、自引用、重复依赖、移除依赖

#### time_entries 路由测试
- **列表查询**: 管理员/普通用户查询、任务/用户/日期过滤、分页
- **获取单条记录**: 成功获取、记录不存在、无权限访问
- **创建记录**: 成功创建、更新任务工时、任务不存在、无权限创建
- **更新记录**: 更新工时（同步更新任务工时）、更新描述
- **删除记录**: 成功删除（同步更新任务工时）、记录不存在、无权限删除
- **工时汇总**: 成功获取、项目/用户过滤

#### documents 路由测试
- **列表查询**: 管理员查询、项目过滤、搜索、分页
- **获取单个文档**: 成功获取、文档不存在、无权限访问
- **上传文档**: 成功上传 PDF/TXT、项目不存在、文件类型不允许、无权限上传
- **删除文档**: 上传者/管理员删除、文档不存在、无权限删除

---

## 测试特点

### 前端测试特点
1. **Pinia 正确初始化**: 使用 `createPinia()` 和 `setActivePinia()`
2. **API Mock**: 使用 `vi.mock('@/api')` 模拟所有 API 调用
3. **不访问真实后端**: 所有请求都被 mock
4. **覆盖正常和异常场景**: 包括成功、失败、权限不足等

### 后端测试特点
1. **内存数据库**: 使用 SQLite 内存数据库，不污染真实数据
2. **测试隔离**: 每个测试函数独立的数据库会话
3. **Fixture 复用**: 提供常用的测试数据和认证头
4. **覆盖权限控制**: 测试不同角色的访问权限
5. **覆盖异常场景**: 包括数据不存在、验证失败、权限不足等

---

## 预期测试结果

运行测试后，预期所有测试用例通过，覆盖率应达到：
- 前端: Store 和 API 模块覆盖率 > 80%
- 后端: Router 覆盖率 > 85%
