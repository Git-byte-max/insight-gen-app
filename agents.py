import os
import streamlit as st
import signal
import threading

# --- 1. SIGNAL PATCH ---
if threading.current_thread() is not threading.main_thread():
    _original_signal = signal.signal
    def _safe_signal_handler(sig, handler):
        try:
            return _original_signal(sig, handler)
        except ValueError:
            pass
    signal.signal = _safe_signal_handler

# --- 2. SETUP & DEBUGGING ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

# GLOBAL VARIABLES
planner = None
coder = None
reporter = None
debug_error = None
DEMO_MODE = True

try:
    from crewai import Agent, LLM
    from tools import execute_code_tool
    LIBS_INSTALLED = True
except ImportError as e:
    LIBS_INSTALLED = False
    debug_error = f"Library Error: {e}"
except Exception as e:
    LIBS_INSTALLED = False
    debug_error = f"Setup Error: {e}"

# --- 3. API KEYS ---
api_key = os.environ.get("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
google_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

# --- 4. AGENT DEFINITIONS ---
if not LIBS_INSTALLED:
    DEMO_MODE = True
elif not api_key and not google_key:
    DEMO_MODE = True
    debug_error = "API Key Missing"
else:
    DEMO_MODE = False
    try:
        if api_key:
            my_llm = LLM(model="gpt-4o-mini", api_key=api_key)
        else:
            my_llm = LLM(model="gemini/gemini-pro", api_key=google_key)

        # AGENT 1: PLANNER (Pattern Architect)
        planner = Agent(
            role='Lead Data Architect',
            goal='Plan a deep-dive analysis to find PATTERNS and RELATIONSHIPS.',
            backstory="""
            You are the Architect. You don't just want numbers; you want to know HOW variables interact.
            
            Your Plan MUST include:
            1. INSPECT: Check data types to see what is possible.
            2. RELATIONSHIPS: 
               - If data is numeric, instruct Coder to calculate **Correlation** (df.corr()).
               - Ask: "Is there a positive or negative link between these variables?"
            3. MAGNITUDE: Instruct Coder to calculate the **Percentage Difference** between groups.
            4. VISUALIZE: Plan a chart that best shows this relationship (Scatter for correlation, Bar for comparison).
            5. SAVE: Save chart as 'plot.png'.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

        # AGENT 2: CODER (Statistical Engineer)
        coder = Agent(
            role='Senior Data Engineer',
            goal='Execute code and PRINT DETAILED STATS.',
            backstory="""
            You are the Engineer. You must output numbers that prove the patterns.
            
            MANDATORY RULES:
            1. DATA: Use 'df'. Do not invent data.
            2. ANALYSIS PROTOCOL:
               - **Correlations:** Run `print(df[['col1', 'col2']].corr())` to see if they move together.
               - **Comparisons:** Calculate the actual difference. (e.g. "Value A is 150, Value B is 100. Diff is 50").
            3. PRINTING: 
               - Print the raw numbers clearly for the Reporter.
               - Explicitly print: "Correlation Coefficient: X".
            4. PLOTTING:
               - `import matplotlib.pyplot as plt; plt.switch_backend('Agg')`
               - `plt.savefig(os.path.join(os.getcwd(), 'plot.png'))`
            """,
            llm=my_llm,
            allow_delegation=False,
            tools=[execute_code_tool], 
            verbose=True
        )

        # AGENT 3: REPORTER (Data Storyteller)
        reporter = Agent(
            role='Data Storyteller',
            goal='Explain the "Story" of the data to a non-technical user.',
            backstory="""
            You are a Storyteller. The user is NOT technical. They want to understand the *meaning*.
            
            GUIDELINES:
            1. **Analyze Relationships:** - If the correlation is high (>0.7), say "There is a strong positive link."
               - If it is low, say "There is no significant pattern connecting these variables."
               - If negative, say "As one goes up, the other goes down."
            
            2. **Contextualize the Numbers:** - Do not just say "51 vs 48". 
               - Say "The difference is small (~6%), suggesting both groups behave similarly."
            
            3. **Final Verdict:** End with a clear "Takeaway" sentence summarizing the finding.
            """,
            llm=my_llm,
            allow_delegation=False,
            verbose=True
        )

    except Exception as e:
        DEMO_MODE = True
        debug_error = f"Agent Init Error: {e}"
