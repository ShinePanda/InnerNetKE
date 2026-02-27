"""
千问模型服务集成
"""
import logging
from typing import AsyncIterator, Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

import httpx
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..config import get_settings

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """对话消息"""
    role: str  # system, user, assistant
    content: str
    timestamp: datetime = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.now()


class QwenService:
    """千问模型服务"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_base = self.settings.qwen.api_base
        self.api_key = self.settings.qwen.api_key
        self.model_name = self.settings.qwen.model_name
        self.max_tokens = self.settings.qwen.max_tokens
        self.temperature = self.settings.qwen.temperature
        self.timeout = self.settings.qwen.timeout
        
        self.http_client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """发送对话请求"""
        url = f"{self.api_base}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": stream
        }
        
        logger.debug(f"Sending request to Qwen API: {url}")
        
        try:
            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """流式对话"""
        url = f"{self.api_base}/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": True
        }
        
        async with self.http_client.stream("POST", url, json=payload) as response:
            async for chunk in response.aiter_lines():
                if chunk.startswith("data: "):
                    data = chunk[6:]
                    if data == "[DONE]":
                        break
                    try:
                        import json
                        chunk_data = json.loads(data)
                        if content := chunk_data.get("choices", [{}])[0].get("delta", {}).get("content"):
                            yield content
                    except json.JSONDecodeError:
                        continue
    
    async def explain_code(
        self,
        code: str,
        context: Optional[str] = None,
        language: str = "cpp"
    ) -> str:
        """解释代码"""
        system_prompt = """You are an expert C++ code analyst. Your task is to provide clear, 
        comprehensive explanations of C++ code. Focus on:
        1. Overall purpose and functionality
        2. Key classes, functions, and their relationships
        3. Design patterns and architectural decisions
        4. Potential improvements and best practices
        
        Provide your explanation in a structured format with code examples where helpful.
        """
        
        user_content = f"## Code to Explain\n```{language}\n{code}\n```"
        
        if context:
            user_content += f"\n\n## Additional Context\n{context}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = await self.chat(messages)
        return response["choices"][0]["message"]["content"]
    
    async def review_code(
        self,
        code: str,
        file_path: Optional[str] = None,
        review_scope: str = "full"
    ) -> Dict[str, Any]:
        """审查代码"""
        scope_prompts = {
            "security": "Focus on security vulnerabilities, memory safety, and potential exploits.",
            "performance": "Focus on performance issues, algorithmic complexity, and resource usage.",
            "style": "Focus on coding style, naming conventions, and best practices.",
            "full": "Comprehensive review covering all aspects: security, performance, style, and correctness."
        }
        
        system_prompt = f"""You are an expert C++ code reviewer. Review the code for quality, 
        safety, and best practices. {scope_prompts.get(review_scope, scope_prompts["full"])}
        
        Output your review in JSON format:
        {{
            "summary": "Brief review summary",
            "score": 85,  // 0-100 score
            "issues": [
                {{
                    "line": 42,
                    "severity": "critical|error|warning|info",
                    "category": "memory_safety|performance|modern_cpp|design|...",
                    "message": "Issue description",
                    "suggestion": "How to fix it"
                }}
            ],
            "metrics": {{
                "complexity": "medium",
                "issues_count": 5
            }}
        }}
        """
        
        user_content = f"## Code to Review\n```cpp\n{code}\n```"
        
        if file_path:
            user_content += f"\n\nFile: {file_path}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = await self.chat(messages)
        import json
        
        try:
            # 尝试解析JSON响应
            content = response["choices"][0]["message"]["content"]
            # 提取JSON部分
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content)
            return result
        except (json.JSONDecodeError, KeyError, IndexError):
            # 如果JSON解析失败，返回原始响应
            logger.warning("Failed to parse JSON response from Qwen")
            return {
                "summary": response["choices"][0]["message"]["content"],
                "score": 50,
                "issues": [],
                "metrics": {"error": "Failed to parse structured response"}
            }
    
    async def suggest_refactoring(
        self,
        code: str,
        refactor_type: str,
        constraints: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """建议重构"""
        type_prompts = {
            "extract-method": "Suggest extracting complex code blocks into separate methods.",
            "inline-method": "Suggest inlining trivial methods.",
            "rename": "Suggest better variable and function names.",
            "simplify-conditionals": "Simplify complex conditional logic.",
            "replace-inheritance": "Replace inheritance with composition where appropriate.",
            "modern-cpp": "Modernize C++ code to use current best practices.",
            "general": "Provide general refactoring suggestions."
        }
        
        constraint_text = "\n".join(constraints) if constraints else "No specific constraints."
        
        system_prompt = f"""You are an expert C++ refactoring specialist. 
        Analyze the code and suggest refactoring improvements.
        
        Refactoring Type: {refactor_type}
        {type_prompts.get(refactor_type, type_prompts["general"])}
        
        Constraints:
        {constraint_text}
        
        Output format:
        {{
            "current_state": "Description of current code structure",
            "issues": [
                {{
                    "issue": "Issue description",
                    "location": "line numbers or code section",
                    "impact": "high|medium|low"
                }}
            ],
            "suggestions": [
                {{
                    "pattern": "Pattern name",
                    "description": "What and why",
                    "before_code": "...",
                    "after_code": "...",
                    "benefits": ["benefit1", "benefit2"],
                    "risks": ["risk1", "risk2"]
                }}
            ],
            "estimated_improvements": {{
                "maintainability": "+20%",
                "performance": "+10%"
            }}
        }}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"## Code to Refactor\n```cpp\n{code}\n```"}
        ]
        
        response = await self.chat(messages)
        import json
        
        try:
            content = response["choices"][0]["message"]["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            result = json.loads(content)
            return result
        except (json.JSONDecodeError, KeyError, IndexError):
            return {
                "summary": response["choices"][0]["message"]["content"],
                "error": "Failed to parse structured response"
            }
    
    async def generate_tests(
        self,
        code: str,
        test_framework: str = "gtest",
        coverage_level: str = "basic"
    ) -> Dict[str, Any]:
        """生成测试用例"""
        coverage_descriptions = {
            "basic": "Basic functionality tests (happy path)",
            "normal": "Normal coverage including edge cases",
            "comprehensive": "Full coverage including error handling and boundary conditions"
        }
        
        system_prompt = f"""You are an expert C++ test engineer. Generate comprehensive 
        unit tests for the provided code.
        
        Test Framework: {test_framework}
        Coverage Level: {coverage_descriptions.get(coverage_level, coverage_descriptions["basic"])}
        
        Output format:
        {{
            "test_cases": [
                {{
                    "name": "TestCaseName",
                    "description": "What this test verifies",
                    "test_code": "Test code with assertions",
                    "expected_behavior": "What the test expects",
                    "edge_cases": ["edge case 1", "edge case 2"]
                }}
            ],
            "coverage_notes": ["Note about coverage"]
        }}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"## Code to Test\n```cpp\n{code}\n```"}
        ]
        
        response = await self.chat(messages)
        import json
        
        try:
            content = response["choices"][0]["message"]["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            result = json.loads(content)
            return result
        except (json.JSONDecodeError, KeyError, IndexError):
            return {
                "summary": response["choices"][0]["message"]["content"],
                "error": "Failed to parse structured response"
            }
