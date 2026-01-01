"""
Action Layer - Task Execution Module
==================================

This layer handles the execution of specific tasks including:
1. Mathematical operations (ASCII conversion, exponential sums)
2. Paint interactions (open, draw rectangle, add text)
3. Email sending
4. Utility functions (calculations, verifications)

Each function supports validation of inputs/outputs using Pydantic models.
Paint operations use pywinauto for GUI automation.
"""

from typing import Dict, Any, Union, Optional, Tuple, List
import math
import time
import os
import json
import asyncio
import subprocess
#import win32gui
#import win32con
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from PIL import Image, ImageDraw, ImageFont
# from pywinauto.application import Application
# from pywinauto.keyboard import send_keys
# from pywinauto import mouse, findwindows
# from pywinauto.controls.hwndwrapper import HwndWrapper
import logging

from models import validate_input, validate_output, function_schemas
#from logger import mcp_server_logger
import inspect


# Gmail configuration
app_password = os.getenv('GMAIL_APP_PASSWORD')  # App-specific password

# Global paint instance
paint_app = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextContent:
    """Response content wrapper with type information."""
    def __init__(self, text: str, type: str = "text"):
        self.type = type
        self.text = text
        
    def __repr__(self):
        return f"{self.type}: {self.text}"
    
    @staticmethod
    def create(text: str) -> 'TextContent':
        """Helper to create a TextContent with default type."""
        return TextContent(text=str(text))

