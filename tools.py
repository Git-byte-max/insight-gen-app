import pandas as pd
import matplotlib.pyplot as plt
from langchain.tools import tool
import io
import sys
import os

# Global variable to hold the DataFrame
# This will be populated by app.py when a file is uploaded
df = None

@tool("execute_code")
def execute_code(code_snippet: str):
    """
    Executes a Python code snippet. The variable 'df' is available as a pandas DataFrame.
    If you create a plot, save it as 'plot.png'.
    Always print the final answer or result to stdout.
    """
    global df
    
    # Capture standard output to return it to the agent
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    try:
        # Create a local environment for execution
        local_scope = {"df": df, "pd": pd, "plt": plt}
        
        # Execute the code
        exec(code_snippet, globals(), local_scope)
        
        # Get the standard output
        output = redirected_output.getvalue()
        return f"Execution Successful. Output:\n{output}"

    except Exception as e:
        return f"Error executing code: {e}"
    
    finally:
        # Restore standard output
        sys.stdout = old_stdout
