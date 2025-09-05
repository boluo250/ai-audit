// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title VulnerableContract - 包含多种安全漏洞的测试合约
 * @dev 这是一个用于测试安全分析工具的合约，包含了多种常见的安全漏洞
 */
contract VulnerableContract {
    address public owner;
    mapping(address => uint256) public balances;
    uint256 public totalSupply;
    bool internal locked;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    
    constructor() {
        owner = msg.sender;
        totalSupply = 1000000 * 10**18;
    }
    
    // 漏洞1: 缺少访问控制修饰符
    function setOwner(address newOwner) public {
        owner = newOwner; // 任何人都可以改变owner
    }
    
    // 漏洞2: 重入攻击漏洞
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // 在更新状态之前进行外部调用 - 重入漏洞
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= amount; // 状态更新在外部调用之后
    }
    
    // 漏洞3: 整数溢出（虽然Solidity 0.8+有内置保护，但逻辑仍有问题）
    function mint(address to, uint256 amount) public {
        // 缺少权限检查
        balances[to] += amount;
        totalSupply += amount; // 可能导致意外的大数值
    }
    
    // 漏洞4: 未检查的外部调用
    function transfer(address to, uint256 amount) public returns (bool) {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        balances[msg.sender] -= amount;
        balances[to] += amount;
        
        // 未检查返回值的外部调用
        to.call(abi.encodeWithSignature("onTokenReceived(address,uint256)", msg.sender, amount));
        
        return true;
    }
    
    // 漏洞5: 弱随机数生成
    function getRandomNumber() public view returns (uint256) {
        // 使用可预测的值生成"随机数"
        return uint256(keccak256(abi.encodePacked(block.timestamp, block.difficulty, msg.sender)));
    }
    
    // 漏洞6: DoS with Failed Call
    function distributeRewards(address[] memory recipients) public {
        require(msg.sender == owner, "Only owner");
        
        for (uint256 i = 0; i < recipients.length; i++) {
            // 如果任何一个调用失败，整个函数会回滚
            (bool success, ) = recipients[i].call{value: 1 ether}("");
            require(success, "Payment failed"); // DoS风险
        }
    }
    
    // 漏洞7: 时间戳依赖
    uint256 public deadline;
    
    function setDeadline() public {
        deadline = block.timestamp + 1 days; // 矿工可以操纵时间戳
    }
    
    function isExpired() public view returns (bool) {
        return block.timestamp > deadline; // 时间戳依赖
    }
    
    // 漏洞8: 未保护的selfdestruct
    function destroy() public {
        // 没有适当的访问控制
        selfdestruct(payable(msg.sender));
    }
    
    // 漏洞9: 状态变量可见性问题
    uint256 private secretValue = 12345; // 私有变量仍可在区块链上读取
    
    function getSecret() public view returns (uint256) {
        return secretValue; // 暴露"私有"数据
    }
    
    // 漏洞10: 缺少输入验证
    function updateBalance(address user, uint256 newBalance) public {
        // 没有验证user地址是否有效
        // 没有验证newBalance是否合理
        balances[user] = newBalance;
    }
    
    // 漏洞11: Gas限制DoS
    function massTransfer(address[] memory recipients, uint256[] memory amounts) public {
        // 没有限制数组长度，可能导致gas耗尽
        for (uint256 i = 0; i < recipients.length; i++) {
            transfer(recipients[i], amounts[i]);
        }
    }
    
    // 接收以太坊
    receive() external payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }
    
    // 漏洞12: 不安全的委托调用
    function delegateCallTest(address target, bytes memory data) public returns (bool, bytes memory) {
        // 危险的委托调用，可能改变合约状态
        return target.delegatecall(data);
    }
}

/**
 * @title FlashLoanVulnerable - 闪电贷相关漏洞示例
 */
contract FlashLoanVulnerable {
    mapping(address => uint256) public deposits;
    uint256 public price = 100; // 简化的价格oracle
    
    // 漏洞13: Price Oracle Manipulation
    function updatePrice() public {
        // 简单地基于合约余额更新价格 - 可被操纵
        price = address(this).balance / 1000;
    }
    
    function liquidate(address user) public {
        require(deposits[user] * price < address(this).balance / 2, "Position healthy");
        // 清算逻辑...
        deposits[user] = 0;
    }
    
    // 漏洞14: 闪电贷重入
    function flashLoan(uint256 amount) external {
        uint256 balanceBefore = address(this).balance;
        
        // 发送资金
        payable(msg.sender).transfer(amount);
        
        // 调用借款人合约
        IFlashLoanReceiver(msg.sender).onFlashLoan(amount);
        
        // 检查还款 - 但状态可能已被重入攻击改变
        require(address(this).balance >= balanceBefore, "Loan not repaid");
    }
}

interface IFlashLoanReceiver {
    function onFlashLoan(uint256 amount) external;
}