"""
飞书边栏插件后端服务
使用 NLI 模型的多关系模板匹配计算类目内聚度指标
支持分类、场景、构成、近义词、特征、状态等多种关系类型
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from transformers import pipeline
import numpy as np
import logging
import os
import nltk
from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize

# 下载必要的NLTK数据
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

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
        'clipboard-write=*, '
        'clipboard-read=(self "*"), '
        'clipboard-write=(self "*")'
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

# 全局变量：NLI 模型
classifier = None

def load_model():
    """加载 NLI 模型（Bart-Large-MNLI）"""
    global classifier
    if classifier is None:
        logger.info("正在加载 NLI 模型...")
        try:
            # 优先尝试从环境变量获取模型名称
            model_name = os.getenv('NLI_MODEL_NAME', 'facebook/bart-large-mnli')
            
            logger.info(f"使用模型: {model_name}")
            classifier = pipeline(
                "zero-shot-classification",
                model=model_name,
                device=-1  # -1 表示使用 CPU，如果有 GPU 可以改为 0
            )
            logger.info("NLI 模型加载成功")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            logger.error("请确保已安装 transformers 库，并且网络连接正常以下载模型")
            raise
    return classifier

def verify_synonym_with_wordnet(word1, word2):
    """
    使用WordNet验证两个词是否是同义词
    
    Args:
        word1: 第一个词
        word2: 第二个词
    
    Returns:
        bool: 如果是同义词返回True，否则返回False
    """
    try:
        # 获取两个词的所有synset（同义词集）
        synsets1 = wn.synsets(word1.lower())
        synsets2 = wn.synsets(word2.lower())
        
        if not synsets1 or not synsets2:
            return False
        
        # 检查是否有共同的synset
        for syn1 in synsets1:
            for syn2 in synsets2:
                # 如果两个词在同一个synset中，它们是同义词
                if syn1 == syn2:
                    return True
                # 检查是否是直接同义词（lemma名称相同）
                if syn1.name().split('.')[0] == syn2.name().split('.')[0]:
                    return True
        
        # 检查是否有相似的含义（通过路径相似度）
        max_similarity = 0.0
        for syn1 in synsets1:
            for syn2 in synsets2:
                try:
                    # 计算路径相似度
                    similarity = syn1.path_similarity(syn2)
                    if similarity is not None:
                        max_similarity = max(max_similarity, similarity)
                except:
                    continue
        
        # 如果路径相似度很高（>=0.8），认为是同义词
        if max_similarity >= 0.8:
            return True
        
        # 检查是否是直接的同义词关系（通过lemma）
        lemmas1 = set()
        lemmas2 = set()
        for syn in synsets1:
            lemmas1.update([lemma.name().lower() for lemma in syn.lemmas()])
        for syn in synsets2:
            lemmas2.update([lemma.name().lower() for lemma in syn.lemmas()])
        
        # 如果两个词的lemma有交集，认为是同义词
        if lemmas1.intersection(lemmas2):
            return True
        
        return False
    except Exception as e:
        logger.debug(f"WordNet验证失败: {e}")
        return False

def calculate_complex_association(category, item):
    """
    使用 NLI 模型计算类目词和子词的关联度
    两步验证机制：
    1. 第一步：广撒网，先看有没有关系（高召回率）
    2. 第二步：照妖镜，过滤主观评价
    
    Args:
        category: 类目词
        item: 子词
    
    Returns:
        (最大相似度分数, 最佳匹配模板, 关联类型)
    """
    if classifier is None:
        load_model()
    
    # ======================================================
    # 第一步：简单关联检测
    # ======================================================
    # 只使用一个模板："{} is associated with {}."
    template = "{} is associated with {}."
    
    max_assoc_score = 0.0
    best_sentence = ""
    best_relation_type = "关联"
    
    # 双向测试：测试正向和反向
    inputs = [(item, category), (category, item)]
    
    for subject, predicate in inputs:
        try:
            # 构造完整句子
            sentence = template.replace('{}', subject, 1).replace('{}', predicate, 1)
            
            # 使用 true/false 检测关联性
            res = classifier(sentence, ["true", "false"])
            
            if res and 'scores' in res and 'labels' in res:
                score = res['scores'][0]
                label = res['labels'][0]
                
                if label == "true" and score > max_assoc_score:
                    max_assoc_score = score
                    best_sentence = sentence
                    best_relation_type = "关联"
                    
        except Exception as e:
            logger.debug(f"关联检测失败: {e}")
            continue
    
    # 直接返回第一步检测的分数
    return float(max_assoc_score), best_sentence, best_relation_type

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

