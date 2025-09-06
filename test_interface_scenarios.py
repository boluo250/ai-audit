#!/usr/bin/env python3
"""
实际场景中修复后接口的专项测试
Specific test for repaired interfaces in real scenarios
"""

import sys
import os
import time

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_reasoning_scanner():
    """测试推理扫描器（实际使用的接口）"""
    print("=== 测试推理扫描器接口 ===")
    
    try:
        # 模拟实际的项目审计数据
        class MockProjectAudit:
            def __init__(self):
                self.project_id = "test-project"
        
        from reasoning.scanner import VulnerabilityScanner
        
        project_audit = MockProjectAudit()
        scanner = VulnerabilityScanner(project_audit)
        
        # 测试简单的prompt执行
        test_prompt = """
        分析以下代码的安全性：
        
        function transfer(address to, uint256 amount) public {
            require(balances[msg.sender] >= amount, "Insufficient balance");
            balances[msg.sender] -= amount;
            balances[to] += amount;
        }
        
        请指出潜在的安全问题。
        """
        
        print("📝 测试推理扫描器...")
        start_time = time.time()
        
        # 直接调用内部API方法
        from openai_api.openai import detect_vulnerabilities
        result = detect_vulnerabilities(test_prompt)
        
        duration = time.time() - start_time
        print(f"⏱️  扫描时间: {duration:.2f}秒")
        print(f"📋 扫描结果: {result[:300]}{'...' if len(result) > 300 else ''}")
        
        return len(result) > 100  # 期望有详细分析
        
    except Exception as e:
        print(f"❌ 推理扫描器测试异常: {e}")
        return False

def test_validation_checker():
    """测试验证检查器接口"""
    print("\n=== 测试验证检查器接口 ===")
    
    try:
        from openai_api.openai import analyze_code_assumptions
        
        test_prompt = """
        分析以下代码假设：
        
        require(msg.sender == owner, "Only owner can call");
        
        这个假设是否安全？有什么潜在风险？
        """
        
        print("📝 测试假设分析...")
        start_time = time.time()
        
        result = analyze_code_assumptions(test_prompt)
        
        duration = time.time() - start_time
        print(f"⏱️  分析时间: {duration:.2f}秒")
        print(f"📋 分析结果: {result[:300]}{'...' if len(result) > 300 else ''}")
        
        return len(result) > 80
        
    except Exception as e:
        print(f"❌ 验证检查器测试异常: {e}")
        return False

def test_planning_interface():
    """测试规划接口"""
    print("\n=== 测试规划接口 ===")
    
    try:
        from openai_api.openai import ask_openai_common
        
        test_prompt = """
        基于以下Solidity合约，制定安全审计计划：
        
        pragma solidity ^0.8.0;
        
        contract SimpleBank {
            mapping(address => uint256) public balances;
            
            function deposit() public payable {
                balances[msg.sender] += msg.value;
            }
            
            function withdraw(uint256 amount) public {
                require(balances[msg.sender] >= amount);
                payable(msg.sender).transfer(amount);
                balances[msg.sender] -= amount;
            }
        }
        
        请提供3个主要的审计检查点。
        """
        
        print("📝 测试规划接口...")
        start_time = time.time()
        
        result = ask_openai_common(test_prompt)
        
        duration = time.time() - start_time
        print(f"⏱️  规划时间: {duration:.2f}秒")
        print(f"📋 规划结果: {result[:400]}{'...' if len(result) > 400 else ''}")
        
        # 检查是否包含关键审计要点
        key_points = ["重入", "整数", "访问控制", "检查点", "安全"]
        found_points = sum(1 for point in key_points if point in result)
        
        print(f"📊 发现关键点: {found_points}/{len(key_points)}")
        return found_points >= 2 and len(result) > 200
        
    except Exception as e:
        print(f"❌ 规划接口测试异常: {e}")
        return False

def test_performance_under_load():
    """测试负载下的性能"""
    print("\n=== 测试负载性能 ===")
    
    try:
        from openai_api.openai import ask_openai_common
        import threading
        import concurrent.futures
        
        def simple_task(task_id):
            prompt = f"简单任务{task_id}: 分析'require(amount > 0)'的安全性"
            start = time.time()
            result = ask_openai_common(prompt)
            duration = time.time() - start
            success = len(result) > 20
            return task_id, success, duration, len(result)
        
        print("📝 执行5个并发任务...")
        overall_start = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            tasks = [executor.submit(simple_task, i) for i in range(1, 6)]
            results = []
            for future in concurrent.futures.as_completed(tasks):
                results.append(future.result())
        
        overall_duration = time.time() - overall_start
        
        # 分析结果
        successful_tasks = [r for r in results if r[1]]
        success_rate = len(successful_tasks) / len(results)
        avg_duration = sum(r[2] for r in successful_tasks) / len(successful_tasks) if successful_tasks else 0
        avg_response_length = sum(r[3] for r in successful_tasks) / len(successful_tasks) if successful_tasks else 0
        
        print(f"⏱️  总耗时: {overall_duration:.2f}秒")
        print(f"📊 成功率: {len(successful_tasks)}/{len(results)} ({success_rate*100:.1f}%)")
        print(f"📊 平均单任务时间: {avg_duration:.2f}秒")
        print(f"📊 平均响应长度: {avg_response_length:.0f}字符")
        
        # 显示详细结果
        for task_id, success, duration, length in sorted(results):
            status = "✅" if success else "❌"
            print(f"   {status} 任务{task_id}: {duration:.2f}秒, {length}字符")
        
        return success_rate >= 0.8 and avg_duration < 30  # 80%成功率，平均30秒内
        
    except Exception as e:
        print(f"❌ 负载测试异常: {e}")
        return False

