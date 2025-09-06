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
    

interface IFlashLoanReceiver {
    function onFlashLoan(uint256 amount) external;
}
