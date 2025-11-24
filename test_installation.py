"""
测试安装是否成功
"""
import sys

def test_imports():
    """测试关键依赖是否已安装"""
    print("正在测试依赖安装...")
    
    try:
        import flask
        print(f"✓ Flask {flask.__version__} 已安装")
    except ImportError as e:
        print(f"✗ Flask 未安装: {e}")
        return False
    
    try:
        import flask_cors
        print(f"✓ Flask-CORS 已安装")
    except ImportError as e:
        print(f"✗ Flask-CORS 未安装: {e}")
        return False
    
    try:
        import sentence_transformers
        print(f"✓ sentence-transformers 已安装")
    except ImportError as e:
        print(f"✗ sentence-transformers 未安装: {e}")
        return False
    
    try:
        import torch
        print(f"✓ PyTorch {torch.__version__} 已安装")
    except ImportError as e:
        print(f"✗ PyTorch 未安装: {e}")
        return False
    
    try:
        import numpy
        print(f"✓ NumPy {numpy.__version__} 已安装")
    except ImportError as e:
        print(f"✗ NumPy 未安装: {e}")
        return False
    
    try:
        import scipy
        print(f"✓ SciPy {scipy.__version__} 已安装")
    except ImportError as e:
        print(f"✗ SciPy 未安装: {e}")
        return False
    
    try:
        import transformers
        print(f"✓ Transformers {transformers.__version__} 已安装")
    except ImportError as e:
        print(f"✗ Transformers 未安装: {e}")
        return False
    
    print("\n所有依赖已成功安装！")
    return True

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)

