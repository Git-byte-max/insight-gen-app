# InsightGen: Agentic AI Analytics Platform

InsightGen is an advanced, AI-powered data analytics suite built with Streamlit and CrewAI. It allows users to upload datasets and interact with autonomous AI agents that plan, code, and report on data patterns, complete with downloadable visualizations and PDF reporting.

## 🚀 Features
* **AI Data Analyst:** Chat directly with your data. The multi-agent system writes and executes custom Python scripts on the fly.
* **Visual Dashboard:** Auto-generated correlation matrices, histograms, and scatter plots.
* **One-Click Downloads:** Download individual plots as PNGs or export entire multi-page PDF Intelligence Reports.
* **Privacy First:** Data analysis happens within the isolated execution environment.

## 🛠️ Local Setup
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment and install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file in the root directory and add your OpenAI API Key: `OPENAI_API_KEY="sk-..."`
5. Run the app: `streamlit run app.py`

## ☁️ Streamlit Cloud Deployment
If deploying to Streamlit Cloud, ensure you navigate to **App Settings > Secrets** and paste your API key in the following format to prevent runtime errors:
`OPENAI_API_KEY="sk-..."`
