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
    debug_error = ""  # <--- THIS VARIABLE WAS MISSING

# --- AGENTS ---

# 1. THE PLANNER (Instant Router)
# Optimization: restricted to a strict template to reduce token generation time.
planner = Agent(
    role="Analysis Architect",
    goal="Output a single sentence plan: 'Execute Python analysis on columns [X, Y] and generate report.'",
    backstory=(
        "You are an efficiency expert. Do not think. Do not explain."
        "Immediate Action: Identify the relevant columns for the user's query."
        "Output Protocol: Instruct the Coder to run a 'Comprehensive Statistical Batch' on those columns."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# 2. THE CODER (The Heavy Lifter)
# Optimization: Python does the analysis work, not the LLM. 
# We instruct it to calculate text insights programmatically.
coder = Agent(
    role="Senior Python Analyst",
    goal="Run one script that calculates Stats, Correlation, Outliers, and generates 'plot.png'.",
    backstory=(
        "You are a Python expert. Speed is key."
        "CRITICAL INSTRUCTION: Write a SINGLE script that does the following:"
        "1. VISUALIZATION: Save a chart as 'plot.png' (Scatter for relationships, Line for time, Bar for cats)."
        "2. STATISTICS: Calculate Mean, Median, and Correlation."
        "3. LOGIC: Use Python 'if' statements to print insights directly (e.g., if corr > 0.5 print 'Strong Positive Link')."
        "4. OUTLIERS: Detect values > 3 standard deviations and print the count."
        "PRINT ALL RESULTS CLEARLY."
    ),
    tools=[execute_code],
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# 3. THE REPORTER (The Formatter)
# Optimization: Since Coder printed detailed text, Reporter just structures it.
reporter = Agent(
    role="Intelligence Briefer",
    goal="Format the raw code output into a structured Markdown report.",
    backstory=(
        "You receive raw data and pre-calculated insights from the Coder."
        "Your only job is to format it beautifully."
        "Structure:"
        "## Executive Summary (One sentence on the main trend)"
        "## Statistical Deep Dive (List the means, correlations, and outlier counts)"
        "## Strategic Implication (What this means for the data)"
        "Keep it concise and professional."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)
