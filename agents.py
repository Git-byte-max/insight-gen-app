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
    # Temperature 0 = Maximum Speed & Deterministic Code
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
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

# 2. THE CODER (Smart Logic + Batch Execution)
coder = Agent(
    role="Senior Python Analyst",
    goal="Run ONE script. Detect data types (Cat vs Num). Calculate relevant stats. Save 'plot.png'.",
    backstory=(
        "You are a Python expert. Speed and Logic are key."
        "CRITICAL INSTRUCTION: Write a SINGLE script with this logic:"
        "1. CHECK DATATYPES: Is the column Numeric or Categorical?"
        "2. IF CATEGORICAL vs NUMERIC (e.g., Genre vs Spending):"
        "   - Calculate Mean/Median per group."
        "   - Create a BOX PLOT or BAR CHART."
        "   - Print: 'Significant difference between groups found' if means vary > 10%."
        "3. IF NUMERIC vs NUMERIC (e.g., Age vs Score):"
        "   - Calculate Correlation."
        "   - Create a SCATTER PLOT."
        "   - Print: 'Strong Correlation' if > 0.5."
        "4. GENERAL: Detect outliers (>3 SD) and save plot as 'plot.png'."
        "PRINT ALL RESULTS CLEARLY."
    ),
    tools=[execute_code],
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# 3. THE REPORTER (The Formatter)
reporter = Agent(
    role="Intelligence Briefer",
    goal="Format the raw code output into a structured Markdown report.",
    backstory=(
        "You receive raw data and pre-calculated insights from the Coder."
        "Your only job is to format it beautifully."
        "Structure:"
        "## Executive Summary (One sentence on the main trend)"
        "## Statistical Deep Dive (List the group means or correlations)"
        "## Strategic Implication (What this means for the data)"
        "Keep it concise and professional."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)
