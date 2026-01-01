import pandas as pd
import sys
from io import StringIO
from langchain.tools import tool

# Global placeholder for the dataframe
# This gets updated by app.py when a file is uploaded
df = None

@tool("execute_code_tool")
def execute_code_tool(code: str):
    """
    Executes the given Python code string.
    The code has access to a pandas dataframe named 'df'.
    It captures and returns any content printed to stdout (print statements).
    """
    global df
    
    # Create a buffer to capture print() statements
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    
    try:
        # Create a safe execution environment with access to 'df' and 'pd'
        local_vars = {"df": df, "pd": pd}
        
        # Execute the code
        exec(code, globals(), local_vars)
        
        # Restore stdout
        sys.stdout = old_stdout
        
        # Return the captured logs
        output = redirected_output.getvalue()
        if not output:
            return "Code executed successfully (No output printed)."
        return output

    except Exception as e:
        sys.stdout = old_stdout
        return f"Execution Error: {e}"
