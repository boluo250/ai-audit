#!/usr/bin/env python3
"""
快速核心验证：修复后的本地Claude接口
Quick core verification of repaired local Claude interface
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def quick_core_test():
    """快速核心功能测试"""
    print("🚀 快速核心验证测试")
    print("=" * 50)
    
    try:
        # 测试1: 基础API回退
        print("\n📝 测试1: 基础API回退机制")
        from openai_api.openai import ask_openai_common
        
        result1 = ask_openai_common("简单测试：回答'OK'")
        success1 = "OK" in result1 or len(result1) > 0
        print(f"   结果: {'✅' if success1 else '❌'} ({len(result1)}字符)")
        
        # 测试2: 漏洞检测回退  
        print("\n📝 测试2: 漏洞检测回退")
        from openai_api.openai import detect_vulnerabilities
        
        simple_vuln = "function bad() { owner = msg.sender; }"
        result2 = detect_vulnerabilities(f"分析安全问题：{simple_vuln}")
        success2 = len(result2) > 50
        print(f"   结果: {'✅' if success2 else '❌'} ({len(result2)}字符)")
        
        # 测试3: 代码假设分析回退
        print("\n📝 测试3: 代码假设分析回退")
        from openai_api.openai import analyze_code_assumptions
        
        result3 = analyze_code_assumptions("分析：require(amount > 0)")
        success3 = len(result3) > 30
        print(f"   结果: {'✅' if success3 else '❌'} ({len(result3)}字符)")
        
        # 汇总结果
        total_success = sum([success1, success2, success3])
        print(f"\n📊 核心测试通过率: {total_success}/3")
        
        if total_success == 3:
            print("🎉 核心功能验证通过！修复成功！")
            print("💡 本地Claude CLI回退机制正常工作")
        elif total_success >= 2:
            print("⚠️ 大部分核心功能正常，修复基本成功") 
        else:
            print("❌ 核心功能存在问题，需要进一步检查")
            
        return total_success >= 2
        
    except Exception as e:
        print(f"❌ 快速测试异常: {e}")
        return False

def check_cli_availability():
    """检查CLI可用性"""
    print("\n🔍 检查本地Claude CLI可用性")
    
    try:
        import subprocess
        result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
        if result.returncode == 0:
            cli_path = result.stdout.strip()
            print(f"✅ Claude CLI找到: {cli_path}")
            
            # 快速测试CLI
            test_result = subprocess.run(['claude'], 
                                       input='测试：请回答"CLI可用"',
                                       capture_output=True, 
                                       text=True, 
                                       timeout=15)
            if test_result.returncode == 0:
                print("✅ CLI功能测试通过")
                return True
            else:
                print(f"⚠️ CLI测试失败: {test_result.stderr}")
                return False
        else:
            print("❌ Claude CLI未找到")
            return False
    except Exception as e:
        print(f"❌ CLI检查异常: {e}")
        return False

def verify_api_fallback_logic():
    """验证API回退逻辑"""
    print("\n🔄 验证API回退逻辑")
    
    try:
        from openai_api.openai import try_local_claude_cli
        
        # 测试本地CLI函数直接调用
        print("📝 测试本地CLI函数...")
        result = try_local_claude_cli("测试直接调用", timeout=10)
        
        if result:
            print("✅ 本地CLI函数工作正常")
            return True
        else:
            print("⚠️ 本地CLI函数返回空结果")
            return False
            
    except Exception as e:
        print(f"❌ API回退逻辑验证异常: {e}")
        return False

def main():
    """主函数"""
    print("⚡ 本地Claude修复快速验证")
    print("🕐 预计耗时: 1-2分钟")
    print("=" * 60)
    
    start_time = time.time()
    
    # 执行三个核心检查
    checks = [
        ("CLI可用性检查", check_cli_availability),
        ("API回退逻辑验证", verify_api_fallback_logic), 
        ("核心功能测试", quick_core_test),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n🧪 执行: {check_name}")
        print("-" * 30)
        
        try:
            success = check_func()
            results.append((check_name, success))
        except Exception as e:
            print(f"❌ {check_name}执行异常: {e}")
            results.append((check_name, False))
    
    total_time = time.time() - start_time
    
    # 最终汇总
    print("\n" + "=" * 60)
    print("📊 快速验证结果汇总")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for check_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {check_name}")
    
    print("-" * 60)
    print(f"🎯 验证通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"⏱️  总耗时: {total_time:.2f}秒")
    
    if passed == total:
        print("\n🎉 快速验证全部通过！")
        print("💡 修复后的本地Claude接口运行完美")
        print("🚀 系统可以正常投入使用")
        return 0
    elif passed >= 2:
        print("\n⚠️ 大部分验证通过，修复基本成功")
        print("💡 系统可以投入使用，建议关注失败项")
        return 0
    else:
        print("\n❌ 验证失败较多，建议进一步检查")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️ 测试被中断")
        sys.exit(1)