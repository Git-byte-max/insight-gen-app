import pandas as pd
import sys
from io import StringIO
from langchain.tools import tool

# Global placeholder
df = None

@tool
def execute_code_tool(code: str) -> str:
    """
    Executes the given Python code string.
    The code has access to a pandas dataframe named 'df'.
    It captures and returns any content printed to stdout.
    """
    global df
    
    # Create buffer
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    
    try:
        local_vars = {"df": df, "pd": pd}
        exec(code, globals(), local_vars)
        sys.stdout = old_stdout
        output = redirected_output.getvalue()
        if not output:
            return "Code executed successfully (No output printed)."
        return output

    except Exception as e:
        sys.stdout = old_stdout
        return f"Execution Error: {e}"
