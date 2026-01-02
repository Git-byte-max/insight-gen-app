import pandas as pd
import sys
import os
from io import StringIO
from crewai.tools import BaseTool

# Global placeholder (fallback)
df = None

class ExecuteCodeTool(BaseTool):
    name: str = "execute_code_tool"
    description: str = (
        "Executes Python code. "
        "The code has access to the dataset via 'df'. "
        "It captures print() output."
    )

    def _run(self, code: str) -> str:
        # Create buffer to capture print output
        old_stdout = sys.stdout
        redirected_output = sys.stdout = StringIO()
        
        try:
            # CRITICAL FIX: Load the file directly from disk to ensure accuracy
            # This prevents the agent from losing the data context
            if os.path.exists("dataset.csv"):
                # We reload it inside the tool to be 100% sure
                local_df = pd.read_csv("dataset.csv")
            else:
                # Fallback to global if file is missing (rare)
                global df
                local_df = df

            # Execution Environment
            # We pass 'df' (the loaded csv), 'pd', and 'os' to the code
            local_vars = {"df": local_df, "pd": pd, "os": os}
            
            # Execute the code
            exec(code, globals(), local_vars)
            
            # Capture output
            sys.stdout = old_stdout
            output = redirected_output.getvalue()
            
            if not output:
                return "Code executed successfully. (No output printed? Remember to use print() to see results)."
            return output

        except Exception as e:
            sys.stdout = old_stdout
            return f"Execution Error: {e}"

# Instantiate the tool
execute_code_tool = ExecuteCodeTool()
