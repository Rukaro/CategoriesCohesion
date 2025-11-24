# 类目内聚度分析工具

使用 Sentence-BERT (SBERT) 模型计算类目内聚度指标，评估类目下词语的关联性。

## 功能说明

本工具实现了"中心距离平均法"来计算类目内聚度：

1. **向量化**：将类目词（Category）和每个普通词（Items）通过 SBERT 模型转换为向量表示
2. **计算距离**：分别计算类目词向量与每个普通词向量之间的余弦相似度
3. **聚合评分**：计算平均值（Mean）和方差（Variance）

## 项目结构

```
CategoriesCohesion/
├── api/                    # Vercel Serverless Functions
│   ├── calculate.py       # 计算类目内聚度 API
│   └── health.py          # 健康检查 API
├── index.html             # 前端页面
├── vercel.json            # Vercel 配置文件
├── requirements.txt       # Python 依赖
├── package.json           # Node.js 配置（用于 Vercel CLI）
└── README.md             # 说明文档
```

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python server.py
```

### 3. 访问工具

打开浏览器访问：`http://localhost:5000/`

## Vercel 部署

### 方法 1: 使用 Vercel CLI

```bash
# 安装 Vercel CLI
npm i -g vercel

# 登录
vercel login

# 部署
vercel

# 生产环境部署
vercel --prod
```

### 方法 2: 通过 GitHub

1. 将代码推送到 GitHub
2. 访问 https://vercel.com/
3. 点击 "New Project"
4. 导入你的 GitHub 仓库
5. Vercel 会自动检测配置并部署

详细部署说明请查看：`Vercel部署说明.md`

## 使用方法

### 输入格式

每行一组数据，格式：`类目词:子词1,子词2,子词3,...`

示例：
```
水果:苹果,香蕉,橙子,葡萄
动物:猫,狗,鸟,鱼
颜色:红色,蓝色,绿色,黄色
```

### 输出结果

表格显示：
- **类目词**：输入的类目词
- **子词列表**：输入的子词
- **平均值 (Mean)**：相似度的平均值
- **方差 (Variance)**：相似度的方差

## 技术说明

### SBERT 模型

默认使用 `paraphrase-multilingual-MiniLM-L12-v2` 模型，支持多语言（包括中文）。

### 相似度计算

使用余弦相似度来衡量向量之间的相似性：
- 值域：-1 到 1
- 值越大表示越相似
- 计算公式：`similarity = 1 - cosine_distance`

### 聚合方法

- **平均值 (Mean)**：所有相似度的算术平均值，反映整体趋势
- **方差 (Variance)**：相似度值的方差，衡量离散程度

## 注意事项

### Vercel 部署限制

1. **模型大小**：Vercel Serverless Functions 有大小限制
   - 免费版：50MB
   - Pro 版：250MB
   - 如果模型太大，可能需要使用更小的模型或升级计划

2. **冷启动**：首次请求可能需要较长时间加载模型

3. **超时时间**：已配置最大执行时间为 60 秒

## 许可证

MIT License
