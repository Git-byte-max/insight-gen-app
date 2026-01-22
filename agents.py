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

# 2. THE CODER (Result-Oriented Executor)
coder = Agent(
    role="Senior Python Analyst",
    goal="Run ONE script and return the RAW TEXT OUTPUT (Means, Correlations, etc.).",
    backstory=(
        "You are a Python expert."
        "CRITICAL EXECUTION PROTOCOL:"
        "1. Write a SINGLE script using 'execute_code'."
        "2. The script MUST print the final numbers (e.g., print(f'Correlation: {corr}'))."
        "3. YOUR FINAL ANSWER MUST BE THE TEXT OUTPUT PRINTED BY THE SCRIPT."
        "4. Do NOT output the Python code itself as the final answer. Output the RESULTS."
        "5. Always save the chart as 'plot.png'."
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
