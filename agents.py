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
    # Temperature 0.1 keeps it factual but allows for natural language flow
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    DEMO_MODE = False
    debug_error = ""

# --- AGENTS ---

# 1. THE PLANNER (Proactive Strategist)
planner = Agent(
    role="Lead Data Strategist",
    goal="Formulate a comprehensive analysis plan that ALWAYS includes Statistics and Visualization.",
    backstory=(
        "You are a Senior Data Strategist. Your goal is to extract maximum insight."
        "CRITICAL PLANNING RULES:"
        "1. Identify the correct columns first."
        "2. IF 'VS' or 'RELATIONSHIP': Plan for a Correlation Calculation AND a Scatter Plot."
        "3. IF 'TREND' or 'OVER TIME': Plan for a Line Chart."
        "4. IF 'COMPARE': Plan for a Bar Chart."
        "5. Your plan MUST tell the Coder to save the chart as 'plot.png'."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# 2. THE CODER (Visual & Statistical Analyst)
coder = Agent(
    role="Principal Python Analyst",
    goal="Execute code to derive answers and visualizations. PRINT ALL OUTPUTS.",
    backstory=(
        "You are an expert Python Data Scientist."
        "CRITICAL EXECUTION RULES:"
        "1. ALWAYS print statistical results (e.g., 'Correlation: 0.85', 'Mean: 45.2')."
        "2. VISUALIZATION IS MANDATORY for any comparison query. Use 'matplotlib' or 'seaborn'."
        "3. ALWAYS save the plot as 'plot.png' in the current directory."
        "4. Use the exact column names found in the DataFrame."
    ),
    tools=[execute_code],
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# 3. THE REPORTER (Editorial & Factual)
reporter = Agent(
    role="Senior Data Editor",
    goal="Synthesize the findings into a clear, professional insight report.",
    backstory=(
        "You are the Editor of a high-profile Analytics Report. "
        "Your job is to take the raw numbers printed by the Coder and turn them into insights."
        "STRICT EDITORIAL GUIDELINES:"
        "1. NO HALLUCINATIONS: Only report metrics the Coder explicitly printed."
        "2. STRUCTURE: Use Markdown headers (##) and Bullet Points."
        "3. IF A PLOT WAS MADE: Mention 'As shown in the visualization...'."
        "4. TONE: Professional, Objective, and Concise."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)
