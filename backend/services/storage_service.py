# IPFS/decentralized storage
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional

import ipfshttpclient
import requests

from ..config import settings
from ..models.chat_models import ChatMessage


class StorageService:
    def __init__(self):
        self.client = None
        self.pinning_service = settings.IPFS_PINNING_SERVICE.lower()
        
        # 初始化 IPFS 客户端（如果使用本地节点）
        if self.pinning_service == "local":
            try:
                self.client = ipfshttpclient.connect(settings.IPFS_API_URL)
                print(f"✅ Connected to local IPFS node at {settings.IPFS_API_URL}")
            except Exception as e:
                print(f"⚠️ Local IPFS connection failed: {e}. Using mock mode.")
                self.pinning_service = "none"
        elif self.pinning_service == "pinata":
            if not (settings.PINATA_JWT or (settings.PINATA_API_KEY and settings.PINATA_SECRET_KEY)):
                print("⚠️ Pinata credentials not configured. Pinning will be disabled.")
                self.pinning_service = "none"
        
        # 用于存储钱包地址到索引文件 IPFS 哈希的映射
        # 在真实模式下，这作为临时缓存，理想情况下应该存储在链上
        self._wallet_index_cache: Dict[str, str] = {}
        # 用于存储钱包地址到索引内容的映射
        # Mock 模式：存储实际索引数据
        # 真实模式：作为临时缓存，加速访问
        self._wallet_index_data: Dict[str, Dict] = {}  # wallet_key -> index_data
        # 用于跟踪已 pin 的内容（用于 unpin）
        self._pinned_hashes: Dict[str, Dict] = {}  # hash -> {service, pin_id, wallet_address}
        # 用于存储对话数据（Mock 模式，用于检索）
        # 真实模式下，数据从 IPFS 实时检索，但可以添加本地缓存优化
        self._chat_data_cache: Dict[str, Dict] = {}  # ipfs_hash -> chat_data

    def _get_wallet_index_key(self, wallet_address: str) -> str:
        """生成钱包索引文件的标识符（基于钱包地址的哈希）"""
        wallet_key = wallet_address.lower()
        # 使用钱包地址生成固定标识符，便于在 IPFS 中查找
        hash_obj = hashlib.sha256(wallet_key.encode())
        return f"wallet_index_{hash_obj.hexdigest()[:16]}"

    def _upload_to_ipfs(self, data: Dict) -> str:
        """上传数据到 IPFS 并返回哈希"""
        if self.client:
            ipfs_hash = self.client.add_json(data)
            # 自动 pin（如果使用本地节点）
            if self.pinning_service == "local":
                try:
                    self.client.pin.add(ipfs_hash)
                    print(f"📌 Pinned to local IPFS: {ipfs_hash}")
                except Exception as e:
                    print(f"⚠️ Failed to pin locally: {e}")
            return ipfs_hash
        else:
            # Mock IPFS for testing
            mock_hash = f"Qm{abs(hash(json.dumps(data, sort_keys=True)))}"
            return mock_hash[:46]
    
    def _pin_to_pinata(self, ipfs_hash: str, wallet_address: Optional[str] = None) -> Optional[Dict]:
        """
        使用 Pinata 服务固定 IPFS 内容
        
        Args:
            ipfs_hash: IPFS 内容哈希
            wallet_address: 钱包地址（用于元数据）
            
        Returns:
            包含 pin_id 的字典，如果失败返回 None
        """
        if self.pinning_service != "pinata":
            return None
        
        headers = {}
        if settings.PINATA_JWT:
            headers["Authorization"] = f"Bearer {settings.PINATA_JWT}"
        elif settings.PINATA_API_KEY and settings.PINATA_SECRET_KEY:
            headers["pinata_api_key"] = settings.PINATA_API_KEY
            headers["pinata_secret_api_key"] = settings.PINATA_SECRET_KEY
        else:
            return None
        
        # Pinata pin by hash API
        url = "https://api.pinata.cloud/pinning/pinByHash"
        
        payload = {
            "hashToPin": ipfs_hash,
            "pinataMetadata": {
                "name": f"chat_history_{wallet_address[:10] if wallet_address else 'unknown'}",
                "keyvalues": {
                    "wallet_address": wallet_address or "unknown",
                    "type": "chat_turn"
                }
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            pin_id = result.get("IpfsHash") or result.get("id")
            
            # 记录 pin 信息
            self._pinned_hashes[ipfs_hash] = {
                "service": "pinata",
                "pin_id": pin_id,
                "wallet_address": wallet_address,
                "pinned_at": datetime.now().isoformat()
            }
            
            print(f"📌 Pinned to Pinata: {ipfs_hash} (Pin ID: {pin_id})")
            return {"pin_id": pin_id, "ipfs_hash": ipfs_hash}
        except Exception as e:
            print(f"⚠️ Failed to pin to Pinata: {e}")
            return None
    
    def _unpin_from_pinata(self, ipfs_hash: str) -> bool:
        """
        从 Pinata 取消固定 IPFS 内容
        
        Args:
            ipfs_hash: IPFS 内容哈希
            
        Returns:
            成功返回 True，失败返回 False
        """
        if self.pinning_service != "pinata":
            return False
        
        pin_info = self._pinned_hashes.get(ipfs_hash)
        if not pin_info:
            print(f"⚠️ Pin info not found for hash: {ipfs_hash}")
            return False
        
        headers = {}
        if settings.PINATA_JWT:
            headers["Authorization"] = f"Bearer {settings.PINATA_JWT}"
        elif settings.PINATA_API_KEY and settings.PINATA_SECRET_KEY:
            headers["pinata_api_key"] = settings.PINATA_API_KEY
            headers["pinata_secret_api_key"] = settings.PINATA_SECRET_KEY
        else:
            return False
        
        # Pinata unpin API
        url = f"https://api.pinata.cloud/pinning/unpin/{ipfs_hash}"
        
        try:
            response = requests.delete(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # 移除记录
            self._pinned_hashes.pop(ipfs_hash, None)
            print(f"🗑️ Unpinned from Pinata: {ipfs_hash}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to unpin from Pinata: {e}")
            return False

    def _retrieve_from_ipfs(self, ipfs_hash: str) -> Optional[Dict]:
        """从 IPFS 检索数据"""
        if self.client:
            try:
                # 真实 IPFS：从 IPFS 节点检索
                data = self.client.get_json(ipfs_hash)
                # 可选：缓存到本地以加速后续访问
                if data:
                    self._chat_data_cache[ipfs_hash] = data
                return data
            except Exception as e:
                print(f"⚠️ Failed to retrieve from IPFS: {e}")
                # 如果 IPFS 检索失败，尝试从本地缓存获取（如果有）
                return self._chat_data_cache.get(ipfs_hash)
        else:
            # Mock mode: 从内存缓存中检索
            return self._chat_data_cache.get(ipfs_hash)

    def save_chat_turn(
        self,
        wallet_address: str,
        user_message: str,
        assistant_reply: str,
        model_used: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> Dict:
        """
        保存单次对话轮次到 IPFS，并更新钱包的对话索引
        
        Args:
            wallet_address: 用户钱包地址
            user_message: 用户消息
            assistant_reply: 助手回复
            model_used: 使用的模型
            timestamp: 时间戳
            
        Returns:
            包含 IPFS 哈希和网关 URL 的字典
        """
        if not timestamp:
            timestamp = datetime.now()

        # 构建单次对话记录
        chat_turn = {
            "wallet_address": wallet_address.lower(),
            "user_message": user_message,
            "assistant_reply": assistant_reply,
            "model_used": model_used,
            "timestamp": timestamp.isoformat(),
        }

        # 上传到 IPFS
        ipfs_hash = self._upload_to_ipfs(chat_turn)
        
        # 缓存对话数据以便后续快速检索（Mock 和真实模式都缓存）
        self._chat_data_cache[ipfs_hash] = chat_turn

        # 使用 Pinata pinning（如果配置）
        pin_result = None
        if self.pinning_service == "pinata":
            pin_result = self._pin_to_pinata(ipfs_hash, wallet_address)

        # 更新钱包的对话索引
        self._update_wallet_index(wallet_address, ipfs_hash)

        result = {
            "ipfs_hash": ipfs_hash,
            "metadataUrl": f"ipfs://{ipfs_hash}",
            "gatewayUrl": f"{settings.IPFS_GATEWAY}{ipfs_hash}",
            "timestamp": timestamp.isoformat(),
            "pinned": pin_result is not None,
        }
        
        if pin_result:
            result["pin_id"] = pin_result.get("pin_id")
        
        return result

    def _update_wallet_index(self, wallet_address: str, new_chat_hash: str) -> None:
        """更新钱包的对话索引，添加新的对话记录哈希"""
        wallet_key = wallet_address.lower()
        
        # 获取现有索引（从缓存或创建新索引）
        index = self._get_wallet_index(wallet_key)
        
        # 添加新的对话哈希（如果不存在）
        if new_chat_hash not in index.get("chat_hashes", []):
            index.setdefault("chat_hashes", []).append(new_chat_hash)
            index["last_updated"] = datetime.now().isoformat()
            
            # 上传更新后的索引到 IPFS
            index_hash = self._upload_to_ipfs(index)
            
            # 自动 pin 索引文件（如果配置了 pinning）
            if self.pinning_service == "pinata":
                self._pin_to_pinata(index_hash, wallet_address)
            elif self.pinning_service == "local" and self.client:
                try:
                    self.client.pin.add(index_hash)
                    print(f"📌 Pinned index to local IPFS: {index_hash}")
                except Exception as e:
                    print(f"⚠️ Failed to pin index locally: {e}")
            
            # 缓存索引数据和哈希（Mock 和真实模式都使用）
            # 注意：真实模式下这是临时缓存，理想情况下索引哈希应存储在链上
            self._wallet_index_cache[wallet_key] = index_hash
            self._wallet_index_data[wallet_key] = index  # 缓存实际索引内容
            
            print(f"💾 Updated wallet index for {wallet_key[:10]}... (Index hash: {index_hash})")

    def _get_wallet_index(self, wallet_address: str) -> Dict:
        """
        获取钱包的对话索引
        
        注意：在完全去中心化的场景中，索引文件的 IPFS 哈希可以：
        1. 存储在智能合约中（推荐）- 需要智能合约支持
        2. 使用固定命名规则通过 IPFS 查找
        3. 每次更新时返回新的索引哈希，由前端/链上存储
        
        当前实现：
        - Mock 模式：使用内存缓存
        - 真实模式：使用内存缓存作为临时方案，理想情况下应从链上获取索引哈希
        """
        wallet_key = wallet_address.lower()
        
        # 优先从内存缓存获取索引内容（Mock 和真实模式都支持）
        if wallet_key in self._wallet_index_data:
            return self._wallet_index_data[wallet_key]
        
        # 如果有缓存的索引哈希，尝试从 IPFS 检索（真实模式）
        if self.client and wallet_key in self._wallet_index_cache:
            index_hash = self._wallet_index_cache[wallet_key]
            try:
                index_data = self._retrieve_from_ipfs(index_hash)
                if index_data:
                    # 验证钱包地址匹配
                    if index_data.get("wallet_address", "").lower() == wallet_key:
                        # 缓存索引数据以便后续快速访问
                        self._wallet_index_data[wallet_key] = index_data
                        print(f"📖 Retrieved wallet index from IPFS: {index_hash}")
                        return index_data
                    else:
                        print(f"⚠️ Index wallet address mismatch: {index_data.get('wallet_address')} != {wallet_key}")
            except Exception as e:
                print(f"⚠️ Failed to retrieve index from IPFS: {e}")
        
        # 创建新索引（首次使用该钱包地址）
        new_index = {
            "wallet_address": wallet_key,
            "chat_hashes": [],
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }
        # 立即缓存新索引
        self._wallet_index_data[wallet_key] = new_index
        print(f"🆕 Created new wallet index for {wallet_key[:10]}...")
        return new_index

    def get_user_chat_history(self, wallet_address: str) -> List[Dict]:
        """
        获取用户的所有历史对话记录
        
        Args:
            wallet_address: 用户钱包地址
            
        Returns:
            按时间排序的对话记录列表
        """
        wallet_key = wallet_address.lower()
        
        # 获取索引
        index = self._get_wallet_index(wallet_key)
        chat_hashes = index.get("chat_hashes", [])
        
        # 从 IPFS 获取所有对话记录
        chat_history = []
        for chat_hash in chat_hashes:
            chat_data = self._retrieve_from_ipfs(chat_hash)
            if chat_data:
                chat_history.append(chat_data)
        
        # 按时间戳排序
        chat_history.sort(key=lambda x: x.get("timestamp", ""))
        
        return chat_history

    def upload_conversation_metadata(
        self,
        messages: List[ChatMessage],
        user_address: str,
        title: str,
        description: Optional[str] = None,
    ) -> Dict:
        """Upload conversation to IPFS and return metadata URL (保留用于 NFT 铸造)."""

        metadata = {
            "name": title,
            "description": description
            or f"Tokenized conversation by {user_address}",
            "owner": user_address,
            "conversation": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                    if msg.timestamp
                    else None,
                }
                for msg in messages
            ],
            "created_at": messages[-1].timestamp.isoformat() if messages else None,
        }

        ipfs_hash = self._upload_to_ipfs(metadata)

        return {
            "metadataUrl": f"ipfs://{ipfs_hash}",
            "ipfs_hash": ipfs_hash,
            "gatewayUrl": f"{settings.IPFS_GATEWAY}{ipfs_hash}",
        }

    def retrieve_conversation(self, ipfs_hash: str) -> Dict:
        """Retrieve conversation from IPFS."""
        result = self._retrieve_from_ipfs(ipfs_hash)
        if result:
            return result
        return {"error": "IPFS client not available or hash not found"}
    
    def unpin_content(self, ipfs_hash: str, wallet_address: Optional[str] = None) -> Dict:
        """
        取消固定 IPFS 内容（删除数据）
        
        Args:
            ipfs_hash: 要取消固定的 IPFS 哈希
            wallet_address: 钱包地址（用于验证所有权，可选）
            
        Returns:
            操作结果字典
        """
        result = {
            "ipfs_hash": ipfs_hash,
            "unpinned": False,
            "service": self.pinning_service,
        }
        
        if self.pinning_service == "local" and self.client:
            try:
                self.client.pin.rm(ipfs_hash)
                result["unpinned"] = True
                result["message"] = "Successfully unpinned from local IPFS node"
                print(f"🗑️ Unpinned from local IPFS: {ipfs_hash}")
            except Exception as e:
                result["error"] = str(e)
                result["message"] = f"Failed to unpin from local IPFS: {e}"
        elif self.pinning_service == "pinata":
            success = self._unpin_from_pinata(ipfs_hash)
            result["unpinned"] = success
            result["message"] = "Successfully unpinned from Pinata" if success else "Failed to unpin from Pinata"
        else:
            result["message"] = "Pinning service not configured or unavailable"
        
        return result
    
    def get_pinned_content(self, wallet_address: Optional[str] = None) -> List[Dict]:
        """
        获取已固定的内容列表
        
        Args:
            wallet_address: 钱包地址（可选，用于过滤）
            
        Returns:
            已固定内容的列表
        """
        if wallet_address:
            # 返回特定钱包的固定内容
            wallet_key = wallet_address.lower()
            return [
                {"ipfs_hash": hash, **info}
                for hash, info in self._pinned_hashes.items()
                if info.get("wallet_address", "").lower() == wallet_key
            ]
        else:
            # 返回所有固定内容
            return [
                {"ipfs_hash": hash, **info}
                for hash, info in self._pinned_hashes.items()
            ]
    
    def set_wallet_index_hash(self, wallet_address: str, index_hash: str) -> bool:
        """
        设置钱包索引文件的 IPFS 哈希（用于从链上或其他来源获取）
        
        这个方法允许从外部（如智能合约）设置索引哈希，然后从 IPFS 检索索引内容
        
        Args:
            wallet_address: 钱包地址
            index_hash: 索引文件的 IPFS 哈希
            
        Returns:
            成功返回 True
        """
        wallet_key = wallet_address.lower()
        self._wallet_index_cache[wallet_key] = index_hash
        
        # 如果 IPFS 客户端可用，立即尝试检索索引内容
        if self.client:
            try:
                index_data = self._retrieve_from_ipfs(index_hash)
                if index_data and index_data.get("wallet_address", "").lower() == wallet_key:
                    self._wallet_index_data[wallet_key] = index_data
                    print(f"✅ Loaded wallet index from IPFS: {index_hash}")
                    return True
            except Exception as e:
                print(f"⚠️ Failed to load index from IPFS: {e}")
        
        return True
    
    def get_wallet_index_hash(self, wallet_address: str) -> Optional[str]:
        """
        获取钱包索引文件的 IPFS 哈希
        
        这个方法返回索引文件的哈希，可以存储到链上或返回给前端
        
        Args:
            wallet_address: 钱包地址
            
        Returns:
            索引文件的 IPFS 哈希，如果不存在返回 None
        """
        wallet_key = wallet_address.lower()
        return self._wallet_index_cache.get(wallet_key)

