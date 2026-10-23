import pytest
import unittest.mock as mock
import asyncio
from backend.agent.llm_agent import ArhieaAgent
from backend.config import settings

@pytest.fixture
def test_agent():
    return ArhieaAgent()

@pytest.mark.asyncio
async def test_openrouter_claude_3_5_sonnet_flow(test_agent):
    """Test switching to Claude 3.5 Sonnet and processing conversational response."""
    with mock.patch("backend.config.settings.OPENROUTER_API_KEY", "sk-or-v1-mock-test-key"):
        with mock.patch("backend.config.settings.OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"):
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": "Claude 3.5 Sonnet response: The speed of light is approximately 299,792 km/s."
                    }
                }]
            }

            with mock.patch("httpx.AsyncClient.post", return_value=mock_response):
                res = await test_agent.process_message("What is the speed of light?")
                assert "299,792" in res["response"]
                assert "Claude 3.5 Sonnet" in res["response"]
                assert res["verified"] is True

@pytest.mark.asyncio
async def test_openrouter_gpt_4o_tool_calling_flow(test_agent):
    """Test switching to OpenAI GPT-4o and verifying tool execution cycle."""
    with mock.patch("backend.config.settings.OPENROUTER_API_KEY", "sk-or-v1-mock-test-key"):
        with mock.patch("backend.config.settings.OPENROUTER_MODEL", "openai/gpt-4o"):
            # First turn: GPT-4o calls get_system_time
            tool_call_response = mock.MagicMock()
            tool_call_response.status_code = 200
            tool_call_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": None,
                        "tool_calls": [{
                            "id": "call_123",
                            "function": {
                                "name": "get_system_time",
                                "arguments": "{}"
                            }
                        }]
                    }
                }]
            }

            # Second turn: GPT-4o formats the answer
            final_response = mock.MagicMock()
            final_response.status_code = 200
            final_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": "The current time has been checked and verified."
                    }
                }]
            }

            with mock.patch("httpx.AsyncClient.post", side_effect=[tool_call_response, final_response]):
                res = await test_agent.process_message("What time is it in my system?")
                assert "The current time has been checked" in res["response"]
                assert res["verified"] is True

@pytest.mark.asyncio
async def test_openrouter_deepseek_r1_reasoning_flow(test_agent):
    """Test switching to DeepSeek R1 reasoning model."""
    with mock.patch("backend.config.settings.OPENROUTER_API_KEY", "sk-or-v1-mock-test-key"):
        with mock.patch("backend.config.settings.OPENROUTER_MODEL", "deepseek/deepseek-r1"):
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": "DeepSeek R1 reasoning: The prime factors of 360 are 2^3 * 3^2 * 5."
                    }
                }]
            }

            with mock.patch("httpx.AsyncClient.post", return_value=mock_response):
                res = await test_agent.process_message("What are the prime factors of 360?")
                assert "2^3 * 3^2 * 5" in res["response"]
                assert res["verified"] is True

@pytest.mark.asyncio
async def test_openrouter_llama_3_3_70b_flow(test_agent):
    """Test switching to Meta Llama 3.3 70B Instruct."""
    with mock.patch("backend.config.settings.OPENROUTER_API_KEY", "sk-or-v1-mock-test-key"):
        with mock.patch("backend.config.settings.OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct"):
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": "Llama 3.3 says: Photosynthesis converts light energy into chemical energy."
                    }
                }]
            }

            with mock.patch("httpx.AsyncClient.post", return_value=mock_response):
                res = await test_agent.process_message("Explain photosynthesis briefly.")
                assert "chemical energy" in res["response"]
                assert res["verified"] is True

@pytest.mark.asyncio
async def test_direct_gemini_2_5_flash_flow(test_agent):
    """Test direct Google Gemini 2.5 Flash API with valid AIzaSy API key."""
    with mock.patch("backend.config.settings.OPENROUTER_API_KEY", ""):
        with mock.patch("backend.config.settings.GEMINI_API_KEY", "AIzaSyMockTestKeyValidFormat123456"):
            mock_response = mock.MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": "Gemini 2.5 Flash: Mitochondria are known as the powerhouses of the cell."
                        }]
                    }
                }]
            }

            with mock.patch("httpx.AsyncClient.post", return_value=mock_response):
                res = await test_agent.process_message("What is the powerhouse of the cell?")
                assert "Mitochondria" in res["response"]
                assert res["verified"] is True

@pytest.mark.asyncio
async def test_autonomous_knowledge_engine_fallback(test_agent):
    """Test that when cloud AI is unreachable or offline, the autonomous engine handles it."""
    with mock.patch("backend.config.settings.OPENROUTER_API_KEY", ""):
        with mock.patch("backend.config.settings.GEMINI_API_KEY", ""):
            res = await test_agent.process_message("Who was Isaac Newton?")
            assert res is not None
            assert len(res["response"]) > 20
            assert any(term in res["response"].lower() for term in ["newton", "mathematician", "physicist", "gravity", "calculus", "motion"])
