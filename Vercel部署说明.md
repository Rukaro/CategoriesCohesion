# Vercel 部署说明

## 部署步骤

### 1. 安装 Vercel CLI（可选）

```bash
npm i -g vercel
```

### 2. 登录 Vercel

```bash
vercel login
```

### 3. 部署项目

在项目根目录运行：

```bash
vercel
```

或者直接通过 GitHub 部署：

1. 将代码推送到 GitHub
2. 访问 https://vercel.com/
3. 点击 "New Project"
4. 导入你的 GitHub 仓库
5. Vercel 会自动检测配置并部署

## 项目结构

```
CategoriesCohesion/
├── api/                    # Vercel Serverless Functions
│   ├── calculate.py       # 计算类目内聚度 API
│   └── health.py          # 健康检查 API
├── index.html             # 前端页面
├── vercel.json            # Vercel 配置文件
├── requirements.txt       # Python 依赖
└── .vercelignore          # 忽略文件
```

## 配置说明

### vercel.json

- `builds`: 指定使用 Python runtime
- `routes`: 路由配置
  - `/api/*` 路由到 Serverless Functions
  - 其他路由返回静态文件
- `functions`: 函数配置
  - `maxDuration`: 最大执行时间（60秒）

### API Functions

- `api/calculate.py`: 处理类目内聚度计算
- `api/health.py`: 健康检查接口

## 注意事项

### 1. 模型大小限制

Vercel Serverless Functions 有大小限制：
- 免费版：50MB
- Pro 版：250MB

SBERT 模型可能超过限制，解决方案：
1. 使用较小的模型（如 `distiluse-base-multilingual-cased`）
2. 使用 Vercel Pro 计划
3. 将模型存储在外部（如 S3），运行时下载

### 2. 冷启动时间

首次请求可能需要较长时间加载模型（冷启动），后续请求会更快。

### 3. 环境变量

如果需要配置环境变量：
1. 在 Vercel 项目设置中添加
2. 或在 `vercel.json` 中配置

## 本地测试

### 使用 Vercel CLI 本地测试

```bash
vercel dev
```

这会启动本地开发服务器，模拟 Vercel 环境。

### 使用传统方式测试

```bash
python server.py
```

然后访问 `http://localhost:5000/`

## 部署后访问

部署成功后，Vercel 会提供一个 URL，例如：
```
https://your-project.vercel.app
```

访问该 URL 即可使用工具。

## 常见问题

### Q: 部署失败，提示模型太大？

**A:** 
1. 修改 `api/calculate.py` 使用更小的模型
2. 或升级到 Vercel Pro 计划

### Q: 请求超时？

**A:** 
1. 检查 `vercel.json` 中的 `maxDuration` 设置
2. 首次请求加载模型可能需要较长时间

### Q: CORS 错误？

**A:** 
API 函数已配置 CORS，如果仍有问题，检查 `api/calculate.py` 中的 headers。

## 优化建议

1. **使用模型缓存**：模型已实现全局缓存，减少加载时间
2. **批量处理**：前端已实现批量计算，减少请求次数
3. **错误处理**：完善的错误处理和用户提示

## 更新部署

代码更新后，重新运行：

```bash
vercel --prod
```

或通过 GitHub 推送，Vercel 会自动重新部署。

