from sentence_transformers import SentenceTransformer, util

# 1. 关键变化：换用【语义相似度】模型
# 这个模型专门用来计算两个词/句子的意思相近程度
model_name = 'sentence-transformers/all-MiniLM-L6-v2'
print(f"正在加载语义模型: {model_name} ...")
model = SentenceTransformer(model_name)
print("模型加载成功！")

# 2. 数据
category = "Furniture"
items = ["Bed", "Chair", "Sofa", "Wardrobe", "Table", "Banana", "Spiky"]

print(f"\n【语义相似度测试】类目: {category}")
print(f"{'Item':<10} | {'相似度 (0-1)':<15}")
print("-" * 30)

# 3. 计算逻辑变了
# 先把词变成向量 (Embedding)
category_emb = model.encode(category, convert_to_tensor=True)
item_embs = model.encode(items, convert_to_tensor=True)

# 计算余弦相似度
scores = util.cos_sim(category_emb, item_embs)[0]

# 4. 打印
for item, score in zip(items, scores):
    print(f"{item:<10} | {score:.4f}")

print("-" * 30)
print("预期结果：")
print("Furniture 类的词 (Bed, Chair...) 应该在 0.4 到 0.8 之间")
print("无关词 (Banana, Spiky) 应该在 0.2 以下")