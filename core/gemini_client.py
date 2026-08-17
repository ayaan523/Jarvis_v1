import os
import time
import logging
from google import genai
from google.genai import types
from google.genai.errors import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lazy loaded client
_client = None

def get_client():
    global _client
    if _client is None:
        _client = genai.Client()  # Picks up GEMINI_API_KEY from env
    return _client

def _map_messages_to_gemini(messages):
    """
    Maps a list of dicts [{'role': 'system'/'user'/'assistant', 'content': '...'}, ...]
    to a tuple of (system_instruction_string, list_of_types_Content).
    """
    system_instructions = []
    contents = []
    
    for msg in messages:
        role = msg.get('role', 'user')
        text = msg.get('content', '')
        
        if role == 'system':
            system_instructions.append(text)
        else:
            gemini_role = "model" if role == "assistant" else "user"
            contents.append(types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=text)]
            ))
            
    # Combine system instructions
    system_text = "\n".join(system_instructions) if system_instructions else None
    
    return system_text, contents


def _tool_config(system_instruction, tools=None, temperature=None):
    config = types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
    if temperature is not None:
        config.temperature = temperature
    if tools:
        declarations = [
            types.FunctionDeclaration(
                name=tool["function"]["name"],
                description=tool["function"].get("description", ""),
                parameters_json_schema=tool["function"].get("parameters", {}),
            )
            for tool in tools
            if tool.get("type") == "function"
        ]
        config.tools = [types.Tool(function_declarations=declarations)]
    return config

def stream_chat_response(model_name: str, messages: list, max_retries: int = 3):
    """
    Yields chunks of text from Gemini API, handling exponential backoff for 429s.
    """
    client = get_client()
    system_instruction, contents = _map_messages_to_gemini(messages)
    
    config = types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
        
    retries = 0
    base_delay = 2.0
    
    while True:
        try:
            response = client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=config
            )
            for chunk in response:
                if chunk.text:
                    yield chunk.text
            return # Success, exit retry loop
            
        except APIError as e:
            # Check for 429 Too Many Requests
            if e.code == 429 and retries < max_retries:
                delay = base_delay * (2 ** retries)
                logger.warning(f"Rate limited (429). Retrying in {delay} seconds...")
                time.sleep(delay)
                retries += 1
            else:
                logger.error(f"Gemini API Error: {e}")
                raise e
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini API: {e}")
            raise e

def generate_chat_response(model_name: str, messages: list, max_retries: int = 3, temperature: float = None):
    """
    Returns the full text from Gemini API, handling exponential backoff.
    """
    client = get_client()
    system_instruction, contents = _map_messages_to_gemini(messages)
    
    config = types.GenerateContentConfig()
    if system_instruction:
        config.system_instruction = system_instruction
    if temperature is not None:
        config.temperature = temperature
        
    retries = 0
    base_delay = 2.0
    
    while True:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            return response.text
            
        except APIError as e:
            if e.code == 429 and retries < max_retries:
                delay = base_delay * (2 ** retries)
                logger.warning(f"Rate limited (429). Retrying in {delay} seconds...")
                time.sleep(delay)
                retries += 1
            else:
                logger.error(f"Gemini API Error: {e}")
                raise e
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini API: {e}")
            raise e


def generate_with_tools(model_name: str, messages: list, tools: list, execute_tool,
                        max_retries: int = 3, temperature: float = None):
    """Execute one Gemini function-calling round trip and return final text."""
    client = get_client()
    system_instruction, contents = _map_messages_to_gemini(messages)
    config = _tool_config(system_instruction, tools, temperature)
    retries = 0
    while True:
        try:
            response = client.models.generate_content(model=model_name, contents=contents, config=config)
            calls = list(getattr(response, "function_calls", None) or [])
            if not calls:
                return response.text or ""
            model_content = response.candidates[0].content
            responses = []
            for call in calls:
                name = call.name
                arguments = dict(call.args or {})
                result = execute_tool(name, arguments)
                responses.append(types.Part.from_function_response(name=name, response={"result": result}))
            contents.extend([model_content, types.Content(role="user", parts=responses)])
            final_response = client.models.generate_content(model=model_name, contents=contents, config=config)
            return final_response.text or ""
        except APIError as error:
            if error.code == 429 and retries < max_retries:
                delay = 2.0 * (2 ** retries)
                logger.warning("Rate limited (429). Retrying in %s seconds...", delay)
                time.sleep(delay)
                retries += 1
                continue
            raise
