# Vercel 配置说明

## 当前配置

`vercel.json` 已简化为最基本的配置，只包含路由重写规则。

## 如果仍然遇到错误

### 方案 1: 完全移除 vercel.json

Vercel 会自动检测 `api/` 目录下的 Python 文件，所以可能不需要 `vercel.json`：

```bash
# 删除 vercel.json
rm vercel.json
```

然后直接访问：
- `/api/calculate.py` - 计算 API
- `/api/health.py` - 健康检查

### 方案 2: 使用最简单的配置

如果方案 1 不行，使用当前的最简配置（已应用）。

### 方案 3: 检查文件命名

确保 API 文件在 `api/` 目录下，并且：
- 文件名：`calculate.py`、`health.py`
- 包含 `handler` 函数
- 返回正确的格式

## Vercel 自动检测规则

Vercel 会自动：
1. 检测 `api/` 目录下的 `.py` 文件
2. 将其识别为 Python Serverless Functions
3. 根据文件名创建路由：
   - `api/calculate.py` → `/api/calculate`
   - `api/health.py` → `/api/health`

## 路由映射

如果需要自定义路由（如 `/api/calculate-cohesion`），可以使用 `vercel.json` 中的 `rewrites`。

## 验证

部署后，访问：
- `https://your-project.vercel.app/api/health` - 应该返回健康检查
- `https://your-project.vercel.app/api/calculate.py` - 计算 API（如果使用自动路由）

## 超时设置

如果需要设置超时时间，可以在 Vercel Dashboard 中配置：
1. 进入项目设置
2. Functions 标签页
3. 设置每个函数的超时时间