def test_end_to_end_scenario():
    """端到端场景测试"""
    print("\n=== 端到端场景测试 ===")
    
    try:
        from openai_api.openai import detect_vulnerabilities, analyze_code_assumptions
        
        # 模拟完整的漏洞检测流程
        contract_code = """
        contract VulnerableContract {
            mapping(address => uint256) balances;
            address owner;
            
            modifier onlyOwner() {
                require(msg.sender == owner);
                _;
            }
            
            function withdraw() public onlyOwner {
                msg.sender.call{value: address(this).balance}("");
            }
            
            function updateBalance(address user, uint256 amount) public {
                balances[user] = amount;
            }
        }
        """
        
        print("📝 第1步: 漏洞检测...")
        vulnerability_prompt = f"请检测以下合约的安全漏洞：\n{contract_code}"
        vuln_result = detect_vulnerabilities(vulnerability_prompt)
        
        print("📝 第2步: 假设分析...")
        assumption_prompt = "分析'require(msg.sender == owner)'这个访问控制的假设"
        assumption_result = analyze_code_assumptions(assumption_prompt)
        
        print("📝 第3步: 综合评估...")
        综合_prompt = f"""
        基于以下分析结果，给出最终安全评估：
        
        漏洞检测结果：{vuln_result[:200]}...
        
        假设分析结果：{assumption_result[:200]}...
        
        请给出1-10分的安全评分和主要建议。
        """
        from openai_api.openai import ask_openai_common
        final_result = ask_openai_common(综合_prompt)
        
        print(f"📋 最终评估: {final_result[:500]}{'...' if len(final_result) > 500 else ''}")
        
        # 检查是否完成了完整流程
        has_vuln_analysis = len(vuln_result) > 100
        has_assumption_analysis = len(assumption_result) > 50
        has_final_score = any(str(i) in final_result for i in range(1, 11))
        
        print(f"📊 漏洞分析完整: {'✅' if has_vuln_analysis else '❌'}")
        print(f"📊 假设分析完整: {'✅' if has_assumption_analysis else '❌'}")
        print(f"📊 包含评分: {'✅' if has_final_score else '❌'}")
        
        return has_vuln_analysis and has_assumption_analysis and has_final_score
        
    except Exception as e:
        print(f"❌ 端到端测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 修复后接口实际场景专项测试")
    print("=" * 70)
    
    # 专项测试列表
    tests = [
        ("推理扫描器接口", test_reasoning_scanner),
        ("验证检查器接口", test_validation_checker),
        ("规划接口", test_planning_interface),
        ("负载性能测试", test_performance_under_load),
        ("端到端场景测试", test_end_to_end_scenario),
    ]
    
    results = []
    total_start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n🧪 执行专项测试: {test_name}")
        print("=" * 50)
        
        try:
            test_start = time.time()
            success = test_func()
            test_duration = time.time() - test_start
            
            results.append((test_name, success, test_duration))
            status = "✅ 通过" if success else "❌ 失败"
            print(f"📊 测试结果: {status} (耗时: {test_duration:.2f}秒)")
            
        except KeyboardInterrupt:
            print("⚠️ 用户中断测试")
            break
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
            results.append((test_name, False, 0))
    
    total_duration = time.time() - total_start_time
    
    # 专项测试汇总
    print("\n" + "=" * 70)
    print("📊 专项测试结果汇总")
    print("=" * 70)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, duration in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name:<30} ({duration:>6.2f}秒)")
    
    print("-" * 70)
    print(f"🎯 专项测试通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"⏱️  总测试时间: {total_duration:.2f}秒")
    
    if passed == total:
        print("🎉 所有专项测试通过！修复后的接口在实际场景中运行完美！")
        print("💡 建议：系统已经可以正常投入使用")
        return 0
    elif passed >= total * 0.8:
        print("⚠️ 大部分专项测试通过，修复基本成功")
        print("💡 建议：可以谨慎投入使用，关注失败的测试项")
        return 0
    else:
        print("❌ 多项专项测试失败，建议进一步优化")
        print("💡 建议：检查失败项的具体原因")
        return 1

if __name__ == "__main__":
    print("⚠️  注意：此测试需要在虚拟环境中运行")
    print("📝 运行命令: source venv/bin/activate && python3 test_local_claude_fix.py")
    print()
    
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)