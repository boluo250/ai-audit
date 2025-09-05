mod vulnerable;

use vulnerable::*;

fn main() {
    println!("=== 测试项目 - 包含安全漏洞的代码 ===");
    
    // 演示各种漏洞
    demonstrate_vulnerabilities();
}

fn demonstrate_vulnerabilities() {
    println!("\n1. 测试缓冲区溢出漏洞:");
    let data = vec![1u8; 2048]; // 超过缓冲区大小
    let result = unsafe_buffer_operations(&data);
    println!("处理了 {} 字节数据", result.len());
    
    println!("\n2. 测试整数溢出:");
    let result = integer_overflow_vulnerability(u32::MAX, 1);
    println!("计算结果: {}", result);
    
    println!("\n3. 测试不安全的反序列化:");
    let json_data = r#"{"name":"test","value":42}"#;
    match unsafe_deserialization(json_data) {
        Ok(data) => println!("反序列化成功: {:?}", data),
        Err(e) => println!("反序列化失败: {}", e),
    }
    
    println!("\n4. 测试路径遍历漏洞:");
    let dangerous_path = "../../../etc/passwd";
    match path_traversal_vulnerability(dangerous_path) {
        Ok(content) => println!("读取到文件内容: {} 字节", content.len()),
        Err(e) => println!("读取文件失败: {}", e),
    }
    
    println!("\n5. 测试命令注入漏洞:");
    let malicious_input = "test; cat /etc/passwd";
    match command_injection_vulnerability(malicious_input) {
        Ok(output) => println!("命令输出: {}", output),
        Err(e) => println!("命令执行失败: {}", e),
    }
    
    println!("\n6. 测试SQL注入漏洞:");
    let malicious_query = "'; DROP TABLE users; --";
    let result = sql_injection_vulnerability(malicious_query);
    println!("查询结果: {}", result);
    
    println!("\n7. 测试内存泄露:");
    memory_leak_vulnerability();
    
    println!("\n8. 测试弱随机数生成:");
    let weak_random = weak_random_generation();
    println!("生成的弱随机数: {}", weak_random);
    
    println!("\n9. 测试不安全的指针操作:");
    unsafe_pointer_operations();
    
    println!("\n10. 测试时间检查到使用时间 (TOCTOU) 漏洞:");
    let filename = "test_file.txt";
    match toctou_vulnerability(filename) {
        Ok(_) => println!("文件操作完成"),
        Err(e) => println!("文件操作失败: {}", e),
    }
    
    println!("\n11. 测试时序攻击漏洞:");
    let _timing_result = timing_attack_vulnerable_compare("secret123", "secret456");
    
    println!("\n12. 测试不安全的查询构建:");
    let _weak_query = unsafe_query_builder("users", "id = 1; DROP TABLE users; --");
    println!("Generated query: {}", _weak_query);
    
    println!("测试完成！");
}