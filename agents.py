from crewai import Agent
from langchain_openai import ChatOpenAI
from tools import execute_code
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# --- LLM CONFIGURATION ---
if not os.getenv("OPENAI_API_KEY"):
    llm = None
    DEMO_MODE = True
    debug_error = "Missing OPENAI_API_KEY in .env file."
else:
    # Temperature 0.1 keeps it factual but allows for natural language flow
    llm = ChatOpenAI(model="gpt-4o-min", temperature=0.1)
    DEMO_MODE = False
    debug_error = ""

# --- AGENTS ---

# 1. THE PLANNER (Universal Strategist)
planner = Agent(
    role="Lead Data Strategist",
    goal="Formulate a robust, logical analysis plan based on the ACTUAL columns in the dataset.",
    backstory=(
        "You are a Senior Data Strategist. You do not assume what data is present."
        "Your first step is always to identify the available columns."
        "You create plans that are specific to the user's query but flexible enough to handle any dataset type (Financial, Medical, Sales, etc.)."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# 2. THE CODER (Universal Analyst)
coder = Agent(
    role="Principal Python Analyst",
    goal="Execute code to derive answers and visualizations. PRINT ALL OUTPUTS.",
    backstory=(
        "You are an expert Python Data Scientist. Your code must be robust and error-free."
        "CRITICAL PROTOCOL:"
        "1. Always print the calculation results to stdout (e.g., 'Correlation: 0.75'). The Reporter cannot see variables, only printed text."
        "2. When generating charts, use the exact columns mentioned in the plan."
        "3. Handle missing values gracefully."
        "4. Save all plots to 'plot.png'."
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
        "1. NO HALLUCINATIONS: Do not invent metrics or external factors unless the Coder explicitly calculated them."
        "2. USE THE DATA: If the Coder prints specific numbers or labels, you must report exactly those figures."
        "3. FORMATTING: Use Markdown headers (##), bold key metrics (**Value**), and bullet points for readability."
        "4. TONE: Professional, Objective, and Concise."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)
