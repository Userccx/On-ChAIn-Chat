# Smart contract interaction - Multi-contract support
import json
from pathlib import Path
from typing import Dict, List, Optional
from web3 import Web3
from eth_account import Account

from ..config import settings
from ..utils.crypto_utils import normalize_address
from ..utils.logger import get_logger

logger = get_logger(__name__)

# ABI 文件路径
ABI_DIR = Path(__file__).parent.parent.parent / "Blockchain"

def load_abi(filename: str) -> list:
    """从文件加载 ABI"""
    abi_path = ABI_DIR / filename
    if abi_path.exists():
        with open(abi_path, 'r') as f:
            return json.load(f)
    logger.warning(f"ABI file not found: {abi_path}")
    return []


# 加载 ABI
DATA_TOKEN_ABI = load_abi("DataToken_2_ABI.json")
MARKET_ABI = load_abi("Market.json")
ETH_MARKET_ABI = [
    # ETHUserDataMarketplace ABI - 从 test_ETH.sol 编译
    # 这里放置编译后的 ABI，或者从文件加载
]


class DataTokenService:
    """DataToken (DTK) ERC20 代币服务"""
    
    def __init__(self, w3: Web3, contract_address: str, private_key: Optional[str] = None):
        self.w3 = w3
        self.contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=DATA_TOKEN_ABI
        )
        self.account = Account.from_key(private_key) if private_key else None
        logger.info(f"✅ DataToken service initialized at {contract_address}")
    
    def get_balance(self, address: str) -> int:
        """获取代币余额"""
        checksum_address = Web3.to_checksum_address(address)
        return self.contract.functions.balanceOf(checksum_address).call()
    
    def get_allowance(self, owner: str, spender: str) -> int:
        """获取授权额度"""
        return self.contract.functions.allowance(
            Web3.to_checksum_address(owner),
            Web3.to_checksum_address(spender)
        ).call()
    
    def approve(self, spender: str, amount: int) -> Dict:
        """授权代币给 spender（需要私钥）"""
        if not self.account:
            raise ValueError("需要配置 PRIVATE_KEY 以发送交易")
        
        tx = self.contract.functions.approve(
            Web3.to_checksum_address(spender),
            amount
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': settings.CHAIN_ID,
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        return {
            "success": receipt.status == 1,
            "tx_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
        }
    
    def transfer(self, to: str, amount: int) -> Dict:
        """转账代币（需要私钥）"""
        if not self.account:
            raise ValueError("需要配置 PRIVATE_KEY 以发送交易")
        
        tx = self.contract.functions.transfer(
            Web3.to_checksum_address(to),
            amount
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': settings.CHAIN_ID,
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        return {
            "success": receipt.status == 1,
            "tx_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
        }
    
    def get_token_info(self) -> Dict:
        """获取代币信息"""
        return {
            "name": self.contract.functions.name().call(),
            "symbol": self.contract.functions.symbol().call(),
            "decimals": self.contract.functions.decimals().call(),
            "totalSupply": self.contract.functions.totalSupply().call(),
        }


class MarketService:
    """数据市场服务（基于 ERC20 代币）"""
    
    def __init__(self, w3: Web3, contract_address: str, private_key: Optional[str] = None):
        self.w3 = w3
        self.contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=MARKET_ABI
        )
        self.account = Account.from_key(private_key) if private_key else None
        logger.info(f"✅ Market service initialized at {contract_address}")
    
    def list_data(self, data_hash: str, price: int) -> Dict:
        """上架数据"""
        if not self.account:
            raise ValueError("需要配置 PRIVATE_KEY 以发送交易")
        
        tx = self.contract.functions.listData(data_hash, price).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': settings.CHAIN_ID,
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        # 解析事件获取 listingId
        listing_id = None
        try:
            events = self.contract.events.DataListed().process_receipt(receipt)
            if events:
                listing_id = events[0]['args']['listingId']
        except Exception as e:
            logger.warning(f"Failed to parse DataListed event: {e}")
        
        return {
            "success": receipt.status == 1,
            "listing_id": listing_id,
            "tx_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
        }
    
    def purchase_access(self, listing_id: int) -> Dict:
        """购买数据访问权（需要先 approve 代币）"""
        if not self.account:
            raise ValueError("需要配置 PRIVATE_KEY 以发送交易")
        
        tx = self.contract.functions.purchaseAccess(listing_id).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': settings.CHAIN_ID,
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        return {
            "success": receipt.status == 1,
            "tx_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
        }
    
    def remove_listing(self, listing_id: int) -> Dict:
        """下架数据"""
        if not self.account:
            raise ValueError("需要配置 PRIVATE_KEY 以发送交易")
        
        tx = self.contract.functions.removeListing(listing_id).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': settings.CHAIN_ID,
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        return {
            "success": receipt.status == 1,
            "tx_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
        }
    
    def get_listing_details(self, listing_id: int) -> Dict:
        """获取上架详情"""
        listing = self.contract.functions.getListingDetails(listing_id).call()
        return {
            "user": listing[0],
            "data_hash": listing[1],
            "price": listing[2],
            "is_active": listing[3],
            "created_at": listing[4],
        }
    
    def get_active_listings(self) -> List[int]:
        """获取所有活跃的上架列表"""
        return self.contract.functions.getActiveListings().call()
    
    def get_user_listings(self, user_address: str) -> List[int]:
        """获取用户的上架列表"""
        return self.contract.functions.getUserListings(
            Web3.to_checksum_address(user_address)
        ).call()
    
    def check_access(self, enterprise: str, listing_id: int) -> bool:
        """检查访问权限"""
        return self.contract.functions.checkAccess(
            Web3.to_checksum_address(enterprise),
            listing_id
        ).call()
    
    def get_payment_token(self) -> str:
        """获取支付代币地址"""
        return self.contract.functions.paymentToken().call()


class ETHMarketService:
    """ETH 版本的数据市场服务"""
    
    def __init__(self, w3: Web3, contract_address: str, private_key: Optional[str] = None):
        self.w3 = w3
        # 如果有编译好的 ABI，使用文件加载
        eth_abi = load_abi("ETH_Market_ABI.json") or ETH_MARKET_ABI
        self.contract = w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=eth_abi
        )
        self.account = Account.from_key(private_key) if private_key else None
        logger.info(f"✅ ETH Market service initialized at {contract_address}")
    
    def list_data(self, data_hash: str, price_wei: int) -> Dict:
        """上架数据（价格单位：wei）"""
        if not self.account:
            raise ValueError("需要配置 PRIVATE_KEY 以发送交易")
        
        tx = self.contract.functions.listData(data_hash, price_wei).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': settings.CHAIN_ID,
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        listing_id = None
        try:
            events = self.contract.events.DataListed().process_receipt(receipt)
            if events:
                listing_id = events[0]['args']['listingId']
        except Exception as e:
            logger.warning(f"Failed to parse DataListed event: {e}")
        
        return {
            "success": receipt.status == 1,
            "listing_id": listing_id,
            "tx_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
        }
    
    def purchase_access(self, listing_id: int, value_wei: int) -> Dict:
        """购买数据访问权（需要发送 ETH）"""
        if not self.account:
            raise ValueError("需要配置 PRIVATE_KEY 以发送交易")
        
        tx = self.contract.functions.purchaseAccess(listing_id).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': settings.CHAIN_ID,
            'value': value_wei,  # 发送 ETH
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        return {
            "success": receipt.status == 1,
            "tx_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
        }
    
    # ... 其他方法与 MarketService 类似 ...


