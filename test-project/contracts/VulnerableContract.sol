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
    
    // 新增状态变量
    mapping(address => uint256) public nonces;
    mapping(bytes32 => bool) public usedSignatures;
    uint256 public lastUpdateTime;
    uint256 public randomSeed;
    
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    
    constructor() {
        owner = msg.sender;
        totalSupply = 1000000 * 10**18;
        lastUpdateTime = block.timestamp;
        randomSeed = uint256(keccak256(abi.encodePacked(block.timestamp, block.difficulty)));
    }
    
    // 漏洞1: 缺少访问控制修饰符
    function setOwner(address newOwner) public {
        owner = newOwner; // 任何人都可以改变owner
        emit OwnershipTransferred(owner, newOwner);
    }
    
    // 漏洞2: 重入攻击漏洞
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        
        // 在更新状态之前进行外部调用 - 重入漏洞
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] -= amount; // 状态更新在外部调用之后
        emit Withdrawal(msg.sender, amount);
    }
    
    // 漏洞3: 整数溢出/下溢 (在0.8.0之前版本中)
    function unsafeAdd(uint256 a, uint256 b) public pure returns (uint256) {
        return a + b; // 可能溢出
    }
    
    function unsafeSub(uint256 a, uint256 b) public pure returns (uint256) {
        return a - b; // 可能下溢
    }
    
    // 漏洞4: 时间戳依赖
    function timeBasedFunction() public view returns (bool) {
        // 依赖区块时间戳，可能被矿工操纵
        return block.timestamp > lastUpdateTime + 1 days;
    }
    
    // 漏洞5: 弱随机数生成
    function getRandomNumber() public view returns (uint256) {
        // 使用可预测的随机数源
        return uint256(keccak256(abi.encodePacked(block.timestamp, block.difficulty, msg.sender)));
    }
    
    // 漏洞6: 签名重放攻击
    function verifySignature(
        address user,
        uint256 amount,
        uint256 nonce,
        bytes memory signature
    ) public {
        bytes32 messageHash = keccak256(abi.encodePacked(user, amount, nonce));
        bytes32 ethSignedMessageHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", messageHash));
        
        address signer = recoverSigner(ethSignedMessageHash, signature);
        require(signer == user, "Invalid signature");
        
        // 没有检查nonce是否已使用 - 重放攻击漏洞
        balances[user] += amount;
    }
    
    // 漏洞7: 缺少重入保护
    function deposit() public payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
        
        // 没有重入保护，可能被重入攻击
        if (msg.value > 0) {
            // 外部调用
            (bool success, ) = msg.sender.call{value: 0}("");
            require(success, "Call failed");
        }
    }
    
    // 漏洞8: 未检查的返回值
    function unsafeTransfer(address to, uint256 amount) public {
        // 没有检查transfer的返回值
        payable(to).transfer(amount);
        balances[msg.sender] -= amount;
    }
    
    // 漏洞9: 前端运行漏洞
    function frontrunVulnerable(uint256 newPrice) public {
        // 价格更新没有时间锁，容易被前端运行
        totalSupply = newPrice;
    }
    
    // 漏洞10: 权限提升漏洞
    function emergencyWithdraw() public {
        // 任何人都可以调用紧急提取
        uint256 contractBalance = address(this).balance;
        payable(msg.sender).transfer(contractBalance);
    }
    
    // 漏洞11: 拒绝服务攻击
    function dosVulnerable() public {
        // 没有gas限制，可能导致DoS
        for (uint256 i = 0; i < 1000000; i++) {
            // 大量计算
            randomSeed = uint256(keccak256(abi.encodePacked(randomSeed, i)));
        }
    }
    
    // 漏洞12: 状态变量未初始化
    uint256 public uninitializedVar; // 默认为0，但可能不是预期值
    
    // 漏洞13: 外部调用后状态修改
    function externalCallVulnerable(address target) public {
        balances[msg.sender] -= 100;
        
        // 外部调用可能失败，但状态已经修改
        (bool success, ) = target.call("");
        require(success, "External call failed");
    }
    
    // 漏洞14: 缺少事件记录
    function silentTransfer(address to, uint256 amount) public {
        balances[msg.sender] -= amount;
        balances[to] += amount;
        // 没有发出事件，难以追踪
    }
    
    // 漏洞15: 硬编码地址
    address constant HARDCODED_ADDRESS = 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6;
    
    function hardcodedTransfer(uint256 amount) public {
        balances[msg.sender] -= amount;
        balances[HARDCODED_ADDRESS] += amount;
    }
    
    // 辅助函数
    function recoverSigner(bytes32 messageHash, bytes memory signature) internal pure returns (address) {
        bytes32 r;
        bytes32 s;
        uint8 v;
        
        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }
        
        return ecrecover(messageHash, v, r, s);
    }
    
    // 接收以太币
    receive() external payable {
        balances[msg.sender] += msg.value;
    }
    
    // 回退函数
    fallback() external payable {
        balances[msg.sender] += msg.value;
    }
}

interface IFlashLoanReceiver {
    function onFlashLoan(uint256 amount) external;
}
