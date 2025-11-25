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
    # 第一步：快速检测关系（优化版）
    # ======================================================
    # 使用最精简的模板，减少计算时间
    association_templates = [
        ("{} is a type of {}.", "分类"),
        ("{} is physically {}.", "特征"),
        ("{} can be described as {}.", "状态"),
    ]
    
    max_assoc_score = 0.0
    best_sentence = ""
    best_relation_type = "未知"
    early_exit_threshold = 0.95  # 只有非常高的分数才提前退出
    
    # 双向测试：先测试正向，如果分数不高再测试反向
    inputs = [(item, category), (category, item)]
    
    for subject, predicate in inputs:
        for template_info in association_templates:
            template, relation_type = template_info
            try:
                # 构造完整句子
                placeholder_count = template.count('{}')
                
                if placeholder_count == 2:
                    sentence = template.replace('{}', subject, 1).replace('{}', predicate, 1)
                elif placeholder_count == 1:
                    sentence = template.replace('{}', subject, 1)
                else:
                    continue
                
                # 快速检测：使用 true/false
                res = classifier(sentence, ["true", "false"])
                
                if res and 'scores' in res and 'labels' in res:
                    score = res['scores'][0]
                    label = res['labels'][0]
                    
                    if label == "true" and score > max_assoc_score:
                        max_assoc_score = score
                        best_sentence = sentence
                        best_relation_type = relation_type
                        
                        # 早期退出：只有分数非常高时才提前退出
                        if max_assoc_score >= early_exit_threshold:
                            break
                        
            except Exception as e:
                logger.debug(f"模板计算失败 ({template}): {e}")
                continue
        
        # 如果已经找到非常高的分数，跳出输入循环
        if max_assoc_score >= early_exit_threshold:
            break
    
    # ======================================================
    # 第二步：主观性过滤（仅在分数较高时执行）
    # ======================================================
    # 只在分数 >= 0.7 时才进行主观性检测，避免不必要的计算
    if max_assoc_score >= 0.7:
        try:
            labels = ["objective physical fact", "subjective personal opinion"]
            res = classifier(best_sentence, labels)
            
            if res and 'scores' in res and 'labels' in res:
                fact_score = res['scores'][res['labels'].index("objective physical fact")]
                opinion_score = res['scores'][res['labels'].index("subjective personal opinion")]
                
                is_subjective = opinion_score > fact_score
                
                if is_subjective:
                    # 惩罚分数
                    final_score = 0.1
                    best_relation_type = "主观评价"
                else:
                    final_score = max_assoc_score
            else:
                final_score = max_assoc_score
                
        except Exception as e:
            logger.debug(f"主观性检测失败: {e}")
            final_score = max_assoc_score
    else:
        # 分数不够高，跳过主观性检测
        final_score = max_assoc_score
    
    return float(final_score), best_sentence, best_relation_type

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