class BlockchainService:
    """统一的区块链服务入口"""
    
    def __init__(self):
        self.mock_mode = settings.USE_MOCK_SERVICES
        self.w3 = None
        self.token_service: Optional[DataTokenService] = None
        self.market_service: Optional[MarketService] = None
        self.eth_market_service: Optional[ETHMarketService] = None
        
        # Mock 模式下的计数器
        self._mock_listing_counter = 0
        
        if not self.mock_mode:
            self._init_real_services()
        else:
            logger.info("🔶 Blockchain service running in MOCK mode")
    
    def _init_real_services(self):
        """初始化真实的区块链服务"""
        if not settings.WEB3_RPC_URL:
            logger.warning("⚠️ WEB3_RPC_URL not configured, using mock mode")
            self.mock_mode = True
            return
        
        try:
            self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))
            if not self.w3.is_connected():
                logger.warning("⚠️ Cannot connect to blockchain node, using mock mode")
                self.mock_mode = True
                return
            
            logger.info(f"✅ Connected to {settings.BLOCKCHAIN_NETWORK}")
            logger.info(f"   Latest block: {self.w3.eth.block_number}")
        except Exception as e:
            logger.warning(f"⚠️ Blockchain connection failed: {e}, using mock mode")
            self.mock_mode = True
            return
        
        # 读取代币合约地址（支持别名）
        token_address = settings.DATA_TOKEN_ADDRESS or settings.PAYMENT_TOKEN_ADDRESS
        if token_address:
            try:
                self.token_service = DataTokenService(
                    self.w3,
                    token_address,
                    settings.PRIVATE_KEY
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to init DataToken service: {e}")
        
        # 读取市场合约地址（支持别名）
        market_address = settings.MARKET_CONTRACT_ADDRESS or settings.CONTRACT_ADDRESS
        eth_market_address = settings.ETH_MARKET_CONTRACT_ADDRESS
        
        # 根据市场类型初始化相应的市场服务
        if settings.MARKET_TYPE == "token" and market_address:
            try:
                self.market_service = MarketService(
                    self.w3,
                    market_address,
                    settings.PRIVATE_KEY
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to init Market service: {e}")
        elif settings.MARKET_TYPE == "eth" and eth_market_address:
            try:
                self.eth_market_service = ETHMarketService(
                    self.w3,
                    eth_market_address,
                    settings.PRIVATE_KEY
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to init ETH Market service: {e}")
        
        # 如果没有配置任何市场服务，回退到 mock 模式
        if not self.market_service and not self.eth_market_service:
            logger.warning("⚠️ No market service configured, market operations will use mock mode")
            self.mock_mode = True
    
    # ============ Token 相关方法 ============
    
    def get_token_balance(self, address: str) -> Dict:
        """获取 DTK 代币余额"""
        if self.mock_mode:
            return {"balance": 1000000, "formatted": "1000000 DTK"}
        
        if not self.token_service:
            return {"error": "Token service not configured"}
        
        balance = self.token_service.get_balance(address)
        decimals = settings.DATA_TOKEN_DECIMALS
        formatted = balance / (10 ** decimals)
        
        return {
            "balance": balance,
            "formatted": f"{formatted} DTK",
            "decimals": decimals,
        }
    
    def approve_tokens(self, spender: str, amount: int) -> Dict:
        """授权代币"""
        if self.mock_mode:
            return {"success": True, "tx_hash": f"0x{'a' * 64}", "message": "Mock approve"}
        
        if not self.token_service:
            return {"success": False, "error": "Token service not configured"}
        
        return self.token_service.approve(spender, amount)
    
    # ============ Market 相关方法 ============
    
    def list_data(self, data_hash: str, price: int = None) -> Dict:
        """上架数据到市场"""
        price = price or settings.DEFAULT_LISTING_PRICE
        
        if self.mock_mode:
            self._mock_listing_counter += 1
            return {
                "success": True,
                "listing_id": self._mock_listing_counter,
                "tx_hash": f"0x{'a' * 64}",
                "network": settings.BLOCKCHAIN_NETWORK,
                "message": "Data listed successfully (mock mode)",
            }
        
        if settings.MARKET_TYPE == "token":
            if not self.market_service:
                return {"success": False, "error": "Market service not configured"}
            return self.market_service.list_data(data_hash, price)
        else:
            if not self.eth_market_service:
                return {"success": False, "error": "ETH Market service not configured"}
            return self.eth_market_service.list_data(data_hash, price)
    
    def purchase_access(self, listing_id: int, value: int = None) -> Dict:
        """购买数据访问权"""
        if self.mock_mode:
            return {
                "success": True,
                "tx_hash": f"0x{'b' * 64}",
                "message": "Access purchased successfully (mock mode)",
            }
        
        if settings.MARKET_TYPE == "token":
            if not self.market_service:
                return {"success": False, "error": "Market service not configured"}
            return self.market_service.purchase_access(listing_id)
        else:
            if not self.eth_market_service:
                return {"success": False, "error": "ETH Market service not configured"}
            if value is None:
                return {"success": False, "error": "Value (ETH amount) required for ETH market"}
            return self.eth_market_service.purchase_access(listing_id, value)
    
    def remove_listing(self, listing_id: int) -> Dict:
        """下架数据"""
        if self.mock_mode:
            return {"success": True, "tx_hash": f"0x{'c' * 64}", "message": "Listing removed (mock)"}
        
        if settings.MARKET_TYPE == "token" and self.market_service:
            return self.market_service.remove_listing(listing_id)
        elif self.eth_market_service:
            return self.eth_market_service.remove_listing(listing_id)
        
        return {"success": False, "error": "Market service not configured"}
    
    def get_listing_details(self, listing_id: int) -> Dict:
        """获取上架详情"""
        if self.mock_mode:
            return {
                "listing_id": listing_id,
                "user": settings.MOCK_WALLET_ADDRESS,
                "data_hash": "ipfs://QmMockHash",
                "price": 100,
                "is_active": True,
                "created_at": 1234567890,
            }
        
        if settings.MARKET_TYPE == "token" and self.market_service:
            return self.market_service.get_listing_details(listing_id)
        elif self.eth_market_service:
            return self.eth_market_service.get_listing_details(listing_id)
        
        return {"error": "Market service not configured"}
    
    def get_active_listings(self) -> List[int]:
        """获取所有活跃的上架列表"""
        if self.mock_mode:
            return [1, 2, 3]
        
        if settings.MARKET_TYPE == "token" and self.market_service:
            return self.market_service.get_active_listings()
        elif self.eth_market_service:
            return self.eth_market_service.get_active_listings()
        
        return []
    
    def check_access(self, enterprise: str, listing_id: int) -> bool:
        """检查访问权限"""
        if self.mock_mode:
            return True
        
        if settings.MARKET_TYPE == "token" and self.market_service:
            return self.market_service.check_access(enterprise, listing_id)
        elif self.eth_market_service:
            return self.eth_market_service.check_access(enterprise, listing_id)
        
        return False
    
    # ============ 兼容旧接口 ============
    
    def mint_context_nft(self, user_address: str, metadata_url: str, price_wei: int = None) -> Dict:
        """
        兼容旧的 mint_context_nft 接口
        实际上调用 list_data 上架数据
        """
        try:
            normalized_address = normalize_address(user_address)
        except ValueError as e:
            return {"success": False, "error": str(e), "message": f"Invalid address: {e}"}
        
        result = self.list_data(metadata_url, price_wei or settings.DEFAULT_LISTING_PRICE)
        
        # 转换返回格式以兼容旧接口
        if result.get("success"):
            return {
                "success": True,
                "token_id": result.get("listing_id"),
                "tx_hash": result.get("tx_hash"),
                "network": settings.BLOCKCHAIN_NETWORK,
                "message": result.get("message", "Data listed successfully"),
            }
        return result