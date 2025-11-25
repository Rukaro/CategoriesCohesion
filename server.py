"""
类目内聚度分析服务
使用SentenceTransformer模型计算类目内聚度指标
使用sentence-transformers和余弦相似度计算单词关联度
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import logging
import os
from sentence_transformers import SentenceTransformer, util

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# 静默 transformers 警告
logging.getLogger("transformers").setLevel(logging.ERROR)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # 允许跨域请求

# 添加全局响应头处理
@app.after_request
def after_request(response):
    """添加安全响应头"""
    # 权限策略：允许必要的功能
    response.headers['Permissions-Policy'] = (
        'geolocation=*, '
        'microphone=*, '
        'camera=*, '
        'fullscreen=*, '
        'payment=*, '
        'usb=*, '
        'clipboard-read=*, '
        'clipboard-write=*, '
        'clipboard-read=(self "*"), '
        'clipboard-write=(self "*")'
    )
    # 内容安全策略
    response.headers['Content-Security-Policy'] = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' "
        "data: blob:; "
        "frame-ancestors *;"
    )
    return response

# 全局变量：SentenceTransformer模型
model = None

def load_model():
    """加载SentenceTransformer模型"""
    global model
    if model is None:
        logger.info("正在加载SentenceTransformer模型...")
        try:
            # 优先尝试从环境变量获取模型名称
            model_name = os.getenv('SENTENCE_MODEL_NAME', 'all-MiniLM-L6-v2')
            
            logger.info(f"使用模型: {model_name}")
            logger.info("首次运行需要下载模型，可能需要几分钟...")
            model = SentenceTransformer(model_name)
            logger.info("SentenceTransformer模型加载成功")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            logger.error("请确保已安装 sentence-transformers 库，并且网络连接正常以下载模型")
            raise
    return model

def get_association_score(word1, word2):
    """
    计算两个单词的关联度分数
    
    Args:
        word1: 第一个单词
        word2: 第二个单词
    
    Returns:
        float: 关联度分数（0到1之间，越接近1表示越相关）
    """
    if model is None:
        load_model()
    
    try:
        # 生成向量
        embedding1 = model.encode(word1, convert_to_tensor=True)
        embedding2 = model.encode(word2, convert_to_tensor=True)
        
        # 计算余弦相似度
        score = util.pytorch_cos_sim(embedding1, embedding2)
        return score.item()
    except Exception as e:
        logger.error(f"计算关联度失败: {e}")
        return 0.0

def calculate_complex_association(category, item):
    """
    使用SentenceTransformer模型计算类目词和子词的关联度
    使用余弦相似度计算两个单词的关联度分数
    
    Args:
        category: 类目词
        item: 子词
    
    Returns:
        (相似度分数, 描述句子, 关联类型)
    """
    if model is None:
        load_model()
    
    try:
        # 计算关联度分数
        score = get_association_score(category, item)
        
        logger.debug(f"SentenceTransformer相似度: {category} <-> {item} = {score:.4f}")
        
        return float(score), f"{category} is associated with {item}.", "关联"
        
    except Exception as e:
        logger.error(f"计算关联度失败: {e}")
        return 0.0, f"{category} is associated with {item}.", "未知"

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
        
        # 加载 NLI 模型
        load_model()
        
        # 使用 NLI 模型计算相似度（多关系模板匹配）
        logger.info(f"正在计算相似度: 类目词='{category}', 普通词数量={len(items)}")
        
        # 计算每个子词与类目词的关联度
        similarities = []
        relation_types = []  # 存储每个子词的关联类型
        for item in items:
            similarity, _, relation_type = calculate_complex_association(category, item)
            similarities.append(similarity)
            relation_types.append(relation_type)
        
        if not similarities or len(similarities) == 0:
            return jsonify({'error': '无法计算相似度，请检查输入文本'}), 400
        
        logger.info(f"计算完成: 类目词='{category}', 子词数量={len(items)}")
        
        result = {
            'similarities': similarities,
            'relation_types': relation_types,  # 关联类型列表
            'category': category,
            'items': items,  # 返回子词列表
            'items_count': len(items)
        }
        
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

