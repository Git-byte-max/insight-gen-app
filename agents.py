import os

# --- CRITICAL FIX: DISABLE TELEMETRY BEFORE IMPORTING CREWAI ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

from crewai import Agent, LLM
from dotenv import load_dotenv

# Import the custom execution tool
try:
    from tools import execute_code
    tool_list = [execute_code]
except ImportError as e:
    tool_list = []
    print(f"Warning: Tool import failed - {e}")

# Load environment variables
load_dotenv()

# --- LLM CONFIGURATION ---
if not os.getenv("OPENAI_API_KEY"):
    llm = None
    DEMO_MODE = True
    debug_error = "Missing OPENAI_API_KEY in .env file."
else:
    # Temperature 0.0 guarantees strict, factual outputs and prevents hallucinated variables
    llm = LLM(
        model="gpt-4o-mini", 
        temperature=0.0
    )
    DEMO_MODE = False
    debug_error = ""

# --- AGENT DEFINITIONS ---

planner = Agent(
    role="Data Analytics Planner",
    goal="Quickly identify the relevant columns and state a 1-sentence mathematical strategy.",
    backstory=(
        "You are a Lead Data Scientist. You review the user's query and the dataset columns. "
        "You output a single, direct sentence instructing the Coder on exactly what to calculate."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

coder = Agent(
    role="Senior Python Data Analyst",
    goal="Write pandas code, execute it using the tool, and print the exact numerical results.",
    backstory=(
        "You are an expert Python data analyst. "
        "CRITICAL RULES YOU MUST FOLLOW: "
        "1. The dataset is already loaded in memory as a pandas DataFrame named 'df'. "
        "2. If creating a plot, include `import matplotlib; matplotlib.use('Agg')` BEFORE importing pyplot, and save it strictly as 'plot.png' with a white background. "
        "3. You MUST explicitly `print()` the final numerical answers to the console so the Reporter can read them. Do not guess; run the code."
    ),
    llm=llm,
    tools=tool_list,
    allow_delegation=False,
    verbose=True
)

reporter = Agent(
    role="AI Reporting Analyst",
    goal="Translate the Coder's printed output into a clean, factual Markdown report.",
    backstory=(
        "You are an expert technical writer. You take the raw console output from the Coder "
        "and turn it into a structured summary. "
        "CRITICAL RULE: You NEVER hallucinate external data or use placeholder variables like {correlation}. "
        "You strictly report the exact numbers provided in the Coder's output."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)
