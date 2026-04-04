/**
 * NeuralBot OMEGA — Contract Deployment Script
 * 
 * Deploys:
 *   1. AaveBotFactory (creates executor instances)
 *   2. NeuralBotVault (profit splitting)
 *   3. First AaveBotExecutor via factory
 *
 * Cost: ~$2-3 on Arbitrum
 * 
 * Usage:
 *   npx hardhat run scripts/deploy.js --network arbitrum
 */

const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with:", deployer.address);
  console.log("Balance:", hre.ethers.formatEther(await hre.ethers.provider.getBalance(deployer.address)), "ETH");

  // ── Arbitrum Aave V3 Pool Addresses Provider ──
  const POOL_PROVIDER = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb";
  const USDC_ARB      = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8";
  const PLATFORM_WALLET = process.env.PLATFORM_WALLET || deployer.address;

  // ── 1. Deploy Factory ──
  console.log("\n1. Deploying AaveBotFactory...");
  const Factory = await hre.ethers.getContractFactory("AaveBotFactory");
  const factory = await Factory.deploy(POOL_PROVIDER);
  await factory.waitForDeployment();
  const factoryAddr = await factory.getAddress();
  console.log("   AaveBotFactory:", factoryAddr);

  // ── 2. Deploy Vault ──
  console.log("\n2. Deploying NeuralBotVault...");
  const Vault = await hre.ethers.getContractFactory("NeuralBotVault");
  const vault = await Vault.deploy(USDC_ARB, PLATFORM_WALLET, deployer.address);
  await vault.waitForDeployment();
  const vaultAddr = await vault.getAddress();
  console.log("   NeuralBotVault:", vaultAddr);

  // ── 3. Create first bot executor ──
  console.log("\n3. Creating first AaveBotExecutor...");
  const tx = await factory.createBot(deployer.address);
  const receipt = await tx.wait();
  const executorAddr = await factory.getExecutor(deployer.address);
  console.log("   AaveBotExecutor:", executorAddr);

  // ── 4. Grant bot role to executor ──
  console.log("\n4. Granting BOT_ROLE to executor on vault...");
  await (await vault.grantBotRole(executorAddr)).wait();
  console.log("   Done.");

  // ── Summary ──
  console.log("\n" + "=".repeat(55));
  console.log("  DEPLOYMENT COMPLETE");
  console.log("=".repeat(55));
  console.log(`  FACTORY:  ${factoryAddr}`);
  console.log(`  VAULT:    ${vaultAddr}`);
  console.log(`  EXECUTOR: ${executorAddr}`);
  console.log(`  PLATFORM: ${PLATFORM_WALLET}`);
  console.log("=".repeat(55));
  console.log("\n  Add to .env:");
  console.log(`  FACTORY_CONTRACT_ADDRESS=${factoryAddr}`);
  console.log(`  VAULT_CONTRACT_ADDRESS=${vaultAddr}`);
  console.log(`  AAVE_BOT_EXECUTOR=${executorAddr}`);
}

main().catch(console.error);
