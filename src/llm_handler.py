from dotenv import load_dotenv
import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from chroma_storage import ChromaStorage

load_dotenv()
logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self, chroma_storage: Optional[ChromaStorage] = None):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "deepseek/deepseek-chat"
        self.chroma_storage = chroma_storage
        
        if not self.api_key:
            logger.error("OPENROUTER_API_KEY not found in environment variables")
            raise ValueError("OPENROUTER_API_KEY is required")
    
    def _get_system_prompt(self) -> str:
        return """You are an intelligent AI assistant with access to a local knowledge database. 

IMPORTANT: You have access to a search_knowledge tool that can search through local documents. Use this tool frequently to provide accurate, context-aware responses. When answering questions, ALWAYS search for relevant information first before responding.

The search tool is extremely powerful - use it liberally to:
- Find relevant information for any topic
- Get context before answering questions
- Verify facts and details
- Provide comprehensive responses based on available knowledge

Be thorough in your searches and always provide detailed, helpful responses based on the information you find."""

    def _get_tools_schema(self) -> List[Dict]:
        if not self.chroma_storage or not self.chroma_storage.is_available():
            return []
        
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge",
                    "description": "Search through local knowledge database for relevant information. Use this tool frequently to find context and information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find relevant information"
                            },
                            "topic_context": {
                                "type": "string",
                                "description": "Additional context to improve search results"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def _execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name == "search_knowledge" and self.chroma_storage:
            query = arguments.get("query", "")
            topic_context = arguments.get("topic_context", "")
            max_results = arguments.get("max_results", 5)
            
            results = self.chroma_storage.search(query, topic_context, max_results)
            
            if not results:
                return f"No results found for query: {query}"
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                source = result.get('source', 'Unknown').split('\\')[-1]
                content = result.get('content', '')[:500] + "..." if len(result.get('content', '')) > 500 else result.get('content', '')
                formatted_results.append(f"Result {i} (from {source}):\n{content}\n")
            
            return "\n".join(formatted_results)
        
        return f"Unknown tool: {tool_name}"

    def prompt_ai(self, message: str, conversation_history: Optional[List[Dict]] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        
        tools_schema = self._get_tools_schema()
        if tools_schema:
            payload["tools"] = tools_schema
            payload["tool_choice"] = "auto"
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            if not response_data.get("choices"):
                logger.error(f"No choices in response: {response_data}")
                return "Error: No response received from AI"
            
            message_obj = response_data["choices"][0]["message"]
            
            # Handle tool calls
            if message_obj.get("tool_calls"):
                tool_results = []
                for tool_call in message_obj["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])
                    
                    result = self._execute_tool_call(function_name, arguments)
                    tool_results.append(f"Tool {function_name} result:\n{result}")
                
                # Make a second call with tool results
                messages.append(message_obj)
                messages.append({
                    "role": "tool",
                    "content": "\n\n".join(tool_results)
                })
                
                payload["messages"] = messages
                payload.pop("tools", None)
                payload.pop("tool_choice", None)
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                response_data = response.json()
                
                return response_data["choices"][0]["message"]["content"]
            
            return message_obj.get("content", "Error: No content in response")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return f"Error: Failed to communicate with AI service - {e}"
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return f"Error: Invalid response format - {e}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"Error: {e}"
