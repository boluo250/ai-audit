#!/usr/bin/env python3
"""
测试DeepSeek API配置的简单脚本
从 .env 文件加载配置并进行实际API调用测试
"""
import sys
import os

# 添加项目路径
sys.path.append('/home/ubuntu/finite-monkey-engine/src')

def load_env_file():
    """从 .env 文件加载环境变量"""
    env_path = '/home/ubuntu/finite-monkey-engine/.env'
    if not os.path.exists(env_path):
        print("❌ .env 文件不存在")
        return False
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 去除引号
                    value = value.strip('"\'')
                    os.environ[key] = value
        print("✅ 成功加载 .env 文件")
        return True
    except Exception as e:
        print(f"❌ 加载 .env 文件失败: {e}")
        return False

def test_deepseek_integration():
    """测试DeepSeek API集成"""
    print("🧪 测试DeepSeek API集成...")
    
    # 加载环境变量
    if not load_env_file():
        return False
    
    from openai_api.openai import ask_openai_common, ask_deepseek, get_model
    
    # 检查环境变量
    api_key = os.environ.get('OPENAI_API_KEY')
    api_base = os.environ.get('OPENAI_API_BASE', 'api.deepseek.com')
    
    print(f"📍 API Base: {api_base}")
    print(f"🔑 API Key: {'已设置 (' + api_key[:10] + '...)' if api_key else '未设置'}")
    print(f"🎯 默认模型: {get_model('openai_general')}")
    
    if not api_key:
        print("⚠️ 请在 .env 文件中设置 OPENAI_API_KEY")
        return False
    
    # 测试简单请求
    test_prompt = "请简单回答：你好，这是一个测试连接"
    
    print("\n🚀 测试 ask_deepseek 函数...")
    try:
        result = ask_deepseek(test_prompt)
        if result:
            print(f"✅ ask_deepseek 成功:")
            print(f"   响应: {result[:200]}{'...' if len(result) > 200 else ''}")
        else:
            print("❌ ask_deepseek 返回空结果")
            return False
    except Exception as e:
        print(f"❌ ask_deepseek 异常: {e}")
        return False
    
    print("\n🚀 测试 ask_openai_common 函数...")
    try:
        result = ask_openai_common(test_prompt)
        if result:
            print(f"✅ ask_openai_common 成功:")
            print(f"   响应: {result[:200]}{'...' if len(result) > 200 else ''}")
        else:
            print("❌ ask_openai_common 返回空结果")
            return False
    except Exception as e:
        print(f"❌ ask_openai_common 异常: {e}")
        return False
    
    print("\n✅ 所有测试通过！DeepSeek API配置成功")
    return True

if __name__ == "__main__":
    success = test_deepseek_integration()
    sys.exit(0 if success else 1)