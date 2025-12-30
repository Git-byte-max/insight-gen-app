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

# --- 2. "OBSIDIAN GOLD" THEME CSS ---
st.markdown("""
    <style>
    /* 1. NEW FONTS: 'Audiowide' (Title) & 'Space Grotesk' (Body) */
    @import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Space+Grotesk:wght@300;500;700&display=swap');
    
    /* 2. GLOBAL STYLES & OBSIDIAN BACKGROUND */
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
        color: #E0E0E0;
        font-size: 17px;
    }
    
    .stApp {
        background: radial-gradient(circle at 50% 10%, #2b2b2b, #000000);
    }
    
    /* 3. CUSTOM SCROLLBAR (Gold) */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #FFD700; border-radius: 4px; }

    /* 4. TITLE STYLE (Audiowide Font + Gold Gradient) */
    .main-title {
        font-family: 'Audiowide', cursive;
        background: linear-gradient(to bottom, #FFD700 0%, #FDB931 50%, #9f7928 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4.2rem;
        letter-spacing: 4px;
        font-weight: 400; /* Audiowide is naturally bold */
        text-shadow: 0px 4px 10px rgba(255, 215, 0, 0.3);
    }
    
    h1, h2, h3 { 
        font-family: 'Space Grotesk', sans-serif !important; 
        color: #FDB931 !important; 
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* 5. METRIC CARDS (Black Glass & Gold Borders) */
    .metric-card {
        background: rgba(10, 10, 10, 0.8);
        border: 1px solid #333;
        border-bottom: 3px solid #FFD700; /* Gold Underline */
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.2);
        border-color: #FFD700;
    }
    .metric-value {
        font-family: 'Audiowide', cursive;
        font-size: 32px;
        color: #FFFFFF;
    }
    .metric-label {
        font-size: 13px;
        color: #888;
        letter-spacing: 1px;
    }

    /* 6. BUTTONS (Luxury Gold Gradient) */
    .stButton>button {
        background: linear-gradient(45deg, #FFD700, #FDB931);
        color: #000000;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 800;
        border: none;
        padding: 0.8rem 1.5rem;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.6);
    }

    /* 7. TABS & INPUTS */
    .stTabs [data-baseweb="tab-list"] { gap: 5px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #111;
        border: 1px solid #333;
        color: #666;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        border-radius: 4px;
    }
    .stTabs [aria-selected="true"] {
        background: #FDB931;
        color: #000;
        border: 1px solid #FFD700;
    }
    
    div[data-testid="stDataFrame"] {
        border: 1px solid #333;
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
    st.caption("THEME: OBSIDIAN & GOLD")

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

        # B. METRICS GRID (Gold Theme)
        st.write("")
        st.subheader("SYSTEM METRICS")
        
        mc1, mc2, mc3, mc4 = st.columns(4)
        
        with mc1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{df.shape[0]:,}</div>
                <div class="metric-label">Records</div>
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
            color = "#FF5252" if missing > 0 else "#FFFFFF"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {color}">{missing}</div>
                <div class="metric-label">Missing</div>
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
                        st.markdown("<center style='color: #FDB931;'>PROCESSING WORKFLOW...</center>", unsafe_allow_html=True)

                # 2. EXECUTION
                try:
                    if DEMO_MODE:
                        time.sleep(4) 
                        loader.empty()
                        
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
                                fig = px.histogram(df, x=numeric_df.columns[0], template="plotly_dark")
                                fig.update_traces(marker_color='#FDB931') # Gold
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

            # --- B. SMART DATA PREVIEW ---
            st.markdown("#### 2. DATA PREVIEW (LIVE)")
            
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
            st.caption(f"Showing top 100 rows.")
            
            st.markdown("---")

            # --- C. CHARTS (Gold & Orange) ---
            numeric_df = filtered_df.select_dtypes(include=['float64', 'int64'])
            
            if not numeric_df.empty:
                # Correlation
                st.markdown("#### 3. CORRELATION MAP")
                corr = numeric_df.corr()
                # 'Solar' or 'Thermal' fits the Gold theme
                fig_corr = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Solar', template="plotly_dark")
                fig_corr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig_corr, use_container_width=True)
                
                # Distributions
                st.markdown("#### 4. VARIABLE DISTRIBUTION")
                target_col = numeric_df.columns[0]
                
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.caption(f"Histogram: {target_col}")
                    fig1 = px.histogram(filtered_df, x=target_col, nbins=20, template="plotly_dark")
                    fig1.update_traces(marker_color='#FFD700') # Pure Gold
                    fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                    st.plotly_chart(fig1, use_container_width=True)

                with col_g2:
                    if len(numeric_df.columns) > 1:
                        target_col2 = numeric_df.columns[1]
                        st.caption(f"Scatter: {target_col} vs {target_col2}")
                        fig2 = px.scatter(filtered_df, x=target_col, y=target_col2, template="plotly_dark")
                        fig2.update_traces(marker_color='#FFA500') # Orange Gold
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
