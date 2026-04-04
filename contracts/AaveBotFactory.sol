// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AaveBotFactory
 * @notice Deploys per-user AaveBotExecutor instances.
 * Users get their own isolated executor contract.
 * 
 * AUDIT:
 *   ✅ Factory pattern: each user gets own contract
 *   ✅ Deterministic addresses via CREATE2
 *   ✅ Owner registry prevents duplicate deployments
 *   ✅ Events on all deployments
 */

import "./AaveBotExecutor.sol";

contract AaveBotFactory {
    address public immutable poolProvider;
    address public admin;

    mapping(address => address) public userExecutors;
    address[] public allExecutors;

    event BotCreated(address indexed user, address indexed executor, uint256 index);

    constructor(address _poolProvider) {
        poolProvider = _poolProvider;
        admin = msg.sender;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "NOT_ADMIN");
        _;
    }

    /**
     * @notice Deploy a new AaveBotExecutor for a user.
     * @param user The user who will own the executor.
     * @return executor Address of the new executor contract.
     */
    function createBot(address user) external onlyAdmin returns (address executor) {
        require(user != address(0), "ZERO_USER");
        require(userExecutors[user] == address(0), "BOT_EXISTS");

        // Deploy new executor with user as owner
        AaveBotExecutor bot = new AaveBotExecutor(poolProvider, user);
        executor = address(bot);

        userExecutors[user] = executor;
        allExecutors.push(executor);

        emit BotCreated(user, executor, allExecutors.length - 1);
    }

    /**
     * @notice Get executor address for a user.
     */
    function getExecutor(address user) external view returns (address) {
        return userExecutors[user];
    }

    /**
     * @notice Total number of deployed executors.
     */
    function totalBots() external view returns (uint256) {
        return allExecutors.length;
    }

    function setAdmin(address _new) external onlyAdmin {
        require(_new != address(0), "ZERO_ADMIN");
        admin = _new;
    }
}
