#!/usr/bin/env python3
"""
简化的本地Claude CLI修复验证测试
Simplified test for local Claude CLI fix verification
"""

import sys
import os
import time

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_local_claude_function():
    """直接测试本地Claude CLI函数"""
    print("=== 测试本地Claude CLI核心函数 ===")
    
    try:
        from openai_api.openai import try_local_claude_cli
        
        # 简单测试
        test_prompt = "请回答：本地Claude测试成功"
        print(f"📝 测试提示: {test_prompt}")
        
        start_time = time.time()
        result = try_local_claude_cli(test_prompt, timeout=30)
        duration = time.time() - start_time
        
        if result:
            print(f"✅ 本地Claude CLI调用成功")
            print(f"⏱️  响应时间: {duration:.2f}秒")
            print(f"📋 返回内容: {result[:150]}{'...' if len(result) > 150 else ''}")
            return True
        else:
            print("❌ 本地Claude CLI调用失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_api_with_fallback():
    """测试API函数的回退机制"""
    print("\n=== 测试API回退机制 ===")
    
    try:
        from openai_api.openai import ask_openai_common
        
        test_prompt = "测试API回退：请回答'回退机制正常'"
        print(f"📝 测试提示: {test_prompt}")
        
        start_time = time.time()
        result = ask_openai_common(test_prompt)
        duration = time.time() - start_time
        
        print(f"⏱️  总响应时间: {duration:.2f}秒")
        print(f"📋 返回内容: {result[:150]}{'...' if len(result) > 150 else ''}")
        
        return len(result) > 0
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_vulnerability_detection():
    """测试漏洞检测函数的CLI回退"""
    print("\n=== 测试漏洞检测CLI回退 ===")
    
    try:
        from openai_api.openai import detect_vulnerabilities
        
        # 简单的漏洞检测测试
        test_code = """
        function transfer(uint256 amount) public {
            balances[msg.sender] = balances[msg.sender] - amount;
            balances[to] += amount;
        }
        """
        
        test_prompt = f"请简要分析此代码安全问题：{test_code}"
        print(f"📝 测试漏洞检测...")
        
        start_time = time.time()
        result = detect_vulnerabilities(test_prompt)
        duration = time.time() - start_time
        
        print(f"⏱️  检测时间: {duration:.2f}秒")
        print(f"📋 检测结果: {result[:200]}{'...' if len(result) > 200 else ''}")
        
        return len(result) > 50  # 期望有详细的安全分析
        
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_concurrent_calls():
    """测试并发调用性能"""
    print("\n=== 测试并发调用性能 ===")
    
    import threading
    import concurrent.futures
    
    try:
        from openai_api.openai import try_local_claude_cli
        
        def single_call(i):
            prompt = f"简单测试{i}: 请回答数字{i}"
            start = time.time()
            result = try_local_claude_cli(prompt, timeout=20)
            duration = time.time() - start
            return i, len(result) > 0, duration
        
        print("📝 执行3个并发调用...")
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(single_call, i) for i in range(1, 4)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        success_count = sum(1 for _, success, _ in results if success)
        
        print(f"⏱️  总耗时: {total_time:.2f}秒")
        print(f"📊 成功率: {success_count}/3")
        
        for i, success, duration in sorted(results):
            status = "✅" if success else "❌"
            print(f"   {status} 调用{i}: {duration:.2f}秒")
        
        return success_count >= 2  # 至少2个成功
        
    except Exception as e:
        print(f"❌ 并发测试异常: {e}")
        return False

def test_error_handling():
    """测试错误处理机制"""
    print("\n=== 测试错误处理 ===")
    
    try:
        from openai_api.openai import try_local_claude_cli
        
        # 测试超时处理
        print("📝 测试超时处理（3秒超时）...")
        start_time = time.time()
        result = try_local_claude_cli("请写一篇1000字的文章", timeout=3)
        duration = time.time() - start_time
        
        if result is None and duration <= 5:
            print(f"✅ 超时处理正常，耗时: {duration:.2f}秒")
            return True
        elif result:
            print(f"✅ 快速响应成功，耗时: {duration:.2f}秒")
            return True
        else:
            print(f"❌ 超时处理异常")
            return False
            
    except Exception as e:
        print(f"❌ 错误处理测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🔧 本地Claude CLI修复验证测试")
    print("=" * 60)
    
    # 测试项目列表
    tests = [
        ("本地Claude核心函数", test_local_claude_function),
        ("API回退机制", test_api_with_fallback),
        ("漏洞检测CLI回退", test_vulnerability_detection),
        ("并发调用性能", test_concurrent_calls),
        ("错误处理机制", test_error_handling),
    ]
    
    results = []
    total_start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n🧪 执行测试: {test_name}")
        print("-" * 40)
        
        try:
            test_start = time.time()
            success = test_func()
            test_duration = time.time() - test_start
            
            results.append((test_name, success, test_duration))
            status = "✅ 通过" if success else "❌ 失败"
            print(f"📊 测试结果: {status} (耗时: {test_duration:.2f}秒)")
            
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
            results.append((test_name, False, 0))
    
    total_duration = time.time() - total_start_time
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, duration in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name:<25} ({duration:>5.2f}秒)")
    
    print("-" * 60)
    print(f"🎯 通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"⏱️  总耗时: {total_duration:.2f}秒")
    
    if passed == total:
        print("🎉 所有测试通过！本地Claude CLI修复成功！")
        return 0
    elif passed >= total * 0.8:
        print("⚠️ 大部分测试通过，修复基本成功")
        return 0
    else:
        print("❌ 多项测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())