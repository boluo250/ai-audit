// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "./VulnerableContract.sol";

/**
 * @title DeFiVulnerableContract - DeFi相关安全漏洞示例
 */
contract DeFiVulnerableContract {
    struct LendingPool {
        uint256 totalDeposits;
        uint256 totalBorrows;
        uint256 interestRate;
    }
    
    mapping(address => LendingPool) public pools;
    mapping(address => mapping(address => uint256)) public userDeposits;
    mapping(address => mapping(address => uint256)) public userBorrows;
    
    address public priceOracle;
    uint256 public constant COLLATERAL_RATIO = 150; // 150%
    
    event Deposit(address indexed user, address indexed token, uint256 amount);
    event Borrow(address indexed user, address indexed token, uint256 amount);
    event Liquidation(address indexed liquidator, address indexed borrower, uint256 amount);
    
    // 漏洞15: 缺少初始化保护
    function initialize(address _priceOracle) public {
        // 可以被多次调用，没有初始化保护
        priceOracle = _priceOracle;
    }
    
    // 漏洞16: 价格预言机操纵
    function getPrice(address token) public view returns (uint256) {
        // 简化的价格获取，容易被操纵
        return IERC20(token).balanceOf(address(this)) * 1000;
    }
    
    // 漏洞17: 不正确的利息计算
    function calculateInterest(address token, address user) public view returns (uint256) {
        // 简化的利息计算，可能导致精度损失
        uint256 principal = userBorrows[token][user];
        uint256 rate = pools[token].interestRate;
        
        // 直接计算可能导致整数除法精度损失
        return (principal * rate * block.timestamp) / (365 days * 100);
    }
    
    // 漏洞18: 闪电贷套利攻击向量
    function deposit(address token, uint256 amount) external {
        // 没有检查token的有效性
        IERC20(token).transferFrom(msg.sender, address(this), amount);
        
        userDeposits[token][msg.sender] += amount;
        pools[token].totalDeposits += amount;
        
        // 立即更新利率 - 可被闪电贷利用
        updateInterestRate(token);
        
        emit Deposit(msg.sender, token, amount);
    }
    
    // 漏洞19: 不正确的抵押品检查
    function borrow(address token, uint256 amount) external {
        uint256 userCollateralValue = getUserCollateralValue(msg.sender);
        uint256 borrowValue = amount * getPrice(token);
        
        // 简单的抵押检查，没有考虑价格波动
        require(userCollateralValue * 100 >= borrowValue * COLLATERAL_RATIO, "Insufficient collateral");
        
        userBorrows[token][msg.sender] += amount;
        pools[token].totalBorrows += amount;
        
        // 在状态更新后转账 - 重入风险
        IERC20(token).transfer(msg.sender, amount);
        
        emit Borrow(msg.sender, token, amount);
    }
    
    // 漏洞20: 清算机制漏洞
    function liquidate(address borrower, address collateralToken, address borrowToken) external {
        uint256 borrowValue = userBorrows[borrowToken][borrower] * getPrice(borrowToken);
        uint256 collateralValue = userDeposits[collateralToken][borrower] * getPrice(collateralToken);
        
        // 简单的清算检查
        require(collateralValue * 100 < borrowValue * COLLATERAL_RATIO, "Position healthy");
        
        // 清算奖励计算有漏洞
        uint256 liquidationBonus = collateralValue / 10; // 10% 奖励
        uint256 seizeAmount = userDeposits[collateralToken][borrower] + liquidationBonus;
        
        // 没有检查是否超出用户实际抵押品
        userDeposits[collateralToken][borrower] = 0;
        userBorrows[borrowToken][borrower] = 0;
        
        // 直接转账给清算者，可能超出实际余额
        IERC20(collateralToken).transfer(msg.sender, seizeAmount);
        
        emit Liquidation(msg.sender, borrower, seizeAmount);
    }
    
    // 漏洞21: 复合利息实现错误
    function updateInterestRate(address token) internal {
        LendingPool storage pool = pools[token];
        
        // 错误的利用率计算
        uint256 utilizationRate = pool.totalBorrows / pool.totalDeposits; // 整数除法
        
        // 简单的线性利率模型，没有考虑极端情况
        pool.interestRate = utilizationRate * 10;
        
        // 超过100%可能导致异常行为
        if (pool.interestRate > 100) {
            pool.interestRate = 100;
        }
    }
    
    // 漏洞22: 治理攻击向量
    mapping(address => uint256) public votingPower;
    uint256 public proposalCount;
    
    struct Proposal {
        string description;
        uint256 forVotes;
        uint256 againstVotes;
        bool executed;
        mapping(address => bool) hasVoted;
    }
    
    mapping(uint256 => Proposal) public proposals;
    
    function vote(uint256 proposalId, bool support) external {
        Proposal storage proposal = proposals[proposalId];
        require(!proposal.hasVoted[msg.sender], "Already voted");
        
        // 投票权重基于当前余额 - 可被闪电贷操纵
        uint256 weight = IERC20(priceOracle).balanceOf(msg.sender);
        
        if (support) {
            proposal.forVotes += weight;
        } else {
            proposal.againstVotes += weight;
        }
        
        proposal.hasVoted[msg.sender] = true;
    }
    
    // 辅助函数
    function getUserCollateralValue(address user) internal view returns (uint256) {
        // 简化实现，实际应该遍历所有代币
        return userDeposits[priceOracle][user] * getPrice(priceOracle);
    }
}

// 漏洞23: 不安全的外部接口
interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title AMMLikeContract - AMM相关漏洞示例
 */
contract AMMLikeContract {
    uint256 public reserve0;
    uint256 public reserve1;
    uint256 public constant MINIMUM_LIQUIDITY = 10**3;
    
    // 漏洞24: K值不变性违反
    function swap(uint256 amount0Out, uint256 amount1Out, address to) external {
        require(amount0Out > 0 || amount1Out > 0, "Invalid output amounts");
        
        // 简化的swap逻辑，没有正确检查K值不变性
        if (amount0Out > 0) {
            reserve0 -= amount0Out;
        }
        if (amount1Out > 0) {
            reserve1 -= amount1Out;
        }
        
        // 缺少K值检查
        // require(reserve0 * reserve1 >= k_value, "K");
    }
    
    // 漏洞25: 前置交易(MEV)漏洞
    function addLiquidity(uint256 amount0, uint256 amount1) external returns (uint256 liquidity) {
        // 没有滑点保护的流动性添加
        reserve0 += amount0;
        reserve1 += amount1;
        
        // 简化的流动性计算
        liquidity = (amount0 + amount1) / 2;
        return liquidity;
    }
}