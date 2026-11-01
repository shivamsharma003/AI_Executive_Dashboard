
import streamlit as st
from groq import Groq
import os


def generate_insights(summary_text: str) -> str:
    """
    Send business KPI summary to Groq AI and get executive report back.
    """

    # Load API key from Streamlit Secrets or environment variables
    try:
        GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

    if not GROQ_API_KEY:
        raise ValueError(
            "Groq API key not found. Please configure GROQ_API_KEY in Streamlit Secrets."
        )

    client = Groq(
        api_key=GROQ_API_KEY,
        timeout=60.0,
        max_retries=2
    )

    prompt = f"""You are a senior business analyst and strategic consultant specializing in retail sales performance.

Based on the following Superstore business performance data, write a comprehensive executive-level insight report.

Structure your report exactly like this:

📊 Performance Overview
Write 2-3 sentences summarizing overall business health based on the numbers.

✅ Key Strengths
List 3 key strengths with brief explanation for each based on the data.

⚠️ Areas of Concern
List 2-3 areas that need leadership attention based on the data.

🎯 Strategic Recommendations
Provide 4 specific actionable recommendations for leadership based on the data.

🔮 Outlook
Write 2-3 sentences about short-term forecast and next steps based on the data.

Use the actual numbers from the data in your report. Be specific and data-driven. Reference categories, regions, segments, and sub-categories where relevant.

--- BUSINESS DATA ---
{summary_text}
--- END ---"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are a senior business analyst who writes clear, concise, data-driven executive reports for retail companies. Always use the actual numbers provided in your analysis."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1000,
        temperature=0.7
    )

    return response.choices[0].message.content
