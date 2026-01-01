import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial
import logging
from memory import Memory
from perception import Perception
from action import Action
from decision import Decision
import inspect
import json


# Create logger
logger = logging.getLogger('cot_logger')
logger.setLevel(logging.INFO)

# Create console handler and set level to INFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create file handler and set level to INFO
os.makedirs('logs', exist_ok=True)
file_handler = logging.FileHandler('logs/cot_process.log')
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 10
last_response = None 
iteration = 0
iteration_response = []


def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    logger.info("Starting main execution...")
    try:
        action = Action()
        # Get all tools and their descriptions
        tools = []
        for tool_name, tool_func in action.func_map.items():
            try:
                sig = inspect.signature(tool_func)
                params = []
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    param_type = param.annotation.__name__ if param.annotation != inspect._empty else "any"
                    params.append(f"{param_name}: {param_type}")
                
                # Get docstring if available
                doc = inspect.getdoc(tool_func) or "No description available"
                doc_first_line = doc.split('\n')[0]
                
                # Format tool description
                tool_desc = f"- {tool_name}({', '.join(params)}) - {doc_first_line}"
                tools.append(tool_desc)
                logger.info(f"Added description for tool: {tool_desc}")
            except Exception as e:
                logger.error(f"Error processing tool {tool_name}: {e}")
                continue
        
        # Sort tools alphabetically for consistent display
        tools.sort()
        tools_description = "\n".join(tools)
        logger.info("Successfully created tools description from ACTION.py")
                
        system_prompt = f"""You are a math agent solving problems iteratively using reasoning and mathematical tools.
First show your reasoning by calling appropriate tools, then calculate and verify each step.

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls:
   FUNCTION_CALL: function_name|value1|value2|...
   
2. For final answers:
   FINAL_ANSWER: [number or text]

Mandatory Rules:
- Think step-by-step before each tool call. Show your reasoning by calling appropriate tools.
- Before calling a tool, briefly explain your reasoning type (arithmetic, geometry, logic, algebra, lookup).
- Always process and understand all values returned by a function before moving to the next step.
- Use exact parameter names as shown in the tool descriptions.
- Pass all required parameters for each function call.
- Only output FINAL_ANSWER after all calculations are verified.
- Never repeat function calls with identical parameters.
- Call exactly one function at a time.

You have access to these tools:
- show_reasoning(steps: list) - Show your step-by-step reasoning process
- calculate(expression: str) - Calculate the result of an expression
- verify(expression: str, expected: float) - Verify if a calculation is correct
- 

Error Handling:
- If a tool fails or output seems inconsistent, issue a self-check by verifying the last result or re-evaluating inputs.
- If uncertainty remains, respond with:
  FUNCTION_CALL: verify|last_function|last_parameters

Self-Check Guidelines:
- After each calculation, internally verify that the result type and magnitude make sense.
- If verification fails, retry or pick an alternative computation path.

Examples:
User: Find the ASCII values of characters in INDIA and calculate sum of exponentials
Assistant: FUNCTION_CALL: show_reasoning|["1. Convert each character in INDIA to ASCII values", "2. Calculate exponential of each ASCII value", "3. Sum all exponentials", "4. Create image with result", "5. Send email with final answer"]
User: Start with the conversion.
Assistant: FUNCTION_CALL: strings_to_chars_to_int|INDIA
User: Now calculate the exponential sum.
Assistant: FUNCTION_CALL: int_list_to_exponential_sum|[73,78,68,73,65]
User: Create image with the result.
Assistant: FUNCTION_CALL: create_image_with_text|Result: 7.599e+33|result.png
User: Open it in Preview.
Assistant: FUNCTION_CALL: open_image_in_preview|result.png
User: Send email with the result.
Assistant: FUNCTION_CALL: send_email|Final answer: 7.599e+33
Assistant: FINAL_ANSWER: ALL TASKS COMPLETED

DO NOT include any explanations or additional text.
Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:"""
# - FUNCTION_CALL: send_email|89.37393e12

        #query = """Find the ASCII values of characters in INDIA and then return sum of exponentials of those values. After that, send email with the final answer."""
        query = """Find the ASCII values of characters in INDIA and then return sum of exponentials of those values. After getting the final answer, create an image with the result, open it in Preview, and send an email with the result."""
        # query = """Add two numbers 8 and 9, then multiply the result by 2."""
        logger.info("Starting iteration loop...")
        
        # Use global iteration variables
        global iteration, last_response
        logger.info("Fetching user preferences from memory...")
        memory = Memory()
        memory.set_preferences(preference="user likes blue color and bold text")
        user_preference = memory.get_preference()
        logger.info("Extracting key facts from perception.py")
        perception=Perception()
        facts = await perception.extract_facts_with_gemini(query)
        response_text = ""
        while iteration < max_iterations:
            logger.info(f"\n--- Iteration {iteration + 1} ---")
            if last_response is None:
                # Format facts dictionary into a string representation
                facts_str = f"Facts extracted: {json.dumps(facts, indent=2)}\n"
                current_query = f"{query}\n\nContext:\n{facts_str}User preferences: {user_preference}"
            else:
                current_query = current_query + "\n\n" + " ".join(iteration_response)
                current_query = current_query + "  What should I do next?"

            # Get model's response with timeout
            logger.info("Preparing to generate LLM response...")
            prompt = f"{system_prompt}\n\nQuery: {current_query}"
            
            try:
                response_text = await perception.generate_decision_response(system_prompt, current_query, client)
                logger.info(f"LLM Response: {response_text}")
                logger.info("Sending LLM response to the decision module...")
                decision= Decision(response_text=response_text)
                func_name, params = decision.get_decision()

                # Find the FUNCTION_CALL line in the response
                # logger.info(f"\nDEBUG: Raw function info: {function_info}")
                # logger.info(f"DEBUG: Split parts: {parts}")
                logger.info(f"DEBUG: Function name: {func_name}")
                logger.info(f"DEBUG: Raw parameters: {params}")
                logger.info(f"Decision is made, time to take ACTION - {func_name}")

                
                try:
                    if func_name:
                        result = await action.act(func_name, params)
                        logger.info(f"DEBUG: Raw result: {result}")
                        
                        # Get the full result content
                        if hasattr(result, 'content'):
                            logger.info(f"DEBUG: Result has content attribute")
                            # Handle multiple content items
                            if isinstance(result.content, list):
                                iteration_result = [
                                    item.text if hasattr(item, 'text') else str(item)
                                    for item in result.content
                                ]
                            else:
                                iteration_result = str(result.content)
                        else:
                            logger.info(f"DEBUG: Result has no content attribute")
                            iteration_result = str(result)
                            
                        logger.info(f"DEBUG: Final iteration result: {iteration_result}")
                        
                        # Format the response based on result type
                        if isinstance(iteration_result, list):
                            result_str = f"[{', '.join(iteration_result)}]"
                        else:
                            result_str = str(iteration_result)
                        
                        iteration_response.append(
                            f"In the {iteration + 1} iteration you called {func_name} with parameters {params} "
                            f"and the function returned {result_str}."
                        )
                        last_response = iteration_result    

                    else:
                        logger.info("FINAL_ANSWER received, ending iterations.")
                        iteration_response.append(f"FINAL_ANSWER received: {response_text}")
                        break
                except Exception as e:
                    logger.info(f"DEBUG: Error details: {str(e)}")
                    logger.info(f"DEBUG: Error type: {type(e)}")
                    iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                    break

         

                iteration += 1
            except Exception as e:
                logger.info(f"DEBUG: Error details: {str(e)}")
                logger.info(f"DEBUG: Error type: {type(e)}")
                iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                break
    except Exception as e:
        logger.info(f"Error in main execution: {e}")
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
