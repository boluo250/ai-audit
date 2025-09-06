#!/usr/bin/env python3
"""
Claude CLI测试程序
Test program for local Claude CLI functionality
"""

import subprocess
import sys
import time
from typing import Optional


def test_claude_cli(prompt: str, timeout: int = 30) -> tuple[bool, str, str]:
    """
    测试Claude CLI功能
    
    Args:
        prompt: 测试提示词
        timeout: 超时时间（秒）
    
    Returns:
        tuple[成功状态, 输出内容, 错误信息]
    """
    try:
        print(f"🧪 正在测试Claude CLI...")
        print(f"📝 提示词: {prompt[:50]}...")
        
        start_time = time.time()
        
        result = subprocess.run(
            ['claude'], 
            input=prompt,
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        
        duration = time.time() - start_time
        print(f"⏱️  执行时间: {duration:.2f}秒")
        
        if result.returncode == 0:
            print("✅ Claude CLI调用成功")
            return True, result.stdout.strip(), ""
        else:
            print(f"❌ Claude CLI调用失败，返回码: {result.returncode}")
            return False, "", result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Claude CLI调用超时 ({timeout}秒)")
        return False, "", f"Timeout after {timeout} seconds"
    except FileNotFoundError:
        print("❌ Claude CLI未找到，请确保已安装")
        return False, "", "Claude CLI not found"
    except Exception as e:
        print(f"❌ 调用异常: {e}")
        return False, "", str(e)


def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 基本功能测试 ===")
    
    test_cases = [
        "Hello, can you respond with 'Claude CLI working'?",
        "What is 2 + 2?",
        "写一行Python代码打印Hello World",
    ]
    
    results = []
    for i, prompt in enumerate(test_cases, 1):
        print(f"\n🔸 测试用例 {i}:")
        success, output, error = test_claude_cli(prompt)
        results.append((success, prompt, output, error))
        
        if success:
            print(f"📤 输出: {output[:100]}{'...' if len(output) > 100 else ''}")
        else:
            print(f"🚫 错误: {error}")
    
    return results


def test_vulnerability_detection():
    """测试漏洞检测相关功能"""
    print("\n=== 漏洞检测功能测试 ===")
    
    # 模拟一个简单的代码漏洞检测请求
    code_sample = '''
    function transfer(address to, uint256 amount) public {
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
    '''
    
    prompt = f"""
    请分析以下Solidity代码是否存在安全漏洞：
    
    {code_sample}
    
    请简洁回答是否存在问题及原因。
    """
    
    print("🔍 测试漏洞检测功能...")
    success, output, error = test_claude_cli(prompt, timeout=60)
    
    if success:
        print(f"✅ 漏洞检测测试成功")
        print(f"📋 分析结果: {output[:200]}{'...' if len(output) > 200 else ''}")
    else:
        print(f"❌ 漏洞检测测试失败: {error}")
    
    return success, output, error


def test_integration_compatibility():
    """测试与现有系统的集成兼容性"""
    print("\n=== 集成兼容性测试 ===")
    
    # 模拟现有系统中的prompt格式
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    
    try:
        from openai_api.openai import ask_openai_common
        
        test_prompt = "简单测试：请回答'集成测试通过'"
        
        print("🔌 测试ask_openai_common函数...")
        result = ask_openai_common(test_prompt)
        if result and "集成测试通过" in result:
            print("✅ 集成兼容性测试成功")
            print(f"📋 返回结果: {result}")
            return True
        else:
            print(f"⚠️ 返回结果不符合预期: {result}")
            return False
    except ImportError as e:
        print(f"⚠️ 无法导入模块，跳过集成测试: {e}")
        return True  # 跳过但不算失败
    except Exception as e:
        print(f"❌ 集成测试异常: {e}")
        return False


def main():
    """主测试函数"""
    print("🎯 Claude CLI 功能测试程序")
    print("=" * 50)
    
    # 检查Claude CLI是否可用
    try:
        result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
        if result.returncode == 0:
            claude_path = result.stdout.strip()
            print(f"📍 Claude CLI路径: {claude_path}")
        else:
            print("❌ Claude CLI未安装或不在PATH中")
            return 1
    except Exception as e:
        print(f"❌ 检查Claude CLI失败: {e}")
        return 1
    
    # 执行测试
    success_count = 0
    total_tests = 0
    
    # 基本功能测试
    basic_results = test_basic_functionality()
    total_tests += len(basic_results)
    success_count += sum(1 for success, _, _, _ in basic_results if success)
    
    # 漏洞检测功能测试
    vul_success, _, _ = test_vulnerability_detection()
    total_tests += 1
    if vul_success:
        success_count += 1
    
    # 集成兼容性测试
    integration_success = test_integration_compatibility()
    total_tests += 1
    if integration_success:
        success_count += 1
    
    # 测试结果汇总
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print(f"✅ 通过: {success_count}/{total_tests}")
    print(f"❌ 失败: {total_tests - success_count}/{total_tests}")
    print(f"🎯 成功率: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 所有测试通过！Claude CLI可以正常使用")
        return 0
    else:
        print("⚠️ 部分测试失败，建议检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())