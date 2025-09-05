// Rust测试代码 - 包含常见安全漏洞
use std::collections::HashMap;
use std::fs::File;
use std::io::{Read, Write};
use std::process::Command;

/// 漏洞26: 缓冲区溢出风险
pub fn unsafe_buffer_operations(data: &[u8]) -> Vec<u8> {
    let mut buffer = vec![0u8; 1024];
    
    // 没有检查data长度，可能导致溢出
    for (i, &byte) in data.iter().enumerate() {
        buffer[i] = byte; // 潜在的越界访问
    }
    
    buffer
}

/// 漏洞27: 未检查的算术运算
pub fn unchecked_arithmetic(a: u32, b: u32) -> u32 {
    // 可能发生整数溢出
    let result = a + b;
    
    // 除法可能panic
    let division = a / b; // 如果b为0会panic
    
    result * division
}

/// 漏洞28: 不安全的文件操作
pub fn unsafe_file_operations(filename: &str, content: &str) -> Result<(), std::io::Error> {
    // 没有路径验证，可能导致路径遍历攻击
    let mut file = File::create(filename)?;
    
    // 直接写入用户输入，没有验证
    file.write_all(content.as_bytes())?;
    
    Ok(())
}

/// 漏洞29: 命令注入
pub fn execute_command(user_input: &str) -> String {
    // 直接将用户输入传递给系统命令 - 命令注入风险
    let output = Command::new("sh")
        .arg("-c")
        .arg(user_input) // 危险：未经验证的用户输入
        .output()
        .expect("Failed to execute command");
    
    String::from_utf8_lossy(&output.stdout).to_string()
}

/// 漏洞30: 内存泄漏和double-free风险
pub fn unsafe_memory_operations() {
    use std::ptr;
    use std::alloc::{alloc, dealloc, Layout};
    
    unsafe {
        let layout = Layout::new::<u8>();
        let ptr = alloc(layout);
        
        if !ptr.is_null() {
            // 写入数据
            *ptr = 42;
            
            // 双重释放风险
            dealloc(ptr, layout);
            // dealloc(ptr, layout); // 如果取消注释会导致double-free
            
            // 使用已释放的内存
            // let value = *ptr; // use-after-free
        }
    }
}

/// 漏洞31: 竞态条件
use std::sync::{Arc, Mutex};
use std::thread;

pub struct UnsafeCounter {
    value: u64,
    // 没有使用Mutex保护
}

impl UnsafeCounter {
    pub fn new() -> Self {
        Self { value: 0 }
    }
    
    // 线程不安全的操作
    pub fn increment(&mut self) {
        let temp = self.value;
        // 模拟一些处理时间
        thread::sleep(std::time::Duration::from_nanos(1));
        self.value = temp + 1; // 竞态条件
    }
    
    pub fn get_value(&self) -> u64 {
        self.value
    }
}

/// 漏洞32: SQL注入模拟（如果使用数据库）
pub fn unsafe_query_builder(table: &str, condition: &str) -> String {
    // 直接字符串拼接，容易SQL注入
    format!("SELECT * FROM {} WHERE {}", table, condition)
}

/// 漏洞33: 弱密码学实现
pub fn weak_encryption(data: &[u8], key: u8) -> Vec<u8> {
    // 简单的XOR"加密" - 非常弱
    data.iter().map(|&b| b ^ key).collect()
}

/// 漏洞34: 时间攻击漏洞
pub fn timing_attack_vulnerable_compare(secret: &str, input: &str) -> bool {
    if secret.len() != input.len() {
        return false;
    }
    
    // 字节级比较，可能泄露时间信息
    for (a, b) in secret.bytes().zip(input.bytes()) {
        if a != b {
            return false; // 早期退出泄露信息
        }
    }
    
    true
}

/// 漏洞35: 不安全的随机数生成
pub fn weak_random_number() -> u32 {
    use std::time::{SystemTime, UNIX_EPOCH};
    
    // 使用可预测的时间戳作为随机数种子
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("Time went backwards")
        .as_secs() as u32;
    
    // 简单的线性同余生成器 - 可预测
    timestamp.wrapping_mul(1103515245).wrapping_add(12345)
}

/// 漏洞36: 资源泄漏
pub fn resource_leak() {
    let mut files = Vec::new();
    
    // 打开很多文件但不关闭
    for i in 0..1000 {
        if let Ok(file) = File::open("/dev/null") {
            files.push(file);
            // 没有明确关闭文件，依赖Drop trait
        }
    }
    // files在函数结束时才会被drop
}

/// 漏洞37: 不正确的错误处理
pub fn improper_error_handling(filename: &str) -> String {
    let mut file = File::open(filename).unwrap(); // panic if file doesn't exist
    let mut content = String::new();
    
    // 忽略read错误
    let _ = file.read_to_string(&mut content);
    
    content
}

/// 漏洞38: 数据验证不足
#[derive(Debug)]
pub struct UserAccount {
    pub username: String,
    pub email: String,
    pub balance: i64,
}

impl UserAccount {
    pub fn new(username: String, email: String, balance: i64) -> Self {
        // 没有输入验证
        Self { username, email, balance }
    }
    
    pub fn transfer(&mut self, amount: i64) -> bool {
        // 没有检查负数或溢出
        self.balance -= amount;
        true
    }
}

/// 漏洞39: 格式化字符串漏洞
pub fn format_string_vulnerability(user_input: &str) {
    // 直接使用用户输入作为格式字符串
    println!("{}", user_input); // 相对安全，但在某些情况下仍需小心
}

/// 漏洞40: 不安全的反序列化
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
pub struct Command {
    pub action: String,
    pub parameters: HashMap<String, String>,
}

pub fn unsafe_deserialize(data: &str) -> Result<Command, serde_json::Error> {
    // 直接反序列化用户输入，可能导致代码执行
    serde_json::from_str(data)
}

// 主函数演示这些漏洞
pub fn demonstrate_vulnerabilities() {
    println!("=== Rust安全漏洞演示 ===");
    
    // 演示缓冲区问题
    let large_data = vec![0u8; 2048]; // 大于buffer大小
    let _result = unsafe_buffer_operations(&large_data);
    
    // 演示算术问题
    let _overflow = unchecked_arithmetic(u32::MAX, 1);
    
    // 演示文件操作问题
    let _ = unsafe_file_operations("../../../etc/passwd", "malicious content");
    
    // 演示弱加密
    let data = b"sensitive information";
    let _encrypted = weak_encryption(data, 42);
    
    println!("漏洞演示完成 - 实际环境中请避免这些模式！");
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_vulnerable_functions() {
        // 测试各种漏洞函数
        let account = UserAccount::new("test".to_string(), "test@example.com".to_string(), 100);
        println!("Created account: {:?}", account);
        
        let weak_rand = weak_random_number();
        println!("Weak random: {}", weak_rand);
    }
}