# Smart contract interaction
from web3 import Web3
from eth_account import Account
from typing import Dict, Optional
import json

from ..config import settings

# 合约 ABI（从 Remix 复制）
ETH_MARKETPLACE_ABI = [
    {
        "inputs": [{"internalType": "string", "name": "_dataHash", "type": "string"},
                   {"internalType": "uint256", "name": "_price", "type": "uint256"}],
        "name": "listData",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    # ... 其他函数定义
]

class BlockchainService:
    def __init__(self):
        self.mock_mode = settings.USE_MOCK_SERVICES
        self.deployed_contracts: Dict[int, Dict] = {}
        
        if not self.mock_mode:
            if not settings.WEB3_RPC_URL or not settings.CONTRACT_ADDRESS:
                raise ValueError("WEB3_RPC_URL 和 CONTRACT_ADDRESS 必须配置")
            
            self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))
            if not self.w3.is_connected():
                raise ConnectionError("无法连接到区块链节点")
            
            self.contract = self.w3.eth.contract(
                address=settings.CONTRACT_ADDRESS,
                abi=ETH_MARKETPLACE_ABI
            )
            
            if settings.PRIVATE_KEY:
                self.account = Account.from_key(settings.PRIVATE_KEY)
            else:
                self.account = None
            
            if not self.w3.is_connected():
                raise ConnectionError("无法连接到区块链节点")
            else:
                print(f"✅ 成功连接到 {settings.BLOCKCHAIN_NETWORK}")
                print(f"   最新区块: {self.w3.eth.block_number}")

    def mint_context_nft(self, user_address: str, metadata_url: str, price_wei: int = 0) -> Dict:
        """
        调用智能合约的 listData 函数上架数据
        metadata_url: IPFS hash (如 "ipfs://Qm...")
        price_wei: 价格（wei 单位，0 表示免费）
        """
        if self.mock_mode:
            # Mock 逻辑保持不变
            token_id = len(self.deployed_contracts) + 1
            return {
                "success": True,
                "token_id": token_id,
                "tx_hash": f"0x{'a' * 64}",
                "network": settings.BLOCKCHAIN_NETWORK,
                "message": "NFT minted successfully (pseudo mode)",
            }
        
        # 真实链交互
        if not self.account:
            raise ValueError("需要配置 PRIVATE_KEY 以发送交易")
        
        try:
            # 构建交易
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            # 调用 listData 函数
            tx = self.contract.functions.listData(metadata_url, price_wei).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': 1,  # 可根据实际情况调整
                'gasPrice': self.w3.eth.gas_price,
                'chainId': settings.CHAIN_ID if hasattr(settings, 'CHAIN_ID') else 1,
            })
            
            # 签名并发送
            signed_tx = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # 等待交易确认
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            # 从事件中提取 listingId
            listing_id = None
            if receipt.logs:
                # 解析 DataListed 事件
                event = self.contract.events.DataListed().process_receipt(receipt)
                if event:
                    listing_id = event[0]['args']['listingId']
            
            return {
                "success": True,
                "token_id": listing_id or receipt.transactionHash.hex(),
                "tx_hash": receipt.transactionHash.hex(),
                "network": settings.BLOCKCHAIN_NETWORK,
                "block_number": receipt.blockNumber,
                "message": "Data listed successfully on blockchain",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"链上交易失败: {str(e)}",
            }