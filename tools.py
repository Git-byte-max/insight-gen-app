import pandas as pd
import matplotlib.pyplot as plt
from crewai.tools import BaseTool
import io
import sys

# Global variable to hold the DataFrame
df = None

class ExecuteCodeTool(BaseTool):
    name: str = "execute_code"
    description: str = (
        "Executes a Python code snippet. "
        "The variable 'df' is available as a pandas DataFrame. "
        "If you create a plot, save it as 'plot.png'. "
        "Always print the final answer or result to stdout."
    )
    
    def _run(self, code_snippet: str) -> str:
        global df
        
        # Capture standard output
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

# Instantiate the tool so agents can import it
execute_code = ExecuteCodeTool()
