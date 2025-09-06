#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import psutil
import time

# 添加src路径
sys.path.append('src')

from openai_api.openai import common_get_embedding, get_embedding_model

def get_memory_usage():
    """获取当前内存使用情况"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024  # MB

def test_hf_embedding():
    """测试Hugging Face Transformers embedding"""
    print("🧪 测试Hugging Face Transformers embedding模型...")
    
    # 记录初始内存
    initial_memory = get_memory_usage()
    print(f" 初始内存使用: {initial_memory:.1f}MB")
    
    # 测试模型加载
    print("\n📥 加载模型...")
    start_time = time.time()
    
    try:
        model, tokenizer = get_embedding_model()
        load_time = time.time() - start_time
        load_memory = get_memory_usage()
        
        print(f"✅ 模型加载完成")
        print(f"   加载时间: {load_time:.2f}秒")
        print(f"   加载后内存: {load_memory:.1f}MB")
        print(f"   内存增加: {load_memory - initial_memory:.1f}MB")
        print(f"   模型维度: {model.config.hidden_size}")
        
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return
    
    # 测试用例
    test_cases = [
        "function transfer(address to, uint256 amount) public",
        "重入攻击漏洞",
        "access control",
        "withdraw function",
        "智能合约安全审计"
    ]
    
    print(f"\n🔍 测试embedding生成...")
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {text}")
        
        try:
            start_time = time.time()
            embedding = common_get_embedding(text)
            end_time = time.time()
            
            current_memory = get_memory_usage()
            
            print(f"✅ 成功生成embedding")
            print(f"   维度: {len(embedding)}")
            print(f"   生成时间: {(end_time - start_time)*1000:.1f}ms")
            print(f"   当前内存: {current_memory:.1f}MB")
            print(f"   前5个值: {[f'{x:.4f}' for x in embedding[:5]]}")
            
        except Exception as e:
            print(f"❌ 失败: {e}")
    
    # 最终内存统计
    final_memory = get_memory_usage()
    print(f"\n📊 最终统计:")
    print(f"   初始内存: {initial_memory:.1f}MB")
    print(f"   最终内存: {final_memory:.1f}MB")
    print(f"   总内存增加: {final_memory - initial_memory:.1f}MB")

if __name__ == "__main__":
    test_hf_embedding()