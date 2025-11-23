# Smart contract interaction (pseudo)
from datetime import datetime
from typing import Dict, List

from ..config import settings


class BlockchainService:
    def __init__(self):
        # Pseudo implementation - in production, connect to actual blockchain
        self.pseudo_mode = True
        self.deployed_contracts: Dict[int, Dict] = {}

    async def mint_context_nft(self, user_address: str, metadata_url: str) -> Dict:
        """
        Pseudo function to simulate minting NFT.
        In production, this would call the actual smart contract.
        """
        if not self.pseudo_mode:
            raise NotImplementedError("链上真实部署尚未连通。")

        token_id = len(self.deployed_contracts) + 1
        minted_at = datetime.utcnow().isoformat()
        record = {
            "owner": user_address,
            "metadata_url": metadata_url,
            "minted_at": minted_at,
            "network": settings.BLOCKCHAIN_NETWORK,
        }
        self.deployed_contracts[token_id] = record

        return {
            "success": True,
            "token_id": token_id,
            "tx_hash": f"0x{'a' * 64}",  # Mock transaction hash
            "network": settings.BLOCKCHAIN_NETWORK,
            "message": "NFT minted successfully (pseudo mode)",
        }

    async def get_user_nfts(self, user_address: str) -> List[Dict]:
        """Retrieve all NFTs owned by user (pseudo)."""
        return [
            {"token_id": tid, **data}
            for tid, data in self.deployed_contracts.items()
            if data["owner"].lower() == user_address.lower()
        ]

