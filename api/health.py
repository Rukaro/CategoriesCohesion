"""
Vercel Serverless Function - 健康检查
"""
import json

def handler(req):
    """健康检查接口"""
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    if req.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'status': 'ok',
            'message': '服务运行正常'
        })
    }

