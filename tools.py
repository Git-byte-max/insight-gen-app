import pandas as pd
import sys
from io import StringIO
from crewai.tools import BaseTool

# Global placeholder for the dataframe
df = None

class ExecuteCodeTool(BaseTool):
    name: str = "execute_code_tool"
    description: str = (
        "Executes the given Python code string. "
        "The code has access to a pandas dataframe named 'df'. "
        "It captures and returns any content printed to stdout."
    )

    def _run(self, code: str) -> str:
        global df
        
        # Create a buffer to capture print() statements
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        
        try:
            # Create a safe execution environment
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

# Instantiate the tool so it can be imported
execute_code_tool = ExecuteCodeTool()