class Action:
    def __init__(self):
        # Map tool names to bound methods so they can be called from an Action instance
        self.func_map = {
            'add': self.add,
            'add_list': self.add_list,
            'subtract': self.subtract,
            'multiply': self.multiply,
            'divide': self.divide,
            'power': self.power,
            'sqrt': self.sqrt,
            'cbrt': self.cbrt,
            'factorial': self.factorial,
            'log': self.log,
            'remainder': self.remainder,
            'sin': self.sin,
            'cos': self.cos,
            'tan': self.tan,
            'strings_to_chars_to_int': self.strings_to_chars_to_int,
            'int_list_to_exponential_sum': self.int_list_to_exponential_sum,
            'fibonacci_numbers': self.fibonacci_numbers,
            'show_reasoning': self.show_reasoning,
            'calculate': self.calculate,
            'verify': self.verify,
            # 'add_text_in_paint': self.add_text_in_paint,  # Windows only
            # 'open_paint': self.open_paint,  # Windows only
            'create_image_with_text': self.create_image_with_text,  # Mac compatible
            'open_image_in_preview': self.open_image_in_preview,  # Mac - opens in Preview
            'send_email': self.send_email,
        }

    async def act(self, func_name: str, params: Union[List[Any], Dict[str, Any]]) -> Any:
        """Execute a tool by name with the given parameters.
        
        Args:
            func_name: Name of the tool to execute (must be in func_map)
            params: List of parameters or dictionary of named parameters
            
        Returns:
            Result of the tool execution
            
        Raises:
            ValueError: If tool doesn't exist or parameters are invalid
        """
        try:
            # Find the matching tool
            tool = self.func_map.get(func_name)
            if not tool:
                logger.info(f"DEBUG: Available tools: {list(self.func_map.keys())}")
                raise ValueError(f"Unknown tool: {func_name}")

            # Get function signature
            sig = inspect.signature(tool)
            arguments = {}
            
            # Handle parameters based on their type
            if isinstance(params, dict):
                # Dictionary params - use as is after validation
                for name, value in params.items():
                    if name not in sig.parameters:
                        raise ValueError(f"Unknown parameter {name} for {func_name}")
                    arguments[name] = value
            else:
                # List params - map to parameter names in order
                param_names = [name for name in sig.parameters 
                             if name != 'self']
                
                # Special handling for functions that expect a single list parameter
                if func_name == 'int_list_to_exponential_sum' and len(param_names) == 1:
                    logger.info(f"DEBUG: Special handling for int_list_to_exponential_sum")
                    logger.info(f"DEBUG: Raw params: {params}")
                    logger.info(f"DEBUG: Param count: {len(params)}")
                    
                    # If we have multiple params but function expects 1 list, combine them
                    if len(params) > 1:
                        logger.info(f"DEBUG: Combining multiple params into list")
                        arguments[param_names[0]] = params  # Pass all params as a list
                    else:
                        # Single parameter - handle normally
                        value = params[0]
                        logger.info(f"DEBUG: Single param value: {value}")
                        logger.info(f"DEBUG: Value type: {type(value)}")
                        
                        if isinstance(value, str):
                            if value.startswith('[') and value.endswith(']'):
                                try:
                                    clean_list = value.strip('[]')
                                    if clean_list:
                                        value = [item.strip().strip("'\"") for item in clean_list.split(',')]
                                    else:
                                        value = []
                                    logger.info(f"DEBUG: Parsed list value: {value}")
                                except Exception as e:
                                    logger.info(f"Failed to parse list parameter: {e}")
                            elif value.startswith('{') and '"numbers"' in value:
                                try:
                                    import json
                                    data = json.loads(value)
                                    value = data.get('numbers', [])
                                    logger.info(f"DEBUG: Parsed JSON value: {value}")
                                except json.JSONDecodeError as e:
                                    logger.info(f"Failed to parse JSON parameter: {e}")
                                    # Keep original value and let the function handle it
                        arguments[param_names[0]] = value
                    
                    logger.info(f"DEBUG: Final arguments for int_list_to_exponential_sum: {arguments}")
                else:
                    # Normal parameter handling
                    if len(params) != len(param_names):
                        raise ValueError(
                            f"Expected {len(param_names)} parameters for {func_name}, got {len(params)}")
                    
                    for name, value in zip(param_names, params):
                        # Handle list parameters - if value looks like a list string
                        if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                            try:
                                # Convert string list "[1,2,3]" to actual list
                                clean_list = value.strip('[]')
                                if clean_list:  # Only split if not empty
                                    value = [item.strip().strip("'\"") for item in clean_list.split(',')]
                                else:
                                    value = []
                            except Exception as e:
                                logger.info(f"Failed to parse list parameter: {e}")
                        arguments[name] = value
                
                # # Convert the value to the correct type based on the schema
                # if param_type == 'integer':
                #     arguments[param_name] = int(value)
                # elif param_type == 'number':
                #     arguments[param_name] = float(value)
                # elif param_type == 'array':
                #     # Handle array input
                #     if isinstance(value, str):
                #         value = value.strip('[]').split(',')
                #     arguments[param_name] = [int(x.strip()) for x in value]
                # else:
                #     arguments[param_name] = str(value)

            logger.info(f"DEBUG: Final arguments: {arguments}")
            logger.info(f"DEBUG: Calling tool {func_name}")
            # Call async tools with await; run sync tools in a thread pool so the event loop is not blocked.
            try:
                if asyncio.iscoroutinefunction(tool):
                    result = await tool(**arguments)
                else:
                    loop = asyncio.get_running_loop()
                    maybe = await loop.run_in_executor(None, lambda: tool(**arguments))
                    # If a sync tool unexpectedly returned a coroutine, await it.
                    if asyncio.iscoroutine(maybe):
                        result = await maybe
                    else:
                        result = maybe
                    return result             
            except Exception as e:
                logger.exception(f"Error while calling tool {func_name}")
                raise
            # result = await session.call_tool(func_name, arguments=arguments)
        except Exception as e:
            logger.exception(f"Error in act method for tool {func_name}: {str(e)}")
            raise
            
        # Paint window handling
    #@staticmethod
    # async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    #     """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    #     global paint_app
    #     try:
    #         if not paint_app:
    #             return {
    #                 "content": [
    #                     TextContent(
    #                         type="text",
    #                         text="Paint is not open. Please call open_paint first."
    #                     )
    #                 ]
    #             }
            
    #         # Get the Paint window
    #         paint_window = paint_app.window(class_name='MSPaintApp')
            
    #         # Get primary monitor width to adjust coordinates
    #         # primary_width = GetSystemMetrics(0)
    #         # print(primary_width)
            
    #         # Ensure Paint window is active
    #         if not paint_window.has_focus():
    #             paint_window.set_focus()
    #             time.sleep(1.5)
            
    #         # paint_window.type_keys('r')  # Select rectangle tool 
    #         # paint_window.type_keys('r')  # Select rectangle tool
    #         # time.sleep(0.8)
    #         # Click on the Rectangle tool using the correct coordinates for secondary screen

    #         paint_window.click_input(coords=(661, 102 ))
    #         time.sleep(2.1)
            

            
    #         # print({"message": "input clicked"})

    #         # Get the canvas area
    #         # canvas = paint_window.child_window(class_name='MSPaintView')
    #         canvas = paint_window.child_window(class_name='MSPaintView', found_index=0)
    #         if not canvas.exists():
    #             for child in paint_window.descendants():
    #                 print(f"Descendant: class={child.friendly_class_name()}, handle={child.handle}, text={child.window_text()}")
    #         # paint_window.click_input(coords=(607, 102 ))
    #         # time.sleep(1.9)

    #         canvas_rect = canvas.rectangle()
    #         # print(canvas_rect)
    #         # Draw within canvas bounds

    #         canvas.press_mouse_input(coords=(x1, y1))
    #         time.sleep(2.1)

    #         # start = (canvas_rect.left + 607, canvas_rect.top + 425)
    #         # end = (canvas_rect.left + 940, canvas_rect.top + 619)


    #         # canvas.press_mouse_input(coords=start)
    #         # time.sleep(0.3)
    #         # canvas.move_mouse_input(coords=end)
    #         # time.sleep(0.3)
    #         # canvas.release_mouse_input(coords=end)
    #         # sys.stdout.flush()

    #         # # Use relative coordinates within canvas
    #         canvas.press_mouse_input(coords=(x1, y1))
    #         time.sleep(1.9)
    #         canvas.move_mouse_input(coords=(x2, y2))
    #         time.sleep(1.9)
    #         canvas.release_mouse_input(coords=(x2, y2))
    #         time.sleep(1.9)

    #         return {
    #             "content": [
    #                 TextContent(
    #                     type="text",
    #                     text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
    #                 )
    #             ]
    #         }
    #     except Exception as e:
    #         return {
    #             "content": [
    #                 TextContent(
    #                     type="text",
    #                     text=f"Error drawing rectangle: {str(e)}"
    #                 )
    #             ]
    #         }

    # Math and utility functions
    @staticmethod
    def add(a: Union[int, float, str], b: Union[int, float, str]) -> int:
        """Add two numbers together.
        
        Args:
            a: First number (will be converted to int)
            b: Second number (will be converted to int)
            
        Returns:
            Sum of a and b as integer
        """
        return int(a) + int(b)

    @staticmethod
    def add_list(numbers: List[Union[int, float, str]]) -> int:
        """Calculate the sum of a list of numbers.
        
        Args:
            numbers: List of numbers to sum (each will be converted to int)
            
        Returns:
            Sum of all numbers as integer
        """
        return sum(map(int, numbers))

    @staticmethod
    def subtract(a: Union[int, float, str], b: Union[int, float, str]) -> int:
        """Subtract b from a.
        
        Args:
            a: Number to subtract from (will be converted to int)
            b: Number to subtract (will be converted to int)
            
        Returns:
            Difference a - b as integer
        """
        return int(a) - int(b)

    @staticmethod
    def multiply(a: Union[int, float, str], b: Union[int, float, str]) -> int:
        """Multiply two numbers.
        
        Args:
            a: First number (will be converted to int)
            b: Second number (will be converted to int)
            
        Returns:
            Product of a and b as integer
        """
        return int(a) * int(b)

    @staticmethod
    def divide(a: Union[int, float, str], b: Union[int, float, str]) -> float:
        """Divide a by b.
        
        Args:
            a: Numerator (will be converted to float)
            b: Denominator (will be converted to float, must not be zero)
            
        Returns:
            Quotient a / b as float
            
        Raises:
            ZeroDivisionError: If b is zero
        """
        return float(a) / float(b)

    @staticmethod
    def power(a: Union[int, float, str], b: Union[int, float, str]) -> int:
        """Raise a to the power of b.
        
        Args:
            a: Base (will be converted to int)
            b: Exponent (will be converted to int)
            
        Returns:
            a ^ b as integer
        """
        return int(a) ** int(b)

    @staticmethod
    def sqrt(a: Union[int, float, str]) -> float:
        """Calculate the square root.
        
        Args:
            a: Non-negative number (will be converted to float)
            
        Returns:
            Square root of a as float
            
        Raises:
            ValueError: If a is negative
        """
        a = float(a)
        if a < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return a ** 0.5

    @staticmethod
    def cbrt(a: Union[int, float, str]) -> float:
        """Calculate the cube root.
        
        Args:
            a: Number (will be converted to float)
            
        Returns:
            Cube root of a as float
        """
        return float(a) ** (1/3)

    @staticmethod
    def factorial(a: Union[int, float, str]) -> int:
        """Calculate factorial.
        
        Args:
            a: Non-negative integer (will be converted to int)
            
        Returns:
            a! (factorial of a) as integer
            
        Raises:
            ValueError: If a is negative
        """
        a = int(a)
        if a < 0:
            raise ValueError("Factorial not defined for negative numbers")
        return math.factorial(a)

    @staticmethod
    def log(a: Union[int, float, str]) -> float:
        """Calculate natural logarithm.
        
        Args:
            a: Positive number (will be converted to float)
            
        Returns:
            Natural log of a as float
            
        Raises:
            ValueError: If a is not positive
        """
        a = float(a)
        if a <= 0:
            raise ValueError("Cannot calculate log of non-positive number")
        return math.log(a)

    @staticmethod
    def remainder(a: Union[int, float, str], b: Union[int, float, str]) -> int:
        """Calculate remainder of division.
        
        Args:
            a: Dividend (will be converted to int)
            b: Divisor (will be converted to int, must not be zero)
            
        Returns:
            Remainder of a / b as integer
            
        Raises:
            ZeroDivisionError: If b is zero
        """
        return int(a) % int(b)

    @staticmethod
    def sin(a: Union[int, float, str]) -> float:
        """Calculate sine of angle in radians.
        
        Args:
            a: Angle in radians (will be converted to float)
            
        Returns:
            Sine of a as float
        """
        return math.sin(float(a))

    @staticmethod
    def cos(a: Union[int, float, str]) -> float:
        """Calculate cosine of angle in radians.
        
        Args:
            a: Angle in radians (will be converted to float)
            
        Returns:
            Cosine of a as float
        """
        return math.cos(float(a))

    @staticmethod
    def tan(a: Union[int, float, str]) -> float:
        """Calculate tangent of angle in radians.
        
        Args:
            a: Angle in radians (will be converted to float)
            
        Returns:
            Tangent of a as float
        """
        return math.tan(float(a))

    @staticmethod
    def mine(a, b):
        return int(a) - int(b) - int(b)

    @staticmethod
    def strings_to_chars_to_int(text: str) -> List[int]:
        """Convert a string to a list of ASCII values.
        
        Args:
            text: The input string to convert to ASCII values
            
        Returns:
            List of integer ASCII values for each character
        """
        return [ord(char) for char in text]

    @staticmethod
    def int_list_to_exponential_sum(int_list: Union[List[Union[int, str]], str]) -> float:
        """Calculate sum of exponentials of integers in the list.
        
        Args:
            int_list: List of integers or string representation of a list
            
        Returns:
            Sum of e^x for each x in the list
            
        Raises:
            ValueError: If input can't be converted to list of integers
        """
        print(f"DEBUG: int_list_to_exponential_sum received: {repr(int_list)}")
        print(f"DEBUG: Type: {type(int_list)}")
        
        # Handle string input
        if isinstance(int_list, str):
            print(f"DEBUG: Processing string input: '{int_list}'")
            
            # Handle JSON string format like '{"numbers": [73, 78, 68, 73, 65]}'
            if int_list.startswith('{'):
                print("DEBUG: Detected JSON-like string")
                try:
                    import json
                    # Try to fix incomplete JSON by adding closing brackets
                    if not int_list.endswith('}'):
                        # Attempt to complete the JSON
                        if '"numbers": [' in int_list and not int_list.endswith(']}'):
                            # Count opening brackets and try to close them
                            open_brackets = int_list.count('[')
                            close_brackets = int_list.count(']')
                            open_braces = int_list.count('{')
                            close_braces = int_list.count('}')
                            
                            # Add missing closing brackets
                            missing_brackets = open_brackets - close_brackets
                            missing_braces = open_braces - close_braces
                            
                            completed_json = int_list + (']' * missing_brackets) + ('}' * missing_braces)
                            print(f"DEBUG: Attempting to complete JSON: '{completed_json}'")
                            int_list = completed_json
                    
                    data = json.loads(int_list)
                    int_list = data.get('numbers', [])
                    print(f"DEBUG: Parsed JSON successfully: {int_list}")
                except json.JSONDecodeError as e:
                    print(f"DEBUG: JSON parsing failed: {e}")
                    raise ValueError(f"Failed to parse JSON string '{int_list}': {e}")
            elif int_list.startswith('[') and int_list.endswith(']'):
                print("DEBUG: Detected list string format")
                # Parse string list "[1,2,3]" format
                clean_list = int_list.strip('[]')
                if clean_list:
                    int_list = [item.strip().strip("'\"") for item in clean_list.split(',')]
                else:
                    int_list = []
                print(f"DEBUG: Parsed list: {int_list}")
            elif ',' in int_list: # Handle comma-separated string without brackets
                print("DEBUG: Detected comma-separated format")
                try:
                    int_list = [item.strip().strip("'\"") for item in int_list.split(',')]
                    print(f"DEBUG: Parsed comma-separated: {int_list}")
                except Exception as e:
                    raise ValueError(f"Failed to parse comma-separated string as list: {e}")
            else:
                raise ValueError(f"String input must be in list format [x,y,z] or JSON format. Got: '{int_list}'")
        
        print(f"DEBUG: Final int_list before calculation: {int_list}")
        
        # Convert all items to int and calculate sum
        try:
            result = sum(math.exp(int(i)) for i in int_list)
            print(f"DEBUG: Calculation successful: {result}")
            return result
        except Exception as e:
            print(f"DEBUG: Calculation failed: {e}")
            print(f"DEBUG: int_list contents: {[repr(i) for i in int_list]}")
            raise

    @staticmethod
    def fibonacci_numbers(n):
        n = int(n)
        if n <= 0:
            return []
        fib_sequence = [0, 1]
        for _ in range(2, n):
            fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
        return fib_sequence[:n]

    @staticmethod
    def show_reasoning(steps):
        """Show reasoning steps, handling both list and string inputs.
        
        Args:
            steps: Either a list of steps or a string containing steps separated by periods
                  or semicolons.
        """
        print("Reasoning steps:")
        if isinstance(steps, str):
            # Split on either periods or semicolons, handle both delimiters
            if ';' in steps:
                steps_list = [s.strip() for s in steps.split(';') if s.strip()]
            else:
                steps_list = [s.strip() for s in steps.split('.') if s.strip()]
        else:
            steps_list = steps
            
        for i, step in enumerate(steps_list, 1):
            print(f"Step {i}: {step}")
        return "Reasoning shown"

    @staticmethod
    def calculate(expression: str) -> str:
        """Calculate result of a mathematical expression.
        
        Args:
            expression: String containing a valid Python math expression
            
        Returns:
            String representation of result or error message
        """
        try:
            result = eval(expression)
            print(f"Result: {result}")
            return str(result)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return error_msg

    @staticmethod
    def verify(expression: str, expected: Union[int, float, str]) -> str:
        """Verify if an expression evaluates to expected value.
        
        Args:
            expression: String containing a valid Python math expression
            expected: Expected result (will be converted to float)
            
        Returns:
            "True" if equal within tolerance, "False" otherwise
        """
        try:
            actual = float(eval(expression))
            is_correct = abs(actual - float(expected)) < 1e-10
            print(f"Verify: {expression} == {expected} ? {is_correct}")
            return str(is_correct)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return error_msg

    @staticmethod
    async def send_email(text: str) -> dict:
        """Send email with the text content"""
        try:

            # Gmail account details
            sender_email = "avinash.ai2022@gmail.com"
            receiver_email = "avinash.ai2022@gmail.com"

            # Create email
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = receiver_email
            msg["Subject"] = "Email tool sent via Action Module | EAG V2 Assignment 6"

            # Body of the email
            body = f"Hello, this is final answer to your question: {text}"
            msg.attach(MIMEText(body, "plain"))

            # Send email via Gmail's SMTP server
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.send_message(msg)

            #mcp_server_logger.info(f"Email sent successfully with content {text}")
            print("Email sent successfully with content {text}")
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Email sent successfully!"
                    )
                ]
            }
        except Exception as e:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text=f"Error sending mail: {str(e)}"
                    )
                ]
            }
        
    @staticmethod
    def show_reasoning(steps):
        """Show the step-by-step reasoning process.
        
        Args:
            steps: Either a list of steps or a string containing steps separated by
                  periods or semicolons.
        """
        print("\n=== Reasoning Steps ===")
        
        if isinstance(steps, str):
            # Split on either periods or semicolons, handle both delimiters
            if ';' in steps:
                steps_list = [s.strip() for s in steps.split(';') if s.strip()]
            else:
                steps_list = [s.strip() for s in steps.split('.') if s.strip()]
        else:
            steps_list = steps
            
        for i, step in enumerate(steps_list, 1):
            print(f"\nStep {i}:")
            print(f"  {step}")
            
        return "Reasoning shown"


    @staticmethod
    def calculate(expression: str) -> str:
        """Calculate the result of an expression"""
        print("\n=== Calculate ===")
        print(f"Expression: {expression}")
        try:
            result = eval(expression)
            print(f"Result: {result}")
            return str(result)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return error_msg

    @staticmethod
    def verify(expression: str, expected: float) -> str:
        """Verify if a calculation is correct"""
        print("\n=== Verify ===")
        print(f"Checking: {expression} = {expected}")
        try:
            actual = float(eval(expression))
            is_correct = abs(actual - float(expected)) < 1e-10
            
            if is_correct:
                print(f"✓ Correct! {expression} = {expected}")
            else:
                print(f"✗ Incorrect! {expression} should be {actual}, got {expected}")
                
            return str(is_correct)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return error_msg

    @staticmethod
    def create_image_with_text(text: str, filename: str = "final_answer.png") -> str:
        """Create an image with text - Mac compatible alternative to Paint.
        
        Args:
            text: Text to display in the image
            filename: Name of the output file (default: final_answer.png)
            
        Returns:
            Success message or error message
        """
        try:
            # Create a new image with white background (larger to accommodate wrapped text)
            width, height = 900, 500
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)
            
            # Try to use a system font, fallback to default if not available
            try:
                # Mac system fonts
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
                title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 28)
            except:
                try:
                    # Alternative Mac font
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
                    title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
                except:
                    # Fallback to default font
                    font = ImageFont.load_default()
                    title_font = ImageFont.load_default()
            
            # Add title
            title = "Final Answer"
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (width - title_width) // 2
            draw.text((title_x, 40), title, fill='black', font=title_font)
            
            # Function to wrap text to fit within specified width
            def wrap_text(text, font, max_width):
                words = text.split(' ')
                lines = []
                current_line = []
                
                for word in words:
                    test_line = ' '.join(current_line + [word])
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    line_width = bbox[2] - bbox[0]
                    
                    if line_width <= max_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                        else:
                            # Word is too long, break it
                            lines.append(word)
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                return lines
            
            # Prepare the result text with wrapping
            result_text = f"Result: {text}"
            max_text_width = width - 100  # Leave 50px margin on each side
            wrapped_lines = wrap_text(result_text, font, max_text_width)
            
            # If we have more than 3 lines, limit to 3 and add "..." to the last line
            if len(wrapped_lines) > 3:
                wrapped_lines = wrapped_lines[:2]
                last_line = wrapped_lines[1] if len(wrapped_lines) > 1 else wrapped_lines[0]
                # Truncate last line if needed and add ellipsis
                while True:
                    test_line = last_line + "..."
                    bbox = draw.textbbox((0, 0), test_line, font=font)
                    if bbox[2] - bbox[0] <= max_text_width:
                        wrapped_lines[1] = test_line
                        break
                    last_line = last_line[:-1]
                    if len(last_line) < 10:  # Prevent infinite loop
                        wrapped_lines[1] = last_line + "..."
                        break
            
            # Draw each line of text
            line_height = 35
            start_y = 120
            
            for i, line in enumerate(wrapped_lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                line_width = bbox[2] - bbox[0]
                line_x = (width - line_width) // 2
                line_y = start_y + (i * line_height)
                
                # Alternate colors for better readability
                color = 'blue' if i == 0 else 'darkblue'
                draw.text((line_x, line_y), line, fill=color, font=font)
            
            # Add additional info on separate lines
            info_lines = [
                "ASCII values of 'INDIA': [73, 78, 68, 73, 65]",
                f"Sum of exponentials: e^73 + e^78 + e^68 + e^73 + e^65"
            ]
            
            info_start_y = start_y + (len(wrapped_lines) * line_height) + 30
            info_font_size = 14
            
            try:
                info_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", info_font_size)
            except:
                info_font = font
            
            for i, info_line in enumerate(info_lines):
                bbox = draw.textbbox((0, 0), info_line, font=info_font)
                line_width = bbox[2] - bbox[0]
                line_x = (width - line_width) // 2
                line_y = info_start_y + (i * 25)
                draw.text((line_x, line_y), info_line, fill='gray', font=info_font)
            
            # Add a decorative rectangle border
            draw.rectangle([30, 20, width-30, height-30], outline='black', width=3)
            
            # Save the image
            image.save(filename)
            
            print(f"Image created successfully: {filename}")
            return f"Image created successfully: {filename}"
            
        except Exception as e:
            error_msg = f"Error creating image: {str(e)}"
            print(error_msg)
            return error_msg

    @staticmethod
    def open_image_in_preview(filename: str = "final_answer.png") -> str:
        """Open an image file in Mac Preview application.
        
        Args:
            filename: Name of the image file to open
            
        Returns:
            Success message or error message
        """
        try:
            import subprocess
            import os
            
            # Check if file exists
            if not os.path.exists(filename):
                return f"Error: File {filename} does not exist"
            
            # Open with Mac Preview using 'open' command
            subprocess.run(['open', '-a', 'Preview', filename], check=True)
            
            print(f"Opened {filename} in Preview")
            return f"Opened {filename} in Preview successfully"
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Error opening Preview: {str(e)}"
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            return error_msg

        
            
