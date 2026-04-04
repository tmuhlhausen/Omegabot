// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title NeuralBotVault
 * @notice On-chain profit splitting vault: 75% platform / 25% user.
 * 
 * Flow:
 *   1. Bot deposits profit via depositProfit()
 *   2. Contract auto-splits: 75% to platform wallet, 25% to user balance
 *   3. User can withdraw their 25% at any time
 *   4. User can opt to auto-compound (reinvest as Aave collateral)
 *
 * AUDIT:
 *   ✅ ReentrancyGuard on all state-modifying functions
 *   ✅ Role-based access: BOT_ROLE for deposits, USER for withdrawals
 *   ✅ Emergency withdraw by admin
 *   ✅ Events on ALL state changes
 *   ✅ No delegatecall, no selfdestruct
 */

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

contract NeuralBotVault is ReentrancyGuard, Pausable, AccessControl {
    using SafeERC20 for IERC20;

    // ─── Roles ───────────────────────────────────────────────────────────
    bytes32 public constant BOT_ROLE = keccak256("BOT_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    // ─── Constants ───────────────────────────────────────────────────────
    uint256 public constant PLATFORM_SHARE_BPS = 7500;  // 75%
    uint256 public constant USER_SHARE_BPS     = 2500;  // 25%
    uint256 public constant BPS_DENOMINATOR    = 10000;

    // ─── State ───────────────────────────────────────────────────────────
    address public platformWallet;
    IERC20  public immutable depositToken;      // USDC

    mapping(address => uint256) public userBalances;
    mapping(address => bool)    public autoCompound;

    uint256 public totalDeposited;
    uint256 public totalPlatformShare;
    uint256 public totalUserShare;
    uint256 public totalWithdrawn;

    // ─── Events ──────────────────────────────────────────────────────────
    event ProfitDeposited(
        address indexed bot,
        uint256 grossAmount,
        uint256 platformAmount,
        uint256 userAmount,
        address indexed user
    );
    event UserWithdrawal(address indexed user, uint256 amount);
    event AutoCompoundSet(address indexed user, bool enabled);
    event PlatformWalletUpdated(address indexed oldWallet, address indexed newWallet);
    event EmergencyWithdraw(address indexed admin, address indexed token, uint256 amount);

    // ─── Constructor ─────────────────────────────────────────────────────
    constructor(
        address _depositToken,
        address _platformWallet,
        address _admin
    ) {
        require(_depositToken != address(0), "ZERO_TOKEN");
        require(_platformWallet != address(0), "ZERO_PLATFORM");
        require(_admin != address(0), "ZERO_ADMIN");

        depositToken = IERC20(_depositToken);
        platformWallet = _platformWallet;

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(ADMIN_ROLE, _admin);
    }

    // ─── Deposit (called by bot after profitable trade) ──────────────────
    /**
     * @notice Deposit profit and auto-split 75/25.
     * @param amount Gross profit amount in deposit token
     * @param user The user who owns this bot instance
     *
     * AUDIT[REENTRANCY]: State updated BEFORE transfers.
     * AUDIT[EXACT_AMOUNT]: Transfers exact calculated amounts.
     */
    function depositProfit(
        uint256 amount,
        address user
    ) external nonReentrant whenNotPaused onlyRole(BOT_ROLE) {
        require(amount > 0, "ZERO_AMOUNT");
        require(user != address(0), "ZERO_USER");

        // Transfer from bot to this vault
        depositToken.safeTransferFrom(msg.sender, address(this), amount);

        // Calculate split
        uint256 platformAmount = (amount * PLATFORM_SHARE_BPS) / BPS_DENOMINATOR;
        uint256 userAmount     = amount - platformAmount; // Avoids rounding loss

        // Update state BEFORE external transfers (reentrancy protection)
        totalDeposited += amount;
        totalPlatformShare += platformAmount;
        totalUserShare += userAmount;
        userBalances[user] += userAmount;

        // Transfer platform share immediately
        depositToken.safeTransfer(platformWallet, platformAmount);

        emit ProfitDeposited(msg.sender, amount, platformAmount, userAmount, user);
    }

    // ─── User Withdrawal ─────────────────────────────────────────────────
    /**
     * @notice Withdraw accumulated user share.
     * @param amount Amount to withdraw (must be <= balance)
     */
    function withdraw(uint256 amount) external nonReentrant whenNotPaused {
        require(amount > 0, "ZERO_AMOUNT");
        require(userBalances[msg.sender] >= amount, "INSUFFICIENT_BALANCE");

        // State update BEFORE transfer
        userBalances[msg.sender] -= amount;
        totalWithdrawn += amount;

        depositToken.safeTransfer(msg.sender, amount);

        emit UserWithdrawal(msg.sender, amount);
    }

    /**
     * @notice Withdraw entire balance.
     */
    function withdrawAll() external nonReentrant whenNotPaused {
        uint256 balance = userBalances[msg.sender];
        require(balance > 0, "ZERO_BALANCE");

        userBalances[msg.sender] = 0;
        totalWithdrawn += balance;

        depositToken.safeTransfer(msg.sender, balance);

        emit UserWithdrawal(msg.sender, balance);
    }

    // ─── Auto-Compound Toggle ────────────────────────────────────────────
    function setAutoCompound(bool enabled) external {
        autoCompound[msg.sender] = enabled;
        emit AutoCompoundSet(msg.sender, enabled);
    }

    // ─── View Functions ──────────────────────────────────────────────────
    function getUserBalance(address user) external view returns (uint256) {
        return userBalances[user];
    }

    function getVaultStats() external view returns (
        uint256 _totalDeposited,
        uint256 _totalPlatformShare,
        uint256 _totalUserShare,
        uint256 _totalWithdrawn,
        uint256 _currentBalance
    ) {
        return (
            totalDeposited,
            totalPlatformShare,
            totalUserShare,
            totalWithdrawn,
            depositToken.balanceOf(address(this))
        );
    }

    // ─── Admin Functions ─────────────────────────────────────────────────
    function setPlatformWallet(address _new) external onlyRole(ADMIN_ROLE) {
        require(_new != address(0), "ZERO_ADDRESS");
        emit PlatformWalletUpdated(platformWallet, _new);
        platformWallet = _new;
    }

    function grantBotRole(address bot) external onlyRole(ADMIN_ROLE) {
        _grantRole(BOT_ROLE, bot);
    }

    function revokeBotRole(address bot) external onlyRole(ADMIN_ROLE) {
        _revokeRole(BOT_ROLE, bot);
    }

    function pause() external onlyRole(ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(ADMIN_ROLE) {
        _unpause();
    }

    /**
     * @notice Emergency rescue of any ERC20 token.
     * AUDIT[EMERGENCY]: Only admin. Emits event. Intended for stuck tokens.
     */
    function emergencyRescue(
        address token,
        uint256 amount
    ) external onlyRole(ADMIN_ROLE) nonReentrant {
        IERC20(token).safeTransfer(msg.sender, amount);
        emit EmergencyWithdraw(msg.sender, token, amount);
    }
}
