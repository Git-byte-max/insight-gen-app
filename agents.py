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
    # Temperature 0.1 keeps it factual but allows for code flexibility
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    DEMO_MODE = False
    debug_error = ""

# --- AGENTS ---

# 1. THE PLANNER (Context Manager)
planner = Agent(
    role="Analysis Architect",
    goal="Identify the user's intent and relevant columns.",
    backstory=(
        "You are an expert data strategist."
        "Your Job: Look at the user's query and the available columns."
        "Output: A single sentence instruction for the Coder. "
        "Example: 'Calculate the maximum value of the Age column.' or 'Analyze the relationship between Age and Salary.'"
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# 2. THE CODER (General Purpose Analyst)
coder = Agent(
    role="Senior Python Analyst",
    goal="Write pandas code to answer the specific question. Print the result.",
    backstory=(
        "You are a Python expert. You can answer ANY data question."
        "CRITICAL INSTRUCTION: Write a SINGLE script that does the following:"
        
        "1. UNDERSTAND THE GOAL: "
        "   - If the user asks for a specific value (e.g., 'What is the max age?'), calculate and PRINT it."
        "   - If the user asks for a count (e.g., 'How many rows?'), calculate and PRINT it."
        "   - If the user asks for a relationship (e.g., 'Age vs Salary'), calculate Correlation and plot it."
        
        "2. VISUALIZATION RULES:"
        "   - If the query implies a trend, distribution, or comparison, generate a plot and save as 'plot.png'."
        "   - If the query is just a single number (e.g., 'Mean Age'), a plot is NOT required."
        
        "3. EXECUTION RULES:"
        "   - PRINT the final answer clearly (e.g., print(f'The maximum age is {max_age}'))."
        "   - YOUR FINAL ANSWER MUST BE THE TEXT OUTPUT PRINTED BY THE SCRIPT."
        "   - Do NOT return the Python code itself. Return the DATA."
    ),
    tools=[execute_code],
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# 3. THE REPORTER (Factual Narrator)
# 3. THE REPORTER (Factual Narrator)
reporter = Agent(
    role="Intelligence Briefer",
    goal="Convert the Coder's printed output into a natural language response.",
    backstory=(
        "You are a strict data editor."
        "RULES:"
        "1. READ the Coder's output. It contains the real answer."
        "2. If the Coder provided a specific number (e.g., 'Max Age: 80'), report that directly."
        "3. FORMATTING RULE: Always use double newlines (\\n\\n) before and after every Header (##)."
        "4. Do NOT hallucinate values. Only use what was printed."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

