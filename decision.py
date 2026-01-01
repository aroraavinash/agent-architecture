# decision.py

from pydantic import BaseModel, Field
from typing import List, Optional, Union, Tuple, Any
import re
from models import validate_input, function_schemas

class Decision():
    
    def __init__(self, response_text: str):
        print("response_text")
        print(response_text)
        self.response_text = response_text

    def get_decision(self) -> str:
        """
        Parse the LLM response and return the appropriate function name
        """
        # Look for FUNCTION_CALL in any line
        function_call_line = None
        for line in self.response_text.split('\n'):
            line = line.strip()
            if line.startswith("FUNCTION_CALL:"):
                function_call_line = line
                break
        
        if function_call_line:
            # Parse FUNCTION_CALL
            _, function_info = function_call_line.split(":", 1)
            parts = [p.strip() for p in function_info.split("|")]
            func_name, params = parts[0], parts[1:]
        elif "FINAL_ANSWER:" in self.response_text:
            # Handle FINAL_ANSWER
            params = None
            func_name = None
        else:
            # No recognized pattern found
            params = None
            func_name = None
            
        return func_name, params
                        
                        