# Msal SSO 演示
git clone -b sso --depth 1 https://github.com/bluemeat0725/exp_inventory.git msal_sso
## 环境配置
1. 进入后端目录：
   ```bash
   cd api
   ```

2. 复制环境变量模板：
   ```bash
   copy .env.example .env  # Windows
   # 或
   cp .env.example .env    # Linux/macOS
   ```

3. 编辑 `.env` 文件，配置以下必要参数：
   ```env
   # Redis 配置
   REDIS_HOST=127.0.0.1
   
   # Azure AD 配置
   AAD_CLIENT_ID=your-azure-client-id
   AAD_TENANT_ID=your-azure-tenant-id
   AAD_SECRETKEY=your-azure-client-secret
   AAD_CERTIFICATE_THUMBPRINT=your-certificate-thumbprint
   AAD_PRIVATE_KEY_FILE=certificate.pem
   
   # 前端地址
   FRONTEND_URL=http://localhost:5173
   AAD_REDIRECT_END_POINT=/login/callback
   ```

#### 前端环境配置
1. 进入前端目录：
   ```bash
   cd ../sso_page
   ```

2. 复制环境变量模板（可选）：
   ```bash
   copy .env.example .env  # Windows
   # 或
   cp .env.example .env    # Linux/macOS
   ```

3. 如需自定义配置，编辑 `.env` 文件：
   ```env
   # API 服务器地址
   VITE_API_URL=http://localhost:8000
   
   # 登录页面倒计时配置（秒），0表示直接跳转
   VITE_LOGIN_COUNTDOWN=0
   ```
   
## 启动服务

#### 启动后端服务
```bash
# 进入后端目录
cd api

# 安装依赖
uv sync

# 启动开发服务器
uv run python main.py
```

后端服务将在 `http://localhost:8000` 启动

#### 启动前端服务
```bash
# 进入前端目录（新开终端窗口）
cd sso_page

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 `http://localhost:5173` 启动

### 4. 访问应用
打开浏览器访问：`http://localhost:5173`
