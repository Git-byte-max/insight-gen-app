import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import time
import numpy as np

# --- 1. SETUP & CONFIGURATION ---
st.set_page_config(
    page_title="InsightGen Analyst",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. PROFESSIONAL STYLING (CSS) ---
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

    /* Metrics & Containers */
    div[data-testid="stMetricValue"] { color: #4DB6AC; font-size: 28px; font-weight: 700; }
    div[data-testid="stMetricLabel"] { color: #9CA3AF; font-size: 11px; letter-spacing: 1px; }
    
    div[data-testid="stExpander"], div[data-testid="stContainer"] {
        background-color: #1E2129;
        border: 1px solid #2D313A;
        border-radius: 8px;
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

# --- 3. HELPER FUNCTIONS FOR AUTOMATED ANALYSIS ---
def generate_automated_summary(df):
    """
    Generates a text summary based on real statistical properties of the dataframe.
    """
    numeric_df = df.select_dtypes(include=['number'])
    if numeric_df.empty:
        return "Dataset contains no numerical columns for statistical analysis."
    
    # Correlation Check
    corr_matrix = numeric_df.corr().abs()
    np.fill_diagonal(corr_matrix.values, 0)
    
    if not corr_matrix.empty:
        max_corr = corr_matrix.max().max()
        idx = corr_matrix.stack().idxmax()
        col1, col2 = idx
        corr_text = f"Strongest correlation detected between **{col1}** and **{col2}** ({max_corr:.2f})."
    else:
        corr_text = "No significant correlations detected."
        
    # Outlier Check (using first numeric column)
    target_col = numeric_df.columns[0]
    q1 = df[target_col].quantile(0.25)
    q3 = df[target_col].quantile(0.75)
    iqr = q3 - q1
    outliers = ((df[target_col] < (q1 - 1.5 * iqr)) | (df[target_col] > (q3 + 1.5 * iqr))).sum()
    
    summary = f"""
    **Automated Findings:**
    1. **Primary Trend:** The dataset features {len(numeric_df.columns)} numerical variables.
    2. **Correlation:** {corr_text}
    3. **Data Quality:** Variable **{target_col}** contains {outliers} potential outliers based on IQR analysis.
    """
    return summary

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### SYSTEM CONFIGURATION")
    uploaded_file = st.file_uploader("Upload Data Source", type=["csv", "xlsx"])
    
    st.markdown("---")
    st.info("SYSTEM STATUS: ONLINE")
    st.caption("VERSION 2.1 | ENTERPRISE BUILD")

# --- 5. MAIN CONTENT ---
st.markdown("<div class='main-title'>INSIGHTGEN</div>", unsafe_allow_html=True)
st.markdown("#### *Autonomous Data Intelligence Platform*")

if uploaded_file:
    # A. LOAD DATA
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # B. METRICS GRID
        st.write("")
        with st.container():
            st.subheader("DATASET METRICS")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("RECORDS", df.shape[0])
            c2.metric("FEATURES", df.shape[1])
            c3.metric("MISSING", df.isnull().sum().sum())
            c4.metric("DUPLICATES", df.duplicated().sum())

        st.write("")

        # C. TABS INTERFACE
        tab1, tab2 = st.tabs(["DEEP PROFILING", "AUTOMATED DASHBOARD"])

        # --- TAB 1: AUTOMATED PROFILER ---
        with tab1:
            st.write("")
            col_q, col_b = st.columns([3, 1])
            with col_q:
                # We use this to simulate selecting a target, though automation scans all
                target_options = df.columns.tolist()
                selected_target = st.selectbox("SELECT TARGET VARIABLE FOR DEEP DIVE", target_options, label_visibility="collapsed")
            with col_b:
                run_btn = st.button("EXECUTE ANALYSIS", use_container_width=True)

            if run_btn:
                # 1. ANIMATION CONTAINER
                loader = st.empty()
                with loader.container():
                    lc1, lc2, lc3 = st.columns([1,2,1])
                    with lc2:
                        components.iframe(
                            "https://lottie.host/embed/705a9879-1c4b-45a1-b1ee-d7690f56f458/HMMnGjpbaU.lottie",
                            height=200,
                            scrolling=False
                        )
                        st.markdown("<center>PROCESSING STATISTICAL MODELS...</center>", unsafe_allow_html=True)

                # 2. PROCESSING (Real Calculation)
                time.sleep(2.5) # Force visible delay for the animation to be appreciated
                summary_text = generate_automated_summary(df)
                loader.empty()
                
                # 3. RESULTS
                res_col1, res_col2 = st.columns([1.5, 1])
                
                with res_col1:
                    st.markdown("#### EXECUTIVE SUMMARY")
                    st.info(summary_text)
                
                with res_col2:
                    st.markdown(f"#### VISUAL OUTPUT: {selected_target}")
                    
                    fig, ax = plt.subplots(figsize=(6,4))
                    fig.patch.set_facecolor('#1E2129')
                    ax.set_facecolor('#1E2129')
                    
                    # Logic to choose plot type based on data type
                    if pd.api.types.is_numeric_dtype(df[selected_target]):
                        sns.histplot(df[selected_target], color='#4DB6AC', kde=True, ax=ax)
                    else:
                        top_10 = df[selected_target].value_counts().head(10)
                        sns.barplot(x=top_10.values, y=top_10.index, palette="viridis", ax=ax)
                        
                    ax.tick_params(colors='white')
                    ax.xaxis.label.set_color('white')
                    ax.yaxis.label.set_color('white')
                    for spine in ax.spines.values():
                        spine.set_color('white')
                        
                    st.pyplot(fig)

        # --- TAB 2: AUTOMATED DASHBOARD ---
        with tab2:
            st.write("")
            
            numeric_df = df.select_dtypes(include=['float64', 'int64'])
            
            if not numeric_df.empty:
                # SECTION 1: CORRELATION
                st.markdown("#### 1. CORRELATION MATRIX")
                fig, ax = plt.subplots(figsize=(10, 4))
                fig.patch.set_facecolor('#1E2129')
                ax.set_facecolor('#1E2129')
                
                # Mask upper triangle for cleaner professional look
                mask = np.triu(np.ones_like(numeric_df.corr(), dtype=bool))
                
                sns.heatmap(numeric_df.corr(), annot=True, mask=mask, cmap='mako', fmt=".2f", 
                            linewidths=0.5, linecolor='#1E2129', ax=ax, cbar=False)
                
                plt.xticks(color='#E0E0E0'); plt.yticks(color='#E0E0E0', rotation=0)
                st.pyplot(fig)
                
                st.markdown("---")
                
                # SECTION 2: DISTRIBUTION GRAPHS
                st.markdown("#### 2. VARIABLE DISTRIBUTIONS")
                
                cols = st.columns(2)
                # Automate: Plot first 2 numeric columns
                for i, col_name in enumerate(numeric_df.columns[:2]):
                    with cols[i]:
                        st.caption(f"DISTRIBUTION: {col_name}")
                        fig_d, ax_d = plt.subplots(figsize=(6,4))
                        fig_d.patch.set_facecolor('#1E2129')
                        ax_d.set_facecolor('#1E2129')
                        
                        sns.boxplot(x=df[col_name], color="#26A69A", ax=ax_d)
                        
                        ax_d.tick_params(colors='white')
                        for spine in ax_d.spines.values():
                            spine.set_color('white')
                        st.pyplot(fig_d)
            else:
                st.info("NO NUMERIC DATA AVAILABLE FOR DASHBOARD")

    except Exception as e:
        st.error(f"FILE LOAD ERROR: {e}")

else:
    # Empty State
    with st.container():
        st.warning("SYSTEM STANDBY: PLEASE UPLOAD DATA SOURCE.")
