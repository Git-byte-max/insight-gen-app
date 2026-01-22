import os
# --- CRITICAL FIX: DISABLE TELEMETRY BEFORE IMPORTING CREWAI ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

from crewai import Agent
from langchain_openai import ChatOpenAI
from tools import execute_code
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- LLM CONFIGURATION ---
if not os.getenv("OPENAI_API_KEY"):
    llm = None
    DEMO_MODE = True
    debug_error = "Missing OPENAI_API_KEY in .env file."
else:
    # Temperature 0.1 reduces creativity to prevent "template" responses
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    DEMO_MODE = False
    debug_error = ""

# --- AGENTS ---

# 1. THE PLANNER (Instant Router)
planner = Agent(
    role="Analysis Architect",
    goal="Output a single sentence plan: 'Execute Python analysis on columns [X, Y] and generate report.'",
    backstory=(
        "You are an efficiency expert. Do not think. Do not explain."
        "Immediate Action: Identify the relevant columns for the user's query."
        "Output Protocol: Instruct the Coder to run a 'Smart Analysis Batch' on those columns."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# 2. THE CODER (Smart Logic + Context-Aware Output)
coder = Agent(
    role="Senior Python Analyst",
    goal="Run ONE script. Detect data types. Calculate Correlation/Group Averages. Print RAW RESULTS.",
    backstory=(
        "You are a Python expert. Speed and Logic are key."
        "CRITICAL INSTRUCTION: Write a SINGLE script that does the following:"
        
        "1. DETECT DATA TYPES: Check if columns are Numeric or Categorical."
        
        "2. SELECT ANALYSIS:"
        "   - IF NUMERIC vs NUMERIC (e.g., pH vs Alcohol):"
        "     Calculate Pearson Correlation." 
        "     Print: f'Correlation between {col1} and {col2}: {corr}'."  # Context-Aware Print
        "     Generate a Scatter Plot."
        "   - IF CATEGORICAL vs NUMERIC (e.g., Quality vs pH):"
        "     Calculate Mean per Group."
        "     Print: f'Group Means for {col1} by {col2}: {means}'."      # Context-Aware Print
        "     Generate a Box Plot."
        
        "3. EXECUTION RULES:"
        "   - Always save the chart as 'plot.png'."
        "   - PRINT all statistical findings to the console."
        "   - YOUR FINAL ANSWER MUST BE THE TEXT OUTPUT PRINTED BY THE SCRIPT."
        "   - Do NOT return the Python code itself as the answer. Return the CALCULATED DATA."
    ),
    tools=[execute_code],
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# 3. THE REPORTER (Strict Factualist)
reporter = Agent(
    role="Intelligence Briefer",
    goal="Convert the Coder's RAW OUTPUT into a clean Markdown report.",
    backstory=(
        "You are a strict data editor."
        "RULES:"
        "1. READ the Coder's output carefully. It contains the real numbers."
        "2. DO NOT use placeholders like '[insert value]'. Use the REAL numbers."
        "3. DO NOT use conditional logic like 'If numeric...'. You must see the actual result and report ONLY that."
        "4. If the Coder printed a Correlation, report it. If they printed a Mean, report it."
        "5. Structure: ## Executive Summary, ## Statistical Deep Dive, ## Strategic Implication."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)
