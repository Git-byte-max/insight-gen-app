import os
import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components 
import time

# --- 1. SETUP & CONFIGURATION ---
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"

st.set_page_config(
    page_title="InsightGen Analyst",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import Backend (Safely)
try:
    from agents import planner, coder, reporter, DEMO_MODE
    import tools
except ImportError:
    DEMO_MODE = True
    tools = None

# --- 2. MATRIX / TERMINAL THEME CSS ---
st.markdown("""
    <style>
    /* 1. NEW FONTS: 'VT323' (Header) & 'Share Tech Mono' (Body) */
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=VT323&display=swap');
    
    /* 2. GLOBAL STYLES (Terminal Look) */
    html, body, [class*="css"] {
        font-family: 'Share Tech Mono', monospace;
        color: #00FF41; /* Classic Terminal Green */
        background-color: #0D0208;
        font-size: 16px;
    }
    
    .stApp {
        background-color: #000000;
        background-image: linear-gradient(rgba(0, 255, 65, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 255, 65, 0.03) 1px, transparent 1px);
        background-size: 20px 20px; /* Grid Pattern */
    }

    /* 3. CUSTOM SCROLLBAR (Green) */
    ::-webkit-scrollbar { width: 10px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #003B00; border: 1px solid #00FF41; }
    ::-webkit-scrollbar-thumb:hover { background: #00FF41; }

    /* 4. TITLE STYLE (Pixelated Glitch) */
    .main-title {
        font-family: 'VT323', monospace;
        color: #00FF41;
        font-size: 5rem;
        line-height: 1;
        text-shadow: 2px 2px 0px #003B00;
        letter-spacing: -2px;
        text-transform: uppercase;
    }
    
    h1, h2, h3 { 
        font-family: 'VT323', monospace !important; 
        color: #00FF41 !important; 
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* 5. METRIC CARDS (Wireframe Style) */
    .metric-card {
        background-color: #000;
        border: 1px solid #00FF41;
        padding: 15px;
        text-align: center;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.2);
        position: relative;
    }
    .metric-card::before {
        content: ">>";
        position: absolute;
        top: 5px;
        left: 5px;
        font-size: 10px;
        color: #003B00;
    }
    .metric-value {
        font-family: 'VT323', monospace;
        font-size: 42px;
        color: #00FF41;
        text-shadow: 0 0 5px #00FF41;
    }
    .metric-label {
        font-size: 14px;
        color: #008F11;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* 6. BUTTONS (Hollow Terminal Style) */
    .stButton>button {
        background-color: #000000;
        color: #00FF41;
        font-family: 'Share Tech Mono', monospace;
        font-size: 18px;
        border: 2px solid #00FF41;
        border-radius: 0px; /* Sharp Edges */
        padding: 0.5rem 1.5rem;
        text-transform: uppercase;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #00FF41;
        color: #000000;
        box-shadow: 0 0 15px #00FF41;
    }

    /* 7. UI ELEMENTS */
    .stTabs [data-baseweb="tab-list"] { gap: 0px; border-bottom: 2px solid #003B00; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        background-color: #000;
        border: 1px solid #003B00;
        color: #003B00;
        font-family: 'Share Tech Mono', monospace;
        border-radius: 0px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #001100;
        color: #00FF41;
        border: 1px solid #00FF41;
        border-bottom: none;
    }
    
    div[data-testid="stDataFrame"] {
        border: 1px solid #00FF41;
        font-family: 'Share Tech Mono', monospace;
    }
    
    /* Input Fields */
    input[type="text"] {
        background-color: #000 !important;
        color: #00FF41 !important;
        border: 1px solid #00FF41 !important;
        font-family: 'Share Tech Mono', monospace !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("### > SYSTEM_CONFIG")
    uploaded_file = st.file_uploader("UPLOAD DATA SOURCE", type=["csv", "xlsx"])
    
    st.markdown("---")
    if DEMO_MODE:
        st.code("STATUS: OFFLINE (SIMULATION)")
    else:
        st.code("STATUS: ONLINE (CONNECTED)")
        
    st.markdown("---")
    st.caption("TERMINAL_V4.0 | MATRIX BUILD")

# --- 4. MAIN CONTENT ---
st.markdown("<div class='main-title'>INSIGHT_GEN</div>", unsafe_allow_html=True)
st.markdown("#### *// EXECUTING AUTONOMOUS DATA PROTOCOLS...*")

if uploaded_file:
    # A. LOAD DATA
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        if tools: tools.df = df
        df.to_csv("dataset.csv", index=False)

        # B. METRICS GRID (Matrix Style)
        st.write("")
        st.subheader("> SYSTEM_METRICS")
        
        mc1, mc2, mc3, mc4 = st.columns(4)
        
        with mc1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{df.shape[0]}</div>
                <div class="metric-label">ROWS_LOADED</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mc2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{df.shape[1]}</div>
                <div class="metric-label">VARIABLES</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mc3:
            missing = df.isnull().sum().sum()
            color = "#FF0000" if missing > 0 else "#00FF41" # Red warning if missing
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {color}">{missing}</div>
                <div class="metric-label">ERRORS_NULL</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mc4:
            dupes = df.duplicated().sum()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{dupes}</div>
                <div class="metric-label">DUPLICATES</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # C. TABS INTERFACE
        tab1, tab2 = st.tabs(["[ 1. AGENT_TERMINAL ]", "[ 2. AUTO_DASHBOARD ]"])

        # --- TAB 1: AGENT WORKFLOW ---
        with tab1:
            st.write("")
            col_q, col_b = st.columns([3, 1])
            with col_q:
                query = st.text_input("ENTER QUERY COMMAND:", placeholder="> Analyze sales trends...", label_visibility="collapsed")
            with col_b:
                run_btn = st.button("RUN_SCRIPT.EXE", use_container_width=True)

            if run_btn and query:
                # 1. ANIMATION (Using IFrame)
                loader = st.empty()
                with loader.container():
                    lc1, lc2, lc3 = st.columns([1,2,1])
                    with lc2:
                        components.iframe(
                            "https://lottie.host/embed/705a9879-1c4b-45a1-b1ee-d7690f56f458/HMMnGjpbaU.lottie",
                            height=200, scrolling=False
                        )
                        st.markdown("<center style='color: #00FF41; font-family: Share Tech Mono;'>[ PROCESSING_DATA_STREAMS... ]</center>", unsafe_allow_html=True)

                # 2. EXECUTION
                try:
                    if DEMO_MODE:
                        time.sleep(4) 
                        loader.empty()
                        st.toast("PROCESS COMPLETE", icon="🟩")
                        
                        res_col1, res_col2 = st.columns([1.5, 1])
                        with res_col1:
                            st.markdown("#### > EXEC_SUMMARY")
                            st.info("Demo Mode: System simulated a successful response.")
                        with res_col2:
                            st.markdown("#### > VISUAL_OUTPUT")
                            numeric_df = df.select_dtypes(include=['number'])
                            if not numeric_df.empty:
                                fig = px.histogram(df, x=numeric_df.columns[0], template="plotly_dark")
                                fig.update_traces(marker_color='#00FF41', marker_line_color='#003B00', marker_line_width=1.5) 
                                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#00FF41")
                                st.plotly_chart(fig, use_container_width=True)

                    else:
                        # 🟢 CRITICAL UPDATE: FIXED 3-AGENT LOGIC
                        from crewai import Crew, Task, Process
                        from agents import planner, coder, reporter # Import all 3
                        
                        # TASK 1: PLAN
                        task_plan = Task(
                            description=f"Create a step-by-step Python analysis plan for: '{query}'. Focus on which columns to use.",
                            expected_output="A numbered list of Python steps.",
                            agent=planner
                        )

                        # TASK 2: CODE (Takes Task 1 Output)
                        task_code = Task(
                            description="Execute the plan using the `execute_code_tool`. Use 'df'. Save 'plot.png' if needed. Return the numeric results.",
                            expected_output="Raw execution logs and calculated numbers.",
                            agent=coder,
                            context=[task_plan] # Coder listens to Planner
                        )

                        # TASK 3: REPORT (Takes Task 2 Output)
                        task_report = Task(
                            description="Summarize the raw numbers provided by the Coder into a business insight.",
                            expected_output="A concise executive summary.",
                            agent=reporter,
                            context=[task_code] # Reporter listens to Coder
                        )

                        # SEQUENTIAL PROCESS (Forces 1->2->3 Order)
                        crew = Crew(
                            agents=[planner, coder, reporter],
                            tasks=[task_plan, task_code, task_report],
                            process=Process.sequential, 
                            verbose=True
                        )
                        
                        result = crew.kickoff()
                        
                        loader.empty()
                        st.toast("TASK COMPLETE", icon="🟩")
                        
                        r1, r2 = st.columns([1.5, 1])
                        with r1:
                            st.markdown("#### > EXEC_SUMMARY")
                            st.markdown(result)
                        with r2:
                            st.markdown("#### > VISUAL_OUTPUT")
                            if os.path.exists("plot.png"):
                                st.image("plot.png")
                            else:
                                st.caption("NO_IMAGE_GENERATED")

                except Exception as e:
                    loader.empty()
                    st.error(f"RUNTIME ERROR: {e}")

        # --- TAB 2: AUTOMATED DASHBOARD ---
        with tab2:
            st.write("")
            
            # --- A. FILTERS ---
            st.markdown("#### > DATA_FILTERS")
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(cat_cols) > 0:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    selected_cat = st.selectbox("SELECT PARAMETER", cat_cols)
                with col_f2:
                    unique_vals = df[selected_cat].unique()
                    selected_val = st.multiselect(f"SELECT VALUES", unique_vals, default=unique_vals[:5])
                
                filtered_df = df[df[selected_cat].isin(selected_val)] if selected_val else df
            else:
                filtered_df = df
            
            st.markdown("---")

            # --- B. SMART DATA PREVIEW ---
            st.markdown("#### > LIVE_DATA_FEED")
            
            column_config = {}
            for col in filtered_df.select_dtypes(include="number").columns:
                column_config[col] = st.column_config.ProgressColumn(
                    col,
                    format="%.2f",
                    min_value=float(filtered_df[col].min()),
                    max_value=float(filtered_df[col].max()),
                )

            st.dataframe(
                filtered_df.head(100), 
                use_container_width=True, 
                height=300,
                column_config=column_config
            )
            st.caption(f"DISPLAYING TOP 100 RECORDS.")
            
            st.markdown("---")

            # --- C. MATRIX CHARTS (Hybrid: Automated + Dropdown) ---
            numeric_df = filtered_df.select_dtypes(include=['float64', 'int64'])
            
            if not numeric_df.empty:
                # 1. Correlation Matrix (Always Automated)
                st.markdown("#### > CORRELATION_MATRIX")
                corr = numeric_df.corr()
                fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Greens', template="plotly_dark")
                fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#00FF41")
                st.plotly_chart(fig_corr, use_container_width=True)
                
                st.markdown("---")
                
                # 2. Customizable Charts Section
                st.markdown("#### > VARIABLE_DISTRIBUTION & RELATIONSHIPS")
                
                # --- DROPDOWNS FOR USER CONTROL ---
                c_sel1, c_sel2 = st.columns(2)
                
                with c_sel1:
                    # Default index=0 (First column) -> Automated start
                    x_axis_val = st.selectbox("SELECT X-AXIS (DISTRIBUTION)", numeric_df.columns, index=0)
                
                with c_sel2:
                    # Default index=1 (Second column) if available, else 0 -> Automated start
                    default_ix = 1 if len(numeric_df.columns) > 1 else 0
                    y_axis_val = st.selectbox("SELECT Y-AXIS (SCATTER)", numeric_df.columns, index=default_ix)

                # --- PLOT THE CHARTS ---
                col_g1, col_g2 = st.columns(2)
                
                # Chart 1: Histogram
                with col_g1:
                    st.caption(f"HISTOGRAM: {x_axis_val}")
                    fig1 = px.histogram(filtered_df, x=x_axis_val, nbins=20, template="plotly_dark")
                    fig1.update_traces(marker_color='#00FF41', marker_line_color='#003B00', marker_line_width=1)
                    fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#00FF41")
                    st.plotly_chart(fig1, use_container_width=True)

                # Chart 2: Scatter
                with col_g2:
                    st.caption(f"SCATTER: {x_axis_val} vs {y_axis_val}")
                    fig2 = px.scatter(filtered_df, x=x_axis_val, y=y_axis_val, template="plotly_dark")
                    fig2.update_traces(marker_color='#008F11')
                    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#00FF41")
                    st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("NO_NUMERIC_DATA_FOUND")

    except Exception as e:
        st.error(f"FATAL_ERROR: {e}")

else:
    with st.container():
        st.warning("SYSTEM STANDBY: AWAITING DATA UPLOAD...")
