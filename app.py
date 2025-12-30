import os
import streamlit as st
import pandas as pd
import plotly.express as px  # Interactive Charts
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

# --- 2. CUSTOM CSS (Professional UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #E0E0E0;
        background-color: #0F1116;
    }
    .stApp { background-color: #0F1116; }
    
    /* Animations */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .block-container { animation: fadeInUp 0.8s ease-out both; }

    /* Headers */
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 700; }
    .main-title {
        background: linear-gradient(90deg, #E0E0E0 60%, #4DB6AC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #161920;
        border-radius: 6px 6px 0px 0px;
        color: #9CA3AF;
        border: 1px solid #2D313A;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 12px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E2129;
        color: #4DB6AC;
        border-top: 2px solid #4DB6AC;
    }

    /* Glassmorphism Metric Card CSS */
    .metric-card {
        background: rgba(30, 33, 41, 0.7);
        border: 1px solid #2D313A;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        border-color: #4DB6AC;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #4DB6AC;
        margin-bottom: 5px;
    }
    .metric-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #9CA3AF;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #4DB6AC 0%, #26A69A 100%);
        color: #0F1116;
        font-weight: 700;
        border: none;
        padding: 0.6rem 1.2rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        box-shadow: 0 4px 12px rgba(77, 182, 172, 0.3);
        color: #FFFFFF;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("### SYSTEM CONFIGURATION")
    uploaded_file = st.file_uploader("Upload Data Source", type=["csv", "xlsx"])
    
    st.markdown("---")
    if DEMO_MODE:
        st.info("MODE: SIMULATION (OFFLINE)")
    else:
        st.success("MODE: AI AGENTS (ONLINE)")
        
    st.markdown("---")
    st.caption("VERSION 2.3 | VISUAL UPGRADE")

# --- 4. MAIN CONTENT ---
st.markdown("<div class='main-title'>INSIGHTGEN</div>", unsafe_allow_html=True)
st.markdown("#### *Autonomous Data Intelligence Platform*")

if uploaded_file:
    # A. LOAD DATA
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        if tools: tools.df = df
        df.to_csv("dataset.csv", index=False)

        # B. METRICS GRID (✨ UPGRADED: GLASSMORPHISM CARDS)
        st.write("")
        st.subheader("DATASET METRICS")
        
        mc1, mc2, mc3, mc4 = st.columns(4)
        
        with mc1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{df.shape[0]:,}</div>
                <div class="metric-label">Total Records</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mc2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{df.shape[1]}</div>
                <div class="metric-label">Features</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mc3:
            missing = df.isnull().sum().sum()
            color = "#EF5350" if missing > 0 else "#4DB6AC"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {color}">{missing}</div>
                <div class="metric-label">Missing Values</div>
            </div>
            """, unsafe_allow_html=True)
            
        with mc4:
            dupes = df.duplicated().sum()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{dupes}</div>
                <div class="metric-label">Duplicates</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # C. TABS INTERFACE
        tab1, tab2 = st.tabs(["AI ANALYST AGENT", "AUTOMATED DASHBOARD"])

        # --- TAB 1: AGENT WORKFLOW ---
        with tab1:
            st.write("")
            col_q, col_b = st.columns([3, 1])
            with col_q:
                query = st.text_input("ANALYTICAL QUERY", placeholder="e.g., Analyze sales trends over time", label_visibility="collapsed")
            with col_b:
                run_btn = st.button("EXECUTE ANALYSIS", use_container_width=True)

            if run_btn and query:
                # 1. ANIMATION
                loader = st.empty()
                with loader.container():
                    lc1, lc2, lc3 = st.columns([1,2,1])
                    with lc2:
                        components.iframe(
                            "https://lottie.host/embed/705a9879-1c4b-45a1-b1ee-d7690f56f458/HMMnGjpbaU.lottie",
                            height=200, scrolling=False
                        )
                        st.markdown("<center>PROCESSING WORKFLOW...</center>", unsafe_allow_html=True)

                # 2. EXECUTION
                try:
                    if DEMO_MODE:
                        time.sleep(4) 
                        loader.empty()
                        
                        # ✨ UPGRADED: TOAST NOTIFICATIONS
                        st.toast("Analysis Complete!", icon="✅")
                        time.sleep(0.5)
                        st.toast("Charts generated successfully.", icon="📊")
                        
                        res_col1, res_col2 = st.columns([1.5, 1])
                        with res_col1:
                            st.markdown("#### EXECUTIVE SUMMARY")
                            st.info(f"""
                            **Query:** {query}
                            **Key Insights:**
                            1. **Trend Detected:** Significant upward trajectory observed.
                            2. **Correlation:** Strong positive correlation (0.85).
                            *Simulated Result.*
                            """)
                        with res_col2:
                            st.markdown("#### VISUAL OUTPUT")
                            numeric_df = df.select_dtypes(include=['number'])
                            if not numeric_df.empty:
                                fig = px.histogram(df, x=numeric_df.columns[0], color_discrete_sequence=['#4DB6AC'])
                                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                                st.plotly_chart(fig, use_container_width=True)

                    else:
                        from crewai import Crew, Task
                        task1 = Task(description=f"Plan analysis for: {query}", agent=planner, expected_output="Plan")
                        task2 = Task(description="Execute Python code on 'df'. Save 'plot.png'.", agent=coder, expected_output="Code")
                        task3 = Task(description="Summarize findings.", agent=reporter, expected_output="Summary")

                        crew = Crew(agents=[planner, coder, reporter], tasks=[task1, task2, task3], verbose=True)
                        result = crew.kickoff()
                        loader.empty()
                        
                        st.toast("AI Analysis Complete!", icon="🤖")
                        
                        r1, r2 = st.columns([1.5, 1])
                        with r1:
                            st.markdown("#### EXECUTIVE SUMMARY")
                            st.markdown(result)
                        with r2:
                            st.markdown("#### VISUAL OUTPUT")
                            if os.path.exists("plot.png"):
                                st.image("plot.png")
                            else:
                                st.caption("No image generated.")
                except Exception as e:
                    loader.empty()
                    st.error(f"SYSTEM ERROR: {e}")

        # --- TAB 2: AUTOMATED DASHBOARD ---
        with tab2:
            st.write("")
            
            # --- A. FILTERS ---
            st.markdown("#### 1. DATA FILTERS")
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(cat_cols) > 0:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    selected_cat = st.selectbox("Select Category", cat_cols)
                with col_f2:
                    unique_vals = df[selected_cat].unique()
                    selected_val = st.multiselect(f"Select Values", unique_vals, default=unique_vals[:5])
                
                filtered_df = df[df[selected_cat].isin(selected_val)] if selected_val else df
            else:
                filtered_df = df
            
            st.markdown("---")

            # --- B. DATA TABLE (✨ UPGRADED: SMART PREVIEW) ---
            st.markdown("#### 2. SMART DATA PREVIEW")
            
            # Create column config with progress bars
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
                column_config=column_config # Adds the visual bars
            )
            st.caption(f"Showing top 100 rows. Numerical columns include visual density bars.")
            
            st.markdown("---")

            # --- C. CHARTS ---
            numeric_df = filtered_df.select_dtypes(include=['float64', 'int64'])
            
            if not numeric_df.empty:
                # Correlation
                st.markdown("#### 3. CORRELATION MAP")
                corr = numeric_df.corr()
                fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Teal')
                fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig_corr, use_container_width=True)
                
                # Distributions
                st.markdown("#### 4. VARIABLE DISTRIBUTION")
                target_col = numeric_df.columns[0]
                
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.caption(f"Histogram: {target_col}")
                    fig1 = px.histogram(filtered_df, x=target_col, nbins=20, color_discrete_sequence=['#26A69A'])
                    fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                    st.plotly_chart(fig1, use_container_width=True)

                with col_g2:
                    if len(numeric_df.columns) > 1:
                        target_col2 = numeric_df.columns[1]
                        st.caption(f"Scatter: {target_col} vs {target_col2}")
                        fig2 = px.scatter(filtered_df, x=target_col, y=target_col2, color_discrete_sequence=['#4DB6AC'])
                        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Need more data for Scatter Plot.")
            else:
                st.info("NO NUMERIC DATA AVAILABLE FOR DASHBOARD")

    except Exception as e:
        st.error(f"FILE LOAD ERROR: {e}")

else:
    with st.container():
        st.warning("SYSTEM STANDBY: PLEASE UPLOAD DATA SOURCE.")
