const { expect } = require("chai");
const { ethers } = require("hardhat");

const describeFork = process.env.ARBITRUM_RPC_URL ? describe : describe.skip;

const POOL_PROVIDER = "0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb";
const USDC = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8";
const WETH = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1";

const erc20Abi = [
  "function balanceOf(address) view returns (uint256)",
  "function transfer(address,uint256) returns (bool)",
  "function deposit() payable",
];

function encodeArb(opCode, params) {
  const coder = ethers.AbiCoder.defaultAbiCoder();
  return coder.encode(
    ["tuple(uint8,address,address,address,uint8,uint8,uint8,uint24,uint24,uint24,uint256,uint256,uint256)"],
    [[
      opCode,
      params.tokenA,
      params.tokenB,
      params.tokenC,
      params.dexBuy,
      params.dexMid,
      params.dexSell,
      params.feeBuy,
      params.feeMid,
      params.feeSell,
      params.minAmountOutBuy,
      params.minAmountOutMid,
      params.minAmountOutSell,
    ]]
  );
}

function encodeLiq(params) {
  const coder = ethers.AbiCoder.defaultAbiCoder();
  return coder.encode(
    ["tuple(address,address,address,uint256,bool,uint8,uint24,uint256)"],
    [[
      params.collateralAsset,
      params.debtAsset,
      params.borrower,
      params.debtToCover,
      params.receiveAToken,
      params.sellDex,
      params.sellFee,
      params.amountOutMin,
    ]]
  );
}

describeFork("AaveBotExecutor fork integration", function () {
  let owner;
  let executor;

  beforeEach(async function () {
    [owner] = await ethers.getSigners();
    const Executor = await ethers.getContractFactory("AaveBotExecutor");
    executor = await Executor.deploy(POOL_PROVIDER, owner.address);
    await executor.waitForDeployment();
  });

  it("exercises the flash-loan entrypoint with explicit slippage-protected arb params", async function () {
    const opData = encodeArb(0, {
      tokenA: WETH,
      tokenB: USDC,
      tokenC: ethers.ZeroAddress,
      dexBuy: 0,
      dexMid: 0,
      dexSell: 1,
      feeBuy: 500,
      feeMid: 0,
      feeSell: 500,
      minAmountOutBuy: 1n,
      minAmountOutMid: 0n,
      minAmountOutSell: 1_000_001n,
    });

    await expect(executor.execute(USDC, 1_000_000n, 0, opData)).to.be.reverted;
  });

  it("exercises the liquidation path against forked Aave wiring", async function () {
    const opData = encodeLiq({
      collateralAsset: WETH,
      debtAsset: USDC,
      borrower: owner.address,
      debtToCover: 1_000_000n,
      receiveAToken: false,
      sellDex: 0,
      sellFee: 3000,
      amountOutMin: 1_000_001n,
    });

    await expect(executor.execute(USDC, 1_000_000n, 2, opData)).to.be.reverted;
  });

  it("rescues accumulated profits after funding the contract on fork", async function () {
    const weth = await ethers.getContractAt(erc20Abi, WETH);
    await weth.deposit({ value: ethers.parseEther("0.2") });
    await weth.transfer(await executor.getAddress(), ethers.parseEther("0.1"));

    expect(await executor.getBalance(WETH)).to.equal(ethers.parseEther("0.1"));

    const ownerBefore = await weth.balanceOf(owner.address);
    await expect(executor.rescueFunds(WETH, ethers.parseEther("0.05")))
      .to.emit(executor, "ProfitRescued");
    expect(await executor.getBalance(WETH)).to.equal(ethers.parseEther("0.05"));
    expect(await weth.balanceOf(owner.address)).to.equal(ownerBefore + ethers.parseEther("0.05"));
  });
});
