# 飞书边栏插件 - 类目内聚度分析

使用 Sentence-BERT (SBERT) 模型计算类目内聚度指标，评估类目下词语的关联性。

## 功能说明

本插件实现了"中心距离平均法"来计算类目内聚度：

1. **向量化**：将类目词（Category）和每个普通词（Items）通过 SBERT 模型转换为向量表示
2. **计算距离**：分别计算类目词向量与每个普通词向量之间的余弦相似度
3. **聚合评分**：对所有相似度值求平均值（Mean）或中位数（Median），作为类目内聚度指标

## 项目结构

```
CategoriesCohesion/
├── manifest.json          # 飞书插件配置文件
├── sidebar.html          # 边栏界面 HTML
├── styles.css            # 样式文件
├── sidebar.js            # 前端逻辑
├── server.py             # 后端服务（Python Flask）
├── requirements.txt      # Python 依赖
└── README.md            # 说明文档
```

## 安装步骤

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
python server.py
```

服务将在 `http://localhost:5000` 启动。

### 3. 配置飞书插件

1. 登录 [飞书开放平台](https://open.feishu.cn/)
2. 创建新应用，选择"企业自建应用"
3. 在"应用功能"中选择"网页"或"自定义组件"
4. **输入插件地址**：`http://localhost:5000/sidebar.html`
   - 本地开发：使用 `http://localhost:5000/sidebar.html`
   - 生产环境：使用公网可访问的地址
5. 配置插件权限：
   - `bitable:read` - 读取多维表格数据
   - `bitable:write` - 写入多维表格数据（可选）
6. 发布插件并安装到你的飞书工作台

**详细配置说明请查看：`飞书插件配置指南.md`**

### 4. 使用插件

1. 在飞书多维表格中打开插件
2. 选择一条记录
3. 在边栏中：
   - 选择"类目词字段"（包含类目词的字段）
   - 选择"普通词字段"（包含普通词列表的字段，用换行、逗号或分号分隔）
   - 选择聚合方法（平均值或中位数）
4. 点击"开始分析"按钮
5. 查看类目内聚度指标和详细相似度

## 技术说明

### SBERT 模型

默认使用 `paraphrase-multilingual-MiniLM-L12-v2` 模型，支持多语言（包括中文）。如果下载失败，会自动切换到备用模型 `distiluse-base-multilingual-cased`。

### 相似度计算

使用余弦相似度来衡量向量之间的相似性：
- 值域：-1 到 1
- 值越大表示越相似
- 计算公式：`similarity = 1 - cosine_distance`

### 聚合方法

- **平均值 (Mean)**：所有相似度的算术平均值，反映整体趋势
- **中位数 (Median)**：所有相似度的中位数，对异常值更鲁棒

## 注意事项

1. 首次运行时会自动下载 SBERT 模型，可能需要一些时间
2. 确保后端服务在 `localhost:5000` 运行，前端才能正常调用
3. 普通词字段支持用换行、逗号、分号分隔多个词语
4. 类目词和普通词字段必须是文本类型

## 开发说明

### 修改后端端口

如需修改后端服务端口，需要同时修改：
- `server.py` 中的 `app.run(port=5000)`
- `sidebar.js` 中的 `fetch('http://localhost:5000/...')`

### 更换 SBERT 模型

在 `server.py` 的 `load_model()` 函数中修改模型名称。推荐的中文模型：
- `paraphrase-multilingual-MiniLM-L12-v2`（默认）
- `distiluse-base-multilingual-cased`
- `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`

## 许可证

MIT License

