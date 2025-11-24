"""
测试 API 接口
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_endpoint(url, method='GET', data=None):
    """测试接口"""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, json=data, timeout=30)
        
        print(f"\n{'='*60}")
        print(f"测试: {method} {url}")
        print(f"状态码: {response.status_code}")
        
        try:
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        except:
            print(f"响应: {response.text[:200]}")
        
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 无法连接到服务器 {url}")
        print("请确保服务正在运行: python server.py")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return False

def main():
    print("开始测试 API 接口...")
    
    # 测试根路径
    test_endpoint(f"{BASE_URL}/")
    
    # 测试健康检查
    test_endpoint(f"{BASE_URL}/api/health")
    
    # 测试计算接口
    test_data = {
        "category": "水果",
        "items": ["苹果", "香蕉", "橙子", "葡萄"],
        "aggregation_method": "mean"
    }
    test_endpoint(f"{BASE_URL}/api/calculate-cohesion", method='POST', data=test_data)
    
    # 测试不存在的路径
    print(f"\n{'='*60}")
    print("测试不存在的路径 (应该返回 404):")
    test_endpoint(f"{BASE_URL}/api/test")
    
    print(f"\n{'='*60}")
    print("测试完成！")

if __name__ == '__main__':
    main()

