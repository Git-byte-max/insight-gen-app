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
        "3. You MUST always clean the data first by dropping duplicate rows, NaN, and Inf values before any computations. "
        "4. You MUST explicitly `print()` the final numerical answers to the console so the Reporter can read them. Do not guess; run the code."
    ),
    llm=llm,
    tools=tool_list,
    allow_delegation=False,
    verbose=True
)

reporter = Agent(
    role='Senior Business Intelligence Analyst',
    goal='Translate raw statistical outputs into a single, concise plain-text business insight sentence. Never use filler text or formatting symbols.',
    backstory=(
        'You are an elite data communicator. Your reports go directly to the CEO, '
        'who has zero tolerance for fluff, generic statements, or formatting symbols. '
        'RULES YOU MUST STRICTLY FOLLOW: '
        '1. Round all long decimal numbers to a maximum of two decimal places (e.g., 0.2056 becomes 0.21). '
        '2. ABSOLUTELY NO MARKDOWN. Do not use "#" for headers, "**" for bolding, or any bullet points. '
        '3. State the variables, the relationship, and the magnitude directly in a single plain-text sentence. '
        '4. Never fabricate or hallucinate values.'
    ),
    llm=llm,
    verbose=True
)
