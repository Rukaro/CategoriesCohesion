from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
# 修改引用
from sentence_transformers import SentenceTransformer, util
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

model = None

def load_model():
    global model
    if model is None:
        logger.info("加载语义相似度模型 (Bi-Encoder)...")
        # 修改为 all-MiniLM-L6-v2
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        logger.info("模型加载完成")
    return model

@app.route('/api/calculate-cohesion', methods=['POST'])
def calculate_cohesion():
    try:
        data = request.json
        category = data.get('category', '').strip()
        items = data.get('items', [])
        
        current_model = load_model()
        
        # 1. 编码类目词
        cat_emb = current_model.encode(category, convert_to_tensor=True)
        
        # 2. 编码所有子词
        items_emb = current_model.encode(items, convert_to_tensor=True)
        
        # 3. 计算余弦相似度
        # util.cos_sim 返回的是一个矩阵，我们取第一行
        scores = util.cos_sim(cat_emb, items_emb)[0]
        
        # 4. 转为列表
        similarities = [float(s) for s in scores]
        
        # 5. 为了前端显示好看，可以把负数置为0（语义反义词）
        similarities = [max(0.0, s) for s in similarities]

        result = {
            'category': category,
            'items': items,
            'similarities': similarities,
            'relation_types': ["语义相关" if s > 0.3 else "弱相关" for s in similarities]
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    """根路径，返回本地分析工具页面"""
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
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

if __name__ == '__main__':
    load_model()
    app.run(host='0.0.0.0', port=5000, debug=True)