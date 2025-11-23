# IPFS/decentralized storage
import json
from typing import Dict, List, Optional

import ipfshttpclient

from ..config import settings
from ..models.chat_models import ChatMessage


class StorageService:
    def __init__(self):
        self.client = None
        try:
            self.client = ipfshttpclient.connect(settings.IPFS_API_URL)
        except Exception as e:
            print(f"IPFS connection failed: {e}. Using mock mode.")

    async def upload_conversation_metadata(
        self,
        messages: List[ChatMessage],
        user_address: str,
        title: str,
        description: Optional[str] = None,
    ) -> Dict:
        """Upload conversation to IPFS and return metadata URL."""

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

        if self.client:
            # Real IPFS upload
            ipfs_hash = self.client.add_json(metadata)
        else:
            # Mock IPFS for testing
            mock_hash = f"Qm{hash(json.dumps(metadata, sort_keys=True))}"
            ipfs_hash = mock_hash[:46]

        return {
            "metadataUrl": f"ipfs://{ipfs_hash}",
            "ipfs_hash": ipfs_hash,
            "gatewayUrl": f"{settings.IPFS_GATEWAY}{ipfs_hash}",
        }

    async def retrieve_conversation(self, ipfs_hash: str) -> Dict:
        """Retrieve conversation from IPFS."""
        if self.client:
            return self.client.get_json(ipfs_hash)
        return {"error": "IPFS client not available"}

