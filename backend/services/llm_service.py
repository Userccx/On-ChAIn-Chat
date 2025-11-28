# LLM service with OpenAI API support
import time
from typing import Dict, List, Optional

from ..config import settings
from ..models.chat_models import ChatMessage
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 尝试导入 OpenAI，如果未安装则使用 mock 模式
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Using mock mode.")


class LLMService:
    """LLM service supporting OpenAI API and mock mode."""

    def __init__(self):
        self.client = None
        self.use_mock = settings.USE_MOCK_SERVICES or not OPENAI_AVAILABLE
        
        # 如果配置了 API Key 且 OpenAI 可用，初始化客户端
        if not self.use_mock and settings.OPENAI_API_KEY:
            try:
                self.client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL,
                )
                logger.info(f"✅ Initialized OpenAI client with base URL: {settings.OPENAI_BASE_URL}")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI client: {e}")
                self.use_mock = True
        else:
            if self.use_mock:
                logger.info("Using mock LLM mode")
            else:
                logger.warning("OpenAI API key not configured. Using mock mode.")

    def get_response(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict:
        """
        Get response from LLM.
        
        Args:
            messages: List of chat messages
            model: Model name (defaults to DEFAULT_LLM_MODEL)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dict with reply, model_used, tokens_used, provider, latency_ms
        """
        start_time = time.time()
        
        # Mock mode
        if self.use_mock:
            logger.info(f"Getting mock response for {len(messages)} messages")
            reply = settings.MOCK_LLM_REPLY or "Hello world"
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "reply": reply,
                "model_used": model or settings.DEFAULT_LLM_MODEL,
                "tokens_used": len(reply.split()),
                "provider": "mock",
                "latency_ms": latency_ms,
            }
        
        # Real OpenAI API
        if not self.client:
            logger.error("OpenAI client not initialized. Falling back to mock.")
            return self._get_mock_response(model)
        
        try:
            # 转换消息格式
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # 如果没有 system message，添加默认的
            if not any(msg.get("role") == "system" for msg in formatted_messages):
                formatted_messages.insert(0, {
                    "role": "system",
                    "content": "You are a helpful assistant."
                })
            
            # 调用 API
            logger.info(f"Calling OpenAI API with model: {model or settings.DEFAULT_LLM_MODEL}")
            logger.debug(f"Messages: {formatted_messages}")
            
            response = self.client.chat.completions.create(
                model=model or settings.DEFAULT_LLM_MODEL,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # 提取回复
            reply = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            latency_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"✅ Got response from OpenAI (tokens: {tokens_used}, latency: {latency_ms}ms)")
            
            return {
                "reply": reply,
                "model_used": response.model,
                "tokens_used": tokens_used,
                "provider": "openai",
                "latency_ms": latency_ms,
            }
            
        except Exception as e:
            logger.error(f"❌ OpenAI API call failed: {e}")
            # 发生错误时返回 mock 响应
            return self._get_mock_response(model, error=str(e))
    
    def _get_mock_response(self, model: Optional[str] = None, error: Optional[str] = None) -> Dict:
        """Get mock response (fallback)."""
        reply = error or settings.MOCK_LLM_REPLY or "Hello world"
        return {
            "reply": reply,
            "model_used": model or settings.DEFAULT_LLM_MODEL,
            "tokens_used": len(reply.split()),
            "provider": "mock",
            "latency_ms": 0,
        }


