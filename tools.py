# CORRECT IMPORT: BaseTool is in crewai.tools, not crewai_tools
from crewai.tools import BaseTool
import pandas as pd
import matplotlib.pyplot as plt

# Global variable to hold the dataframe
df = None 

class ExecuteCodeTool(BaseTool):
    name: str = "Execute Python Code"
    description: str = "Executes python code. The dataframe is available as variable 'df'. If the code generates a plot, save it as 'plot.png'."

    def _run(self, code_string: str) -> str:
        global df
        try:
            # Safe-ish execution environment
            local_vars = {"df": df, "pd": pd, "plt": plt}
            exec(code_string, {}, local_vars)
            return "Code executed successfully. If a plot was created, it is saved as plot.png."
        except Exception as e:
            return f"Error executing code: {str(e)}. Please rewrite the code to fix this."

class GetColumnsTool(BaseTool):
    name: str = "Read Dataset Columns"
    description: str = "Returns the columns of the current dataset."

    def _run(self, dummy_input: str) -> str:
        global df
        if df is not None:
            return str(list(df.columns))
        return "No dataframe loaded."

# Instantiate tools so agents can use them
execute_code_tool = ExecuteCodeTool()
get_columns_tool = GetColumnsTool()