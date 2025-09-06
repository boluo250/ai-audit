#!/usr/bin/env python3
"""
测试修复后的API调用功能
Test repaired API calling functions
"""

import sys
import os

# 添加src路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_ask_openai_common():
    """测试通用OpenAI API调用"""
    print("=== 测试 ask_openai_common ===")
    
    try:
        from openai_api.openai import ask_openai_common
        
        test_prompt = "请回答：API修复测试通过"
        print(f"📝 测试提示: {test_prompt}")
        
        result = ask_openai_common(test_prompt)
        print(f"📋 返回结果: {result[:100]}{'...' if len(result) > 100 else ''}")
        
        return len(result) > 0 and "API修复测试通过" in result
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_detect_vulnerabilities():
    """测试漏洞检测功能"""
    print("\n=== 测试 detect_vulnerabilities ===")
    
    try:
        from openai_api.openai import detect_vulnerabilities
        
        # 使用简单的测试代码
        test_code = """
        function withdraw(uint amount) public {
            require(balances[msg.sender] >= amount);
            msg.sender.send(amount);
            balances[msg.sender] -= amount;
        }
        """
        
        test_prompt = f"请分析以下代码是否存在安全问题：{test_code}"
        print(f"📝 测试漏洞检测...")
        
        result = detect_vulnerabilities(test_prompt)
        print(f"📋 检测结果: {result[:150]}{'...' if len(result) > 150 else ''}")
        
        # 检查是否返回了有效结果
        return len(result) > 20  # 至少有一些分析内容
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_analyze_code_assumptions():
    """测试代码假设分析功能"""
    print("\n=== 测试 analyze_code_assumptions ===")
    
    try:
        from openai_api.openai import analyze_code_assumptions
        
        test_prompt = "请分析这段代码的假设：require(msg.value > 0)"
        print(f"📝 测试代码假设分析...")
        
        result = analyze_code_assumptions(test_prompt)
        print(f"📋 分析结果: {result[:150]}{'...' if len(result) > 150 else ''}")
        
        return len(result) > 20
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_model_config():
    """测试模型配置"""
    print("\n=== 测试模型配置 ===")
    
    try:
        from openai_api.openai import get_model
        
        # 测试几个关键模型配置
        models_to_test = [
            'vulnerability_detection',
            'code_assumptions_analysis', 
            'openai_general'
        ]
        
        success = True
        for model_key in models_to_test:
            model = get_model(model_key)
            print(f"📋 {model_key}: {model}")
            if not model:
                success = False
        
        return success
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🔧 API修复功能测试")
    print("=" * 50)
    
    # 执行所有测试
    tests = [
        ("模型配置", test_model_config),
        ("通用API调用", test_ask_openai_common),
        ("漏洞检测", test_detect_vulnerabilities),
        ("代码假设分析", test_analyze_code_assumptions),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 执行测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ 通过" if success else "❌ 失败"
            print(f"📊 结果: {status}")
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！API修复成功")
        return 0
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())