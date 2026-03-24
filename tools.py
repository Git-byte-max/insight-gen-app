import io
import traceback
from contextlib import redirect_stdout
from crewai.tools import tool

# This global variable gets overwritten dynamically by app.py 
# when the user uploads a CSV or Excel file.
df = None

@tool("Execute Python Code")
def execute_code(code: str) -> str:
    """
    Executes a Python script and returns the printed console output.
    You MUST use this to run pandas operations. The dataframe is already loaded as 'df'.
    """
    global df
    
    if df is None:
        return "Error: No dataset loaded. Please wait for the user to upload data."

    # Clean the code string in case the LLM wrapped it in markdown code blocks
    clean_code = code.replace("```python", "").replace("```", "").strip()
    
    # Setup the execution environment with the injected dataframe
    execution_env = {'df': df}
    output_buffer = io.StringIO()
    
    try:
        # Redirect standard output so we can capture the AI's print() statements
        with redirect_stdout(output_buffer):
            exec(clean_code, {}, execution_env)
        
        result = output_buffer.getvalue()
        
        if not result.strip():
            return "Script executed successfully, but nothing was printed. Please explicitly print() the final answer."
            
        return result
        
    except Exception as e:
        # Return the exact error traceback so the AI can self-correct its code
        error_msg = f"Execution Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return error_msg
