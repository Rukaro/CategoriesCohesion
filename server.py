"""
飞书边栏插件后端服务
使用 SBERT 模型计算类目内聚度指标
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sentence_transformers import SentenceTransformer
import numpy as np
from scipy.spatial.distance import cosine
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # 允许跨域请求

# 添加全局响应头处理
@app.after_request
def after_request(response):
    """添加安全响应头"""
    # 权限策略：允许必要的功能（解决浏览器扩展的权限策略错误）
    # 注意：这个错误通常来自浏览器扩展，不影响插件功能
    response.headers['Permissions-Policy'] = (
        'geolocation=*, '
        'microphone=*, '
        'camera=*, '
        'fullscreen=*, '
        'payment=*, '
        'usb=*, '
        'clipboard-read=*, '
        'clipboard-write=*'
    )
    # 内容安全策略（允许飞书 SDK 和必要的资源加载）
    response.headers['Content-Security-Policy'] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' "
        "https://lf1-cdn-tos.bytegoofy.com "
        "https://*.feishu.cn "
        "https://*.larkoffice.com "
        "data: blob:; "
        "frame-ancestors *;"
    )
    return response

# 全局变量：加载 SBERT 模型
model = None

def load_model():
    """加载 SBERT 模型"""
    global model
    if model is None:
        logger.info("正在加载 SBERT 模型...")
        # 使用中文 SBERT 模型，如果网络问题可以使用其他模型
        # 例如: 'paraphrase-multilingual-MiniLM-L12-v2' 或 'distiluse-base-multilingual-cased'
        try:
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("SBERT 模型加载成功")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            # 备用模型
            model = SentenceTransformer('distiluse-base-multilingual-cased')
            logger.info("使用备用 SBERT 模型")
    return model

@app.route('/sidebar.html', methods=['GET'])
def sidebar():
    """飞书插件入口页面"""
    response = send_from_directory('.', 'sidebar.html')
    # 允许在 iframe 中加载（飞书插件需要）
    # 注意：X-Frame-Options 不支持 ALLOWALL，使用 Content-Security-Policy 的 frame-ancestors
    return response

@app.route('/styles.css', methods=['GET'])
def styles():
    """样式文件"""
    response = send_from_directory('.', 'styles.css', mimetype='text/css')
    # 允许跨域访问
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/sidebar.js', methods=['GET'])
def sidebar_js():
    """JavaScript 文件"""
    response = send_from_directory('.', 'sidebar.js', mimetype='application/javascript')
    # 允许跨域访问
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/', methods=['GET'])
def index():
    """根路径，返回本地分析工具页面"""
    # 优先返回本地分析工具
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    
    # 否则返回 API 信息
    return jsonify({
        'service': '类目内聚度分析服务',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'calculate': '/api/calculate-cohesion',
            'local_tool': '/index.html (本地分析工具)'
        },
        'status': 'running',
        'usage': '访问 http://localhost:5000/ 使用本地分析工具'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'ok', 'message': '服务运行正常'})

@app.route('/api/calculate-cohesion', methods=['POST'])
def calculate_cohesion():
    """
    计算类目内聚度指标
    
    请求体:
    {
        "category": "类目词",
        "items": ["词语1", "词语2", ...],
        "aggregation_method": "mean" 或 "variance" 或 "median"
    }
    
    返回:
    {
        "cohesion_score": 0.85,
        "mean_score": 0.85,
        "variance": 0.02 (如果 method 是 variance),
        "similarities": [0.9, 0.8, 0.85, ...],
        "method": "mean"
    }
    """
    try:
        data = request.json
        
        # 验证输入
        if not data:
            return jsonify({'error': '请求体为空'}), 400
        
        category = data.get('category', '').strip()
        items = data.get('items', [])
        aggregation_method = data.get('aggregation_method', 'mean')
        
        if not category:
            return jsonify({'error': '类目词不能为空'}), 400
        
        if not items or len(items) == 0:
            return jsonify({'error': '普通词列表不能为空'}), 400
        
        if aggregation_method not in ['mean', 'median', 'variance']:
            return jsonify({'error': '聚合方法必须是 mean、median 或 variance'}), 400
        
        # 加载模型
        model = load_model()
        
        # 向量化：将类目词和所有普通词转换为向量
        logger.info(f"正在向量化: 类目词='{category}', 普通词数量={len(items)}")
        
        # 准备所有文本（类目词 + 普通词）
        all_texts = [category] + items
        
        # 批量编码，提高效率
        embeddings = model.encode(all_texts, convert_to_numpy=True, show_progress_bar=False)
        
        category_embedding = embeddings[0]
        item_embeddings = embeddings[1:]
        
        # 计算相似度：使用余弦相似度（1 - 余弦距离）
        similarities = []
        for item_embedding in item_embeddings:
            # 计算余弦相似度（值域: -1 到 1，越接近1越相似）
            # 使用 1 - cosine_distance 得到相似度
            cosine_distance = cosine(category_embedding, item_embedding)
            similarity = 1 - cosine_distance
            similarities.append(float(similarity))
        
        # 计算平均值
        mean_score = float(np.mean(similarities))
        
        # 计算方差（如果请求方差）
        variance = None
        if aggregation_method == 'variance':
            variance = float(np.var(similarities))
            cohesion_score = variance
        elif aggregation_method == 'mean':
            cohesion_score = mean_score
        else:  # median
            cohesion_score = float(np.median(similarities))
        
        logger.info(f"计算完成: 平均值={mean_score:.4f}, 方法={aggregation_method}")
        
        result = {
            'cohesion_score': cohesion_score,
            'mean_score': mean_score,
            'similarities': similarities,
            'method': aggregation_method,
            'category': category,
            'items_count': len(items)
        }
        
        if variance is not None:
            result['variance'] = variance
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"计算错误: {str(e)}", exc_info=True)
        return jsonify({'error': f'计算失败: {str(e)}'}), 500

@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({
        'error': 'Not Found',
        'message': '请求的 URL 不存在',
        'available_endpoints': {
            'root': '/',
            'health': '/api/health',
            'calculate': '/api/calculate-cohesion (POST)'
        }
    }), 404

if __name__ == '__main__':
    # 预加载模型
    logger.info("启动服务，预加载模型...")
    load_model()
    
    # 启动 Flask 服务
    logger.info("服务启动在 http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

