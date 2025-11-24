"""
Vercel Serverless Function - 计算类目内聚度
"""
from sentence_transformers import SentenceTransformer
import numpy as np
from scipy.spatial.distance import cosine
import json

# 全局变量：模型缓存
_model = None

def load_model():
    """加载 SBERT 模型（带缓存）"""
    global _model
    if _model is None:
        print("正在加载 SBERT 模型...")
        try:
            _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("SBERT 模型加载成功")
        except Exception as e:
            print(f"模型加载失败: {e}")
            # 备用模型
            _model = SentenceTransformer('distiluse-base-multilingual-cased')
            print("使用备用 SBERT 模型")
    return _model

def handler(req):
    """Vercel Serverless Function Handler"""
    # 处理 CORS
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # 处理 OPTIONS 请求（CORS 预检）
    if req.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # 只处理 POST 请求
    if req.method != 'POST':
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # 获取请求体
        if hasattr(req, 'json') and req.json:
            data = req.json
        else:
            body = req.body
            if isinstance(body, str):
                data = json.loads(body)
            elif isinstance(body, bytes):
                data = json.loads(body.decode('utf-8'))
            else:
                data = body if body else {}
        
        # 验证输入
        if not data:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': '请求体为空'})
            }
        
        category = data.get('category', '').strip()
        items = data.get('items', [])
        aggregation_method = data.get('aggregation_method', 'mean')
        
        if not category:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': '类目词不能为空'})
            }
        
        if not items or len(items) == 0:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': '普通词列表不能为空'})
            }
        
        if aggregation_method not in ['mean', 'median', 'variance']:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': '聚合方法必须是 mean、median 或 variance'})
            }
        
        # 加载模型
        model = load_model()
        
        # 向量化：将类目词和所有普通词转换为向量
        print(f"正在向量化: 类目词='{category}', 普通词数量={len(items)}")
        
        # 准备所有文本（类目词 + 普通词）
        all_texts = [category] + items
        
        # 批量编码
        embeddings = model.encode(all_texts, convert_to_numpy=True, show_progress_bar=False)
        
        category_embedding = embeddings[0]
        item_embeddings = embeddings[1:]
        
        # 计算相似度：使用余弦相似度
        similarities = []
        for item_embedding in item_embeddings:
            cosine_distance = cosine(category_embedding, item_embedding)
            similarity = 1 - cosine_distance
            similarities.append(float(similarity))
        
        # 计算平均值
        mean_score = float(np.mean(similarities))
        
        # 计算方差（始终计算，供前端使用）
        variance = float(np.var(similarities))
        
        # 根据聚合方法确定返回的主要分数
        if aggregation_method == 'variance':
            cohesion_score = variance
        elif aggregation_method == 'mean':
            cohesion_score = mean_score
        else:  # median
            cohesion_score = float(np.median(similarities))
        
        print(f"计算完成: 平均值={mean_score:.4f}, 方差={variance:.4f}, 方法={aggregation_method}")
        
        result = {
            'cohesion_score': cohesion_score,
            'mean_score': mean_score,
            'variance': variance,
            'similarities': similarities,
            'method': aggregation_method,
            'category': category,
            'items_count': len(items)
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"计算错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'计算失败: {str(e)}'})
        }

