# IPFS/decentralized storage with Pinata cloud persistence
import hashlib
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import requests

from ..config import settings
from ..models.chat_models import ChatMessage, Conversation, MintRecord
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 尝试导入 ipfshttpclient（仅 local 模式需要）
try:
    import ipfshttpclient
    IPFS_CLIENT_AVAILABLE = True
except ImportError:
    IPFS_CLIENT_AVAILABLE = False
    logger.info("ipfshttpclient not installed. Local IPFS mode unavailable.")


class StorageService:
    """
    IPFS 存储服务 - 支持 Pinata 云端持久化
    
    数据类型:
    - conversation: 完整对话（包含所有消息和状态）
    - mint_record: NFT 铸造记录
    
    Pinata 元数据结构:
    {
        "name": "conversation_0x1234..._abc123",
        "keyvalues": {
            "wallet_address": "0x1234...",
            "type": "conversation" | "mint_record",
            "conversation_id": "abc123",
            "app": "tokenized_llm_platform"
        }
    }
    """
    
    APP_IDENTIFIER = "tokenized_llm_platform"
    
    def __init__(self):
        self.client = None
        self.pinning_service = settings.IPFS_PINNING_SERVICE.lower()
        
        # 初始化服务
        if self.pinning_service == "local":
            self._init_local_ipfs()
        elif self.pinning_service == "pinata":
            self._init_pinata()
        else:
            logger.info("📝 Storage service running in MOCK mode (no IPFS)")
        
        # 本地缓存
        self._conversation_cache: Dict[str, Conversation] = {}  # conversation_id -> Conversation
        self._mint_record_cache: Dict[str, MintRecord] = {}  # mint_id -> MintRecord
        self._data_cache: Dict[str, Dict] = {}  # ipfs_hash -> data

    # ============ 初始化方法 ============

    def _init_local_ipfs(self):
        """初始化本地 IPFS 节点"""
        if not IPFS_CLIENT_AVAILABLE:
            logger.warning("⚠️ ipfshttpclient not installed. Falling back to mock mode.")
            self.pinning_service = "none"
            return
        
        try:
            ipfs_address = self._convert_to_multiaddr(settings.IPFS_API_URL)
            self.client = ipfshttpclient.connect(ipfs_address)
            logger.info(f"✅ Connected to local IPFS node at {settings.IPFS_API_URL}")
        except Exception as e:
            logger.warning(f"⚠️ Local IPFS connection failed: {e}. Using mock mode.")
            self.pinning_service = "none"

    def _init_pinata(self):
        """初始化 Pinata 服务"""
        has_jwt = settings.PINATA_JWT and settings.PINATA_JWT.strip()
        has_api_key = (settings.PINATA_API_KEY and settings.PINATA_API_KEY.strip() and
                      settings.PINATA_SECRET_KEY and settings.PINATA_SECRET_KEY.strip())
        
        if not (has_jwt or has_api_key):
            logger.warning("⚠️ Pinata credentials not configured.")
            self.pinning_service = "none"
        else:
            if self._verify_pinata_credentials():
                logger.info(f"✅ Pinata service initialized successfully")
            else:
                logger.warning("⚠️ Pinata credentials verification failed. Using mock mode.")
                self.pinning_service = "none"

    def _get_pinata_headers(self) -> Dict[str, str]:
        """获取 Pinata API 请求头"""
        headers = {"Content-Type": "application/json"}
        
        if settings.PINATA_JWT and settings.PINATA_JWT.strip():
            headers["Authorization"] = f"Bearer {settings.PINATA_JWT.strip()}"
        elif settings.PINATA_API_KEY and settings.PINATA_SECRET_KEY:
            headers["pinata_api_key"] = settings.PINATA_API_KEY.strip()
            headers["pinata_secret_api_key"] = settings.PINATA_SECRET_KEY.strip()
        
        return headers

    def _verify_pinata_credentials(self) -> bool:
        """验证 Pinata 凭证"""
        try:
            headers = self._get_pinata_headers()
            response = requests.get(
                "https://api.pinata.cloud/data/testAuthentication",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Pinata connection error: {e}")
            return False

    def _convert_to_multiaddr(self, url: str) -> str:
        """将 HTTP URL 转换为 IPFS Multiaddr 格式"""
        if url.startswith("http://"):
            url = url[7:]
        elif url.startswith("https://"):
            url = url[8:]
        
        if ":" in url:
            host, port = url.split(":", 1)
        else:
            host = url
            port = "5001"
        
        try:
            import ipaddress
            ip = ipaddress.ip_address(host)
            if isinstance(ip, ipaddress.IPv4Address):
                return f"/ip4/{host}/tcp/{port}"
            else:
                return f"/ip6/{host}/tcp/{port}"
        except ValueError:
            return f"/dns4/{host}/tcp/{port}"

    # ============ 通用存储方法 ============

    def _generate_id(self) -> str:
        """生成唯一 ID"""
        return str(uuid.uuid4())

    def _generate_mock_hash(self, data: Dict) -> str:
        """生成模拟的 IPFS 哈希"""
        content = json.dumps(data, sort_keys=True, default=str)
        hash_digest = hashlib.sha256(content.encode()).hexdigest()
        return f"Qm{hash_digest[:44]}"

    def _upload_to_pinata(
        self,
        data: Dict,
        name: str,
        wallet_address: str,
        data_type: str,
        extra_keyvalues: Optional[Dict] = None
    ) -> Optional[str]:
        """上传 JSON 数据到 Pinata"""
        url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
        headers = self._get_pinata_headers()
        
        keyvalues = {
            "wallet_address": wallet_address.lower(),
            "type": data_type,
            "app": self.APP_IDENTIFIER,
            "timestamp": datetime.now().isoformat(),
        }
        if extra_keyvalues:
            keyvalues.update(extra_keyvalues)
        
        payload = {
            "pinataContent": data,
            "pinataMetadata": {
                "name": name,
                "keyvalues": keyvalues
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            ipfs_hash = result.get("IpfsHash")
            logger.info(f"📌 Uploaded to Pinata: {ipfs_hash} (type: {data_type})")
            return ipfs_hash
        except Exception as e:
            logger.error(f"❌ Failed to upload to Pinata: {e}")
            return None

    def _query_pinata_pins(
        self,
        wallet_address: Optional[str] = None,
        data_type: Optional[str] = None,
        conversation_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """查询 Pinata 上的 pins"""
        if self.pinning_service != "pinata":
            return []
        
        url = "https://api.pinata.cloud/data/pinList"
        headers = self._get_pinata_headers()
        
        params = {"status": "pinned", "pageLimit": limit}
        
        keyvalues = {"app": {"value": self.APP_IDENTIFIER, "op": "eq"}}
        if wallet_address:
            keyvalues["wallet_address"] = {"value": wallet_address.lower(), "op": "eq"}
        if data_type:
            keyvalues["type"] = {"value": data_type, "op": "eq"}
        if conversation_id:
            keyvalues["conversation_id"] = {"value": conversation_id, "op": "eq"}
        
        params["metadata"] = json.dumps({"keyvalues": keyvalues})
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get("rows", [])
        except Exception as e:
            logger.error(f"❌ Failed to query Pinata pins: {e}")
            return []

    def _retrieve_from_gateway(self, ipfs_hash: str) -> Optional[Dict]:
        """通过网关检索 IPFS 内容"""
        if ipfs_hash in self._data_cache:
            return self._data_cache[ipfs_hash]
        
        gateways = [
            f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}",
            f"https://ipfs.io/ipfs/{ipfs_hash}",
            f"https://cloudflare-ipfs.com/ipfs/{ipfs_hash}",
        ]
        
        for gateway_url in gateways:
            try:
                response = requests.get(gateway_url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    self._data_cache[ipfs_hash] = data
                    return data
            except Exception:
                continue
        
        return None

    def _unpin_from_pinata(self, ipfs_hash: str) -> bool:
        """从 Pinata 取消固定"""
        url = f"https://api.pinata.cloud/pinning/unpin/{ipfs_hash}"
        headers = self._get_pinata_headers()
        
        try:
            response = requests.delete(url, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"🗑️ Unpinned from Pinata: {ipfs_hash}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Failed to unpin: {e}")
            return False

    # ============ 对话管理方法 ============

    def create_conversation(self, wallet_address: str, title: str = "New Conversation") -> Conversation:
        """创建新对话"""
        conversation = Conversation(
            id=self._generate_id(),
            wallet_address=wallet_address.lower(),
            title=title,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        # 缓存
        self._conversation_cache[conversation.id] = conversation
        
        # 立即保存到 IPFS
        self._save_conversation_to_ipfs(conversation)
        
        logger.info(f"🆕 Created conversation {conversation.id} for {wallet_address[:10]}...")
        return conversation

    def get_conversation(self, conversation_id: str, wallet_address: str) -> Optional[Conversation]:
        """获取对话"""
        wallet_key = wallet_address.lower()
        
        # 从缓存获取
        if conversation_id in self._conversation_cache:
            convo = self._conversation_cache[conversation_id]
            if convo.wallet_address.lower() == wallet_key:
                return convo
        
        # 从 Pinata 获取
        if self.pinning_service == "pinata":
            convo = self._load_conversation_from_pinata(conversation_id, wallet_key)
            if convo:
                self._conversation_cache[conversation_id] = convo
                return convo
        
        return None

    def _load_conversation_from_pinata(self, conversation_id: str, wallet_address: str) -> Optional[Conversation]:
        """从 Pinata 加载对话"""
        pins = self._query_pinata_pins(
            wallet_address=wallet_address,
            data_type="conversation",
            conversation_id=conversation_id,
            limit=10
        )
        
        if not pins:
            return None
        
        # 按时间排序，获取最新版本
        pins.sort(key=lambda x: x.get("date_pinned", ""), reverse=True)
        latest_pin = pins[0]
        ipfs_hash = latest_pin.get("ipfs_pin_hash")
        
        if ipfs_hash:
            data = self._retrieve_from_gateway(ipfs_hash)
            if data:
                try:
                    # 重建 Conversation 对象
                    messages = [ChatMessage(**msg) for msg in data.get("messages", [])]
                    convo = Conversation(
                        id=data.get("id", conversation_id),
                        wallet_address=data.get("wallet_address", wallet_address),
                        title=data.get("title", "Untitled"),
                        messages=messages,
                        created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                        updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
                        ipfs_hash=ipfs_hash,
                    )
                    logger.info(f"📖 Loaded conversation {conversation_id} from Pinata")
                    return convo
                except Exception as e:
                    logger.error(f"Failed to parse conversation: {e}")
        
        return None

    def add_message_to_conversation(
        self,
        conversation_id: str,
        wallet_address: str,
        role: str,
        content: str,
    ) -> ChatMessage:
        """向对话添加消息"""
        wallet_key = wallet_address.lower()
        
        # 获取或创建对话
        conversation = self.get_conversation(conversation_id, wallet_key)
        if not conversation:
            conversation = self.create_conversation(wallet_key, content[:30])
            conversation.id = conversation_id  # 使用指定的 ID
        
        # 创建消息
        message = ChatMessage(
            id=self._generate_id(),
            role=role,
            content=content,
            timestamp=datetime.now(),
            is_minted=False,
        )
        
        # 添加到对话
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        
        # 更新缓存
        self._conversation_cache[conversation.id] = conversation
        
        # 保存到 IPFS
        self._save_conversation_to_ipfs(conversation)
        
        return message

    def _save_conversation_to_ipfs(self, conversation: Conversation) -> Optional[str]:
        """保存对话到 IPFS"""
        # 序列化对话
        data = {
            "id": conversation.id,
            "wallet_address": conversation.wallet_address,
            "title": conversation.title,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "is_minted": msg.is_minted,
                }
                for msg in conversation.messages
            ],
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }
        
        if self.pinning_service == "pinata":
            name = f"conversation_{conversation.wallet_address[:10]}_{conversation.id[:8]}"
            ipfs_hash = self._upload_to_pinata(
                data, name, conversation.wallet_address, "conversation",
                extra_keyvalues={"conversation_id": conversation.id}
            )
            if ipfs_hash:
                conversation.ipfs_hash = ipfs_hash
                return ipfs_hash
        elif self.pinning_service == "local" and self.client:
            ipfs_hash = self.client.add_json(data)
            self.client.pin.add(ipfs_hash)
            conversation.ipfs_hash = ipfs_hash
            return ipfs_hash
        
        # Mock 模式
        return self._generate_mock_hash(data)

    def get_user_conversations(self, wallet_address: str) -> List[Conversation]:
        """获取用户的所有对话"""
        wallet_key = wallet_address.lower()
        conversations = []
        
        if self.pinning_service == "pinata":
            # 从 Pinata 查询所有对话
            pins = self._query_pinata_pins(
                wallet_address=wallet_key,
                data_type="conversation",
                limit=1000
            )
            
            # 按 conversation_id 分组，只取最新版本
            convo_pins: Dict[str, Dict] = {}
            for pin in pins:
                metadata = pin.get("metadata", {})
                keyvalues = metadata.get("keyvalues", {})
                convo_id = keyvalues.get("conversation_id")
                
                if convo_id:
                    if convo_id not in convo_pins or pin.get("date_pinned", "") > convo_pins[convo_id].get("date_pinned", ""):
                        convo_pins[convo_id] = pin
            
            # 加载每个对话
            for convo_id, pin in convo_pins.items():
                ipfs_hash = pin.get("ipfs_pin_hash")
                if ipfs_hash:
                    data = self._retrieve_from_gateway(ipfs_hash)
                    if data:
                        try:
                            messages = [ChatMessage(**msg) for msg in data.get("messages", [])]
                            convo = Conversation(
                                id=data.get("id", convo_id),
                                wallet_address=data.get("wallet_address", wallet_key),
                                title=data.get("title", "Untitled"),
                                messages=messages,
                                created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                                updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
                                ipfs_hash=ipfs_hash,
                            )
                            conversations.append(convo)
                            self._conversation_cache[convo.id] = convo
                        except Exception as e:
                            logger.error(f"Failed to parse conversation: {e}")
        else:
            # 从缓存获取
            for convo in self._conversation_cache.values():
                if convo.wallet_address.lower() == wallet_key:
                    conversations.append(convo)
        
        # 按更新时间排序
        conversations.sort(key=lambda x: x.updated_at, reverse=True)
        
        logger.info(f"📚 Retrieved {len(conversations)} conversations for {wallet_key[:10]}...")
        return conversations

    def update_message_mint_status(
        self,
        conversation_id: str,
        wallet_address: str,
        message_ids: List[str],
        is_minted: bool
    ) -> bool:
        """更新消息的铸造状态"""
        conversation = self.get_conversation(conversation_id, wallet_address)
        if not conversation:
            return False
        
        # 更新消息状态
        for msg in conversation.messages:
            if msg.id in message_ids:
                msg.is_minted = is_minted
        
        conversation.updated_at = datetime.now()
        self._conversation_cache[conversation.id] = conversation
        
        # 保存到 IPFS
        self._save_conversation_to_ipfs(conversation)
        
        return True

    # ============ NFT 铸造记录方法 ============

    def create_mint_record(
        self,
        conversation: Conversation,
        message_ids: List[str],
        ipfs_hash: str,
        metadata_url: str,
        gateway_url: str,
        tx_hash: Optional[str] = None,
        token_id: Optional[int] = None,
        listing_id: Optional[int] = None,
    ) -> MintRecord:
        """创建 NFT 铸造记录"""
        mint_record = MintRecord(
            id=self._generate_id(),
            conversation_id=conversation.id,
            message_ids=message_ids,
            wallet_address=conversation.wallet_address,
            ipfs_hash=ipfs_hash,
            metadata_url=metadata_url,
            gateway_url=gateway_url,
            tx_hash=tx_hash,
            token_id=token_id,
            listing_id=listing_id,
            price=0,
            is_listed=False,
            owner_address=conversation.wallet_address,
            minted_at=datetime.now(),
        )
        
        # 缓存
        self._mint_record_cache[mint_record.id] = mint_record
        
        # 保存到 IPFS
        self._save_mint_record_to_ipfs(mint_record)
        
        # 更新消息的铸造状态
        self.update_message_mint_status(
            conversation.id,
            conversation.wallet_address,
            message_ids,
            True
        )
        
        logger.info(f"🎨 Created mint record {mint_record.id} for conversation {conversation.id}")
        return mint_record

    def _save_mint_record_to_ipfs(self, mint_record: MintRecord) -> Optional[str]:
        """保存铸造记录到 IPFS"""
        data = {
            "id": mint_record.id,
            "conversation_id": mint_record.conversation_id,
            "message_ids": mint_record.message_ids,
            "wallet_address": mint_record.wallet_address,
            "ipfs_hash": mint_record.ipfs_hash,
            "metadata_url": mint_record.metadata_url,
            "gateway_url": mint_record.gateway_url,
            "tx_hash": mint_record.tx_hash,
            "token_id": mint_record.token_id,
            "listing_id": mint_record.listing_id,
            "price": mint_record.price,
            "is_listed": mint_record.is_listed,
            "owner_address": mint_record.owner_address,
            "minted_at": mint_record.minted_at.isoformat(),
        }
        
        if self.pinning_service == "pinata":
            name = f"mint_{mint_record.wallet_address[:10]}_{mint_record.id[:8]}"
            return self._upload_to_pinata(
                data, name, mint_record.wallet_address, "mint_record",
                extra_keyvalues={
                    "conversation_id": mint_record.conversation_id,
                    "mint_id": mint_record.id,
                }
            )
        
        return self._generate_mock_hash(data)

    def get_mint_records(self, wallet_address: str) -> List[MintRecord]:
        """获取用户的所有铸造记录"""
        wallet_key = wallet_address.lower()
        records = []
        
        if self.pinning_service == "pinata":
            pins = self._query_pinata_pins(
                wallet_address=wallet_key,
                data_type="mint_record",
                limit=1000
            )
            
            for pin in pins:
                ipfs_hash = pin.get("ipfs_pin_hash")
                if ipfs_hash:
                    data = self._retrieve_from_gateway(ipfs_hash)
                    if data:
                        try:
                            record = MintRecord(
                                id=data.get("id"),
                                conversation_id=data.get("conversation_id"),
                                message_ids=data.get("message_ids", []),
                                wallet_address=data.get("wallet_address"),
                                ipfs_hash=data.get("ipfs_hash"),
                                metadata_url=data.get("metadata_url"),
                                gateway_url=data.get("gateway_url"),
                                tx_hash=data.get("tx_hash"),
                                token_id=data.get("token_id"),
                                listing_id=data.get("listing_id"),
                                price=data.get("price", 0),
                                is_listed=data.get("is_listed", False),
                                owner_address=data.get("owner_address"),
                                minted_at=datetime.fromisoformat(data.get("minted_at", datetime.now().isoformat())),
                            )
                            records.append(record)
                            self._mint_record_cache[record.id] = record
                        except Exception as e:
                            logger.error(f"Failed to parse mint record: {e}")
        else:
            for record in self._mint_record_cache.values():
                if record.wallet_address.lower() == wallet_key:
                    records.append(record)
        
        records.sort(key=lambda x: x.minted_at, reverse=True)
        return records

    def get_mint_record_by_conversation(self, conversation_id: str, wallet_address: str) -> Optional[MintRecord]:
        """根据对话 ID 获取铸造记录"""
        records = self.get_mint_records(wallet_address)
        for record in records:
            if record.conversation_id == conversation_id:
                return record
        return None

    def update_mint_record_listing(
        self,
        mint_id: str,
        wallet_address: str,
        listing_id: int,
        price: float,
        is_listed: bool
    ) -> bool:
        """更新铸造记录的上架状态"""
        # 从缓存获取
        if mint_id in self._mint_record_cache:
            record = self._mint_record_cache[mint_id]
        else:
            # 从 Pinata 获取
            records = self.get_mint_records(wallet_address)
            record = next((r for r in records if r.id == mint_id), None)
        
        if not record:
            return False
        
        record.listing_id = listing_id
        record.price = price
        record.is_listed = is_listed
        
        self._mint_record_cache[mint_id] = record
        self._save_mint_record_to_ipfs(record)
        
        return True

    # ============ NFT 元数据上传 ============

    def upload_nft_metadata(
        self,
        conversation: Conversation,
        message_ids: Optional[List[str]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict:
        """上传 NFT 元数据到 IPFS"""
        # 筛选要铸造的消息
        if message_ids:
            messages_to_mint = [m for m in conversation.messages if m.id in message_ids]
        else:
            messages_to_mint = conversation.messages
            message_ids = [m.id for m in messages_to_mint]
        
        # 构建 NFT 元数据
        metadata = {
            "name": title or conversation.title,
            "description": description or f"Tokenized conversation by {conversation.wallet_address}",
            "owner": conversation.wallet_address,
            "conversation_id": conversation.id,
            "message_ids": message_ids,
            "conversation": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
                for msg in messages_to_mint
            ],
            "created_at": datetime.now().isoformat(),
        }
        
        # 上传到 IPFS
        if self.pinning_service == "pinata":
            name = f"nft_{conversation.wallet_address[:10]}_{conversation.id[:8]}"
            ipfs_hash = self._upload_to_pinata(
                metadata, name, conversation.wallet_address, "nft_metadata",
                extra_keyvalues={"conversation_id": conversation.id}
            )
        elif self.pinning_service == "local" and self.client:
            ipfs_hash = self.client.add_json(metadata)
            self.client.pin.add(ipfs_hash)
        else:
            ipfs_hash = self._generate_mock_hash(metadata)
        
        return {
            "ipfs_hash": ipfs_hash,
            "metadataUrl": f"ipfs://{ipfs_hash}",
            "gatewayUrl": f"{settings.IPFS_GATEWAY}{ipfs_hash}",
            "message_ids": message_ids,
        }

    # ============ 辅助方法 ============

    def get_service_status(self) -> Dict:
        """获取存储服务状态"""
        return {
            "service": self.pinning_service,
            "available": self.pinning_service != "none",
            "gateway": settings.IPFS_GATEWAY,
            "app_identifier": self.APP_IDENTIFIER,
            "cached_conversations": len(self._conversation_cache),
            "cached_mint_records": len(self._mint_record_cache),
        }

    def retrieve_content(self, ipfs_hash: str) -> Optional[Dict]:
        """检索 IPFS 内容"""
        return self._retrieve_from_gateway(ipfs_hash)

    def unpin_content(self, ipfs_hash: str) -> bool:
        """取消固定 IPFS 内容"""
        if self.pinning_service == "pinata":
            return self._unpin_from_pinata(ipfs_hash)
        elif self.pinning_service == "local" and self.client:
            try:
                self.client.pin.rm(ipfs_hash)
                return True
            except Exception:
                return False
        return False
