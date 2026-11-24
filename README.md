# UK & EU Law Argumentation Studio (A2UI + Streamlit + Gemini 4 Carbon)

A multi-agent legal argumentation, fact-checking, and sur-rebuttal workbench built with **Streamlit**, Google's **A2UI 1.0** declarative UI pattern, and **`gemini-4-carbon`** (`google-genai`).

Designed specifically for **UK Law (England & Wales)** and **EU / Assimilated Law** essays, featuring live **Google Search grounding** against primary legal sources (`legislation.gov.uk`, `caselaw.nationalarchives.gov.uk`, `lawcom.gov.uk`, `eur-lex.europa.eu`) and **OSCOLA** citation formatting.

## Project Structure

```text
uk-eu-law-a2ui-studio/
├── app.py                        # Main Streamlit app & multi-round session state
├── requirements.txt              # Python dependencies
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example      # API key template for local & Cloud deployment
├── schemas/
│   ├── __init__.py
│   └── a2ui_catalog.py           # Strict Pydantic A2UI 1.0 component catalog
├── agents/
│   ├── __init__.py
│   └── legal_agents.py           # 3-stage Gemini 4 Carbon agents + Search grounding
└── renderer/
    ├── __init__.py
    └── a2ui_streamlit.py         # Declarative A2UI JSON -> Streamlit native renderer
```

## Quick Start (Local)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add your `GEMINI_API_KEY`:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Deploy to Streamlit Community Cloud

1. Push this directory to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and connect your repository (`app.py` as the main file).
3. In **App settings -> Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   ```
4. Deploy.
