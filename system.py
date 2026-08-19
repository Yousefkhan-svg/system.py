import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
import base64
from datetime import datetime
from fpdf import FPDF
from groq import Groq
import streamlit.components.v1 as components

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
GROQ_API_KEY = "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"

DATA_FILE = "expenses.csv"
BUDGET_FILE = "budget.txt"
RECURRING_FILE = "recurring.csv"

# ---------------------------------------------------------
# Page Setup & Professional Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Executive AI Financial Terminal",
    layout="wide",
    page_icon="💼"
)

st.markdown("""
    <style>
    /* Dark Executive Theme */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Headings & High Contrast Accents */
    h1, h2, h3 {
        color: #f59e0b !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    /* Custom Metric Cards */
    .pro-card {
        background: rgba(30, 41, 59, 0.85);
        border: 1.5px solid #f59e0b;
        border-radius: 10px;
        padding: 14px 10px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
    }
    .pro-title {
        color: #94a3b8;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }
    .pro-value {
        color: #fbbf24;
        font-size: 1.25rem;
        font-weight: 800;
        word-wrap: break-word;
        white-space: normal;
        line-height: 1.2;
    }

    /* Custom Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(51, 65, 85, 0.6);
        border-radius: 8px;
        color: #cbd5e1;
        padding: 10px 20px;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background-color: #f59e0b !important;
        color: #0f172a !important;
        font-weight: 700;
    }

    /* Primary Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
        color: #0f172a;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Data Storage Functions
# ---------------------------------------------------------
def load_data():
    expected_cols = ["Date", "Type", "Category", "Amount", "Description", "Currency"]
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if "Type" not in df.columns: df["Type"] = "Expense"
        if "Currency" not in df.columns: df["Currency"] = "PKR"
        if not df.empty: df["Date"] = pd.to_datetime(df["Date"]).dt.date
        return df[expected_cols]
    return pd.DataFrame(columns=expected_cols)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def get_budget():
    if os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, "r") as f:
            try: return float(f.read().strip())
            except ValueError: return 0.0
    return 50000.0

def save_budget(val):
    with open(BUDGET_FILE, "w") as f: f.write(str(val))

def load_recurring():
    if os.path.exists(RECURRING_FILE):
        return pd.read_csv(RECURRING_FILE)
    return pd.DataFrame(columns=["Name", "Type", "Category", "Amount"])

def save_recurring(df):
    df.to_csv(RECURRING_FILE, index=False)

# ---------------------------------------------------------
# PDF Generator Function
# ---------------------------------------------------------
def generate_pdf_report(df, currency, budget):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "Executive Personal Financial Statement", ln=True, align='C')
    pdf.ln(8)
    
    pdf.set_font("Arial", size=11)
    pdf.cell(190, 7, f"Statement Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.cell(190, 7, f"Allocated Budget Target: {currency} {budget:,.2f}", ln=True)
    pdf.ln(4)

    inc = df[df["Type"] == "Income"]["Amount"].sum()
    exp = df[df["Type"] == "Expense"]["Amount"].sum()
    sav = df[df["Type"] == "Saving"]["Amount"].sum()
    inv = df[df["Type"] == "Investment"]["Amount"].sum()

    pdf.set_font("Arial", 'B', 11)
    pdf.cell(190, 7, f"Total Income: {currency} {inc:,.2f}  |  Total Expenses: {currency} {exp:,.2f}", ln=True)
    pdf.cell(190, 7, f"Total Savings: {currency} {sav:,.2f}  |  Investments: {currency} {inv:,.2f}", ln=True)
    pdf.cell(190, 7, f"Net Liquid Balance: {currency} {(inc - exp - sav - inv):,.2f}", ln=True)
    pdf.ln(8)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(28, 8, "Date", 1)
    pdf.cell(28, 8, "Type", 1)
    pdf.cell(42, 8, "Category", 1)
    pdf.cell(32, 8, "Amount", 1)
    pdf.cell(60, 8, "Description", 1)
    pdf.ln()

    pdf.set_font("Arial", size=9)
    for _, row in df.tail(20).iterrows():
        pdf.cell(28, 7, str(row["Date"]), 1)
        pdf.cell(28, 7, str(row["Type"]), 1)
        pdf.cell(42, 7, str(row["Category"]), 1)
        pdf.cell(32, 7, f"{row['Amount']:,.2f}", 1)
        pdf.cell(60, 7, str(row["Description"])[:30], 1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin1')

# ---------------------------------------------------------
# Auto-Stop Voice Recorder Component
# ---------------------------------------------------------
def auto_stop_mic_component():
    html_code = """
    <div style="font-family: sans-serif; text-align: center; background: #1e293b; padding: 12px; border-radius: 10px; border: 1px solid #f59e0b;">
        <button id="recordBtn" style="background: linear-gradient(90deg, #f59e0b, #d97706); color: #0f172a; font-weight: bold; border: none; padding: 10px 22px; border-radius: 8px; cursor: pointer; font-size: 0.95rem;">
            ⚡ Tap & Speak (Fast Auto-Stop)
        </button>
        <p id="status" style="color: #94a3b8; font-size: 0.8rem; margin-top: 8px; margin-bottom: 0;">Click to speak — stops instantly when you finish.</p>
    </div>

    <script>
    let mediaRecorder;
    let audioChunks = [];
    let audioContext;
    let analyser;
    let microphone;
    let silenceTimer = null;
    
    const SILENCE_THRESHOLD = 10;
    const SILENCE_DURATION = 650;

    const recordBtn = document.getElementById('recordBtn');
    const status = document.getElementById('status');

    recordBtn.addEventListener('click', async () => {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            stopRecording();
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } 
            });
            
            audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
            analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            
            microphone = audioContext.createMediaStreamSource(stream);
            microphone.connect(analyser);

            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                status.innerText = "⚡ Processing audio...";
                recordBtn.innerText = "⏳ Processing...";
                
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    const base64Audio = reader.result.split(',')[1];
                    window.parent.postMessage({ type: 'streamlit:setComponentValue', value: base64Audio }, '*');
                };
                
                setTimeout(() => {
                    recordBtn.innerText = "⚡ Tap & Speak (Fast Auto-Stop)";
                    recordBtn.style.background = "linear-gradient(90deg, #f59e0b, #d97706)";
                    status.innerText = "Done! Process completed.";
                }, 400);
            };

            mediaRecorder.start(100);
            recordBtn.innerText = "🔴 Listening... Speak Now";
            recordBtn.style.background = "#ef4444";
            status.innerText = "Listening... Will auto-stop ~0.6s after you stop speaking.";

            detectSilence();
        } catch (err) {
            status.innerText = "Microphone error or permission denied.";
        }
    });

    function detectSilence() {
        const dataArray = new Uint8Array(analyser.frequencyBinCount);

        function check() {
            if (!mediaRecorder || mediaRecorder.state !== "recording") return;

            analyser.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i];
            }
            let average = sum / dataArray.length;

            if (average < SILENCE_THRESHOLD) {
                if (!silenceTimer) {
                    silenceTimer = setTimeout(() => {
                        stopRecording();
                    }, SILENCE_DURATION);
                }
            } else {
                if (silenceTimer) {
                    clearTimeout(silenceTimer);
                    silenceTimer = null;
                }
            }

            requestAnimationFrame(check);
        }
        check();
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            if (microphone) microphone.mediaStream.getTracks().forEach(track => track.stop());
            if (audioContext) audioContext.close();
        }
    }
    </script>
    """
    return components.html(html_code, height=110)

# ---------------------------------------------------------
# Groq AI Engine
# ---------------------------------------------------------
SYSTEM_PROMPT = """
You are an executive personal financial secretary.
Extract structured transaction parameters from user text or voice transcriptions in English, Urdu, or Roman Urdu.
Translate non-English descriptions into concise English.

Reference Date: {today}
Currency: {currency}

Validation Constraints:
- Type MUST be strictly one of: "Expense", "Income", "Saving", "Investment"
- Category MUST be strictly one of: "Food & Groceries", "Transport & Fuel", "Bills & Utilities", "Shopping", "Health & Wellness", "Salary & Income", "Savings & Funds", "Investments", "Other"
- Amount MUST be a positive numerical float.

Return raw JSON only:
{{
    "date": "YYYY-MM-DD",
    "type": "Expense",
    "category": "Food & Groceries",
    "amount": 500.0,
    "description": "Short explanation in English"
}}
"""

def parse_input_groq(text_input, audio_bytes, currency, file_filename="voice.webm"):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        if audio_bytes:
            transcription = client.audio.transcriptions.create(
                file=(file_filename, audio_bytes),
                model="whisper-large-v3",
                response_format="text"
            )
            text_to_process = transcription
            st.info(f"🗣️ **Voice Recognized:** \"{transcription}\"")
        else:
            text_to_process = text_input

        prompt = SYSTEM_PROMPT.format(today=today_str, currency=currency)
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": text_to_process}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return (datetime.strptime(data["date"], "%Y-%m-%d").date(), data["type"], data["category"], float(data["amount"]), data["description"])
    except Exception as e:
        st.error(f"Processing Error: {e}")
        return None

def ask_advisor_groq(question, df, currency):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        context = df.to_string()
        prompt = f"You are a high-level personal financial advisor. Analyze these transaction records:\n{context}\n\nUser Question: {question}\nProvide concise, high-value financial recommendations using currency {currency}."
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Advisor Engine Error: {e}"

# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------
df = load_data()
current_budget = get_budget()

st.sidebar.title("💼 Control Panel")
currency = st.sidebar.selectbox("Base Currency", ["PKR", "USD", "EUR", "GBP", "INR", "AED"])
new_budget = st.sidebar.number_input("Monthly Expense Cap", min_value=0.0, value=current_budget, step=1000.0)

if new_budget != current_budget:
    save_budget(new_budget)
    st.sidebar.success("Budget threshold updated!")
    st.rerun()

st.sidebar.divider()
st.sidebar.caption("⚡ Powered by High-Speed Groq Llama 3.3 Engine")

# ---------------------------------------------------------
# Main App Header & Budget Tracker
# ---------------------------------------------------------
st.title("💼 Executive AI Financial Terminal")

if not df.empty:
    current_month = datetime.now().month
    month_data = df[pd.to_datetime(df['Date']).dt.month == current_month]
    
    total_exp_month = month_data[month_data['Type'] == 'Expense']['Amount'].sum()
    total_sav_month = month_data[month_data['Type'].isin(['Saving', 'Investment'])]['Amount'].sum()

    budget_usage = (total_exp_month / current_budget * 100) if current_budget > 0 else 0
    
    if budget_usage >= 100:
        st.error(f"⚠️ **Budget Cap Exceeded:** Spent {currency} {total_exp_month:,.2f} of {currency} {current_budget:,.2f} threshold.")
    else:
        st.info(f"📊 **Current Month Spend:** {currency} {total_exp_month:,.2f} / {currency} {current_budget:,.2f} | **Capital Savings:** {currency} {total_sav_month:,.2f}")

# ---------------------------------------------------------
# Processing Center
# ---------------------------------------------------------
st.markdown("### ⚡ Quick Entry Command Center")

# Direct Text and Auto-Stop Mic
st.markdown("##### Direct Text or Auto-Stop Live Mic")
input_col1, input_col2 = st.columns([1, 2])

with input_col1:
    audio_record = st.audio_input("🎙️ Standard Browser Recording")

with input_col2:
    text_input = st.text_input("💬 Natural Language Input", placeholder="e.g. Spent 3500 PKR on petrol today or Aaj 1200 ka lunch kiya")

auto_stop_mic_component()

if st.button("⚡ Execute Transaction Entry", use_container_width=True):
    if audio_record or text_input:
        with st.spinner("Analyzing transaction data..."):
            parsed = parse_input_groq(text_input, audio_record.read() if audio_record else None, currency)

            if parsed:
                p_date, p_type, p_cat, p_amt, p_desc = parsed
                new_entry = pd.DataFrame([[p_date, p_type, p_cat, p_amt, p_desc, currency]], columns=df.columns)
                df = pd.concat([df, new_entry], ignore_index=True)
                save_data(df)
                st.success(f"Recorded: **{p_type}** | **{p_cat}**: {currency} {p_amt:,.2f} ({p_desc})")
                st.rerun()

st.divider()

# File Upload Section
st.markdown("##### Drop Pre-Recorded Voice Note (.m4a, .mp3, .wav)")
uploaded_audio = st.file_uploader("📂 Select or drag a recorded audio file from phone/PC", type=["m4a", "mp3", "wav", "ogg", "webm"])

if uploaded_audio is not None:
    if st.button("⚡ Process Audio File", use_container_width=True):
        with st.spinner("Transcribing and processing uploaded file..."):
            audio_bytes = uploaded_audio.read()
            parsed = parse_input_groq("", audio_bytes, currency, file_filename=uploaded_audio.name)
            if parsed:
                p_date, p_type, p_cat, p_amt, p_desc = parsed
                new_entry = pd.DataFrame([[p_date, p_type, p_cat, p_amt, p_desc, currency]], columns=df.columns)
                df = pd.concat([df, new_entry], ignore_index=True)
                save_data(df)
                st.success(f"Recorded from File: **{p_type}** | **{p_cat}**: {currency} {p_amt:,.2f} ({p_desc})")
                st.rerun()

st.divider()

# ---------------------------------------------------------
# Tabs System
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Executive Dashboard", 
    "🤖 AI Financial Advisor", 
    "🔄 Recurring Presets", 
    "💬 Telegram Integration",
    "📄 PDF Statements", 
    "⚙️ Ledger Console"
])

# TAB 1: Executive Dashboard
with tab1:
    if not df.empty:
        inc_total = df[df["Type"] == "Income"]["Amount"].sum()
        exp_total = df[df["Type"] == "Expense"]["Amount"].sum()
        sav_total = df[df["Type"] == "Saving"]["Amount"].sum()
        inv_total = df[df["Type"] == "Investment"]["Amount"].sum()
        net_balance = inc_total - exp_total - sav_total - inv_total

        m1, m2, m3, m4, m5 = st.columns(5)
        
        with m1:
            st.markdown(f'''
                <div class="pro-card">
                    <div class="pro-title">Total Income</div>
                    <div class="pro-value">{currency} {inc_total:,.2f}</div>
                </div>
            ''', unsafe_allow_html=True)

        with m2:
            st.markdown(f'''
                <div class="pro-card">
                    <div class="pro-title">Total Expenses</div>
                    <div class="pro-value">{currency} {exp_total:,.2f}</div>
                </div>
            ''', unsafe_allow_html=True)

        with m3:
            st.markdown(f'''
                <div class="pro-card">
                    <div class="pro-title">Total Savings</div>
                    <div class="pro-value">{currency} {sav_total:,.2f}</div>
                </div>
            ''', unsafe_allow_html=True)

        with m4:
            st.markdown(f'''
                <div class="pro-card">
                    <div class="pro-title">Investments</div>
                    <div class="pro-value">{currency} {inv_total:,.2f}</div>
                </div>
            ''', unsafe_allow_html=True)

        with m5:
            st.markdown(f'''
                <div class="pro-card">
                    <div class="pro-title">Liquid Balance</div>
                    <div class="pro-value">{currency} {net_balance:,.2f}</div>
                </div>
            ''', unsafe_allow_html=True)

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Capital Allocation")
            fig_type = px.pie(df, names="Type", values="Amount", hole=0.45, color_discrete_sequence=["#f59e0b", "#10b981", "#3b82f6", "#8b5cf6"])
            st.plotly_chart(fig_type, use_container_width=True)

        with c2:
            st.subheader("Expense Distribution")
            exp_df = df[df["Type"] == "Expense"]
            if not exp_df.empty:
                fig_cat = px.pie(exp_df, names="Category", values="Amount", color_discrete_sequence=px.colors.qualitative.Bold)
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("No expense data recorded.")
    else:
        st.info("No transaction data available.")

# TAB 2: AI Financial Advisor
with tab2:
    st.subheader("🤖 Financial Intelligence Advisor")
    user_q = st.text_input("Ask for financial recommendations or analytical insights:")
    if st.button("Generate Strategy Report"):
        if user_q:
            with st.spinner("Analyzing ledger statistics..."):
                answer = ask_advisor_groq(user_q, df, currency)
                st.markdown(answer)

# TAB 3: Recurring Presets
with tab3:
    st.subheader("🔄 Automated Recurring Transactions")
    rec_df = load_recurring()
    
    with st.form("add_rec_form", clear_on_submit=True):
        rc1, rc2, rc3, rc4 = st.columns(4)
        r_name = rc1.text_input("Title (e.g. Office Rent)")
        r_type = rc2.selectbox("Type", ["Expense", "Investment", "Saving"])
        r_cat = rc3.selectbox("Category", ["Bills & Utilities", "Food & Groceries", "Investments", "Savings & Funds", "Other"])
        r_amt = rc4.number_input("Amount", min_value=0.0)
        
        if st.form_submit_button("Save Recurring Configuration"):
            if r_name and r_amt > 0:
                new_rec = pd.DataFrame([[r_name, r_type, r_cat, r_amt]], columns=rec_df.columns)
                rec_df = pd.concat([rec_df, new_rec], ignore_index=True)
                save_recurring(rec_df)
                st.success("Preset stored successfully.")
                st.rerun()

    if not rec_df.empty:
        st.dataframe(rec_df, use_container_width=True)
        if st.button("⚡ Execute All Presets for Today"):
            today_date = datetime.now().date()
            rows_to_add = []
            for _, row in rec_df.iterrows():
                rows_to_add.append([today_date, row["Type"], row["Category"], row["Amount"], f"Automated Recurring: {row['Name']}", currency])
            
            new_entries = pd.DataFrame(rows_to_add, columns=df.columns)
            df = pd.concat([df, new_entries], ignore_index=True)
            save_data(df)
            st.success("All recurring entries appended to ledger.")
            st.rerun()

# TAB 4: Free Telegram Integration Guide
with tab4:
    st.subheader("💬 Free Telegram Auto-Sync Engine")
    st.write("Log expenses seamlessly by messaging your dedicated Telegram Bot directly.")
    
    st.markdown("""
    **Quick Execution Workflow:**
    1. **Create a Bot**: Message `@BotFather` on Telegram, use `/newbot`, and get your API Token.
    2. **Run Bot Script**: Start your background polling script by running `python telegram_bot.py` in a separate terminal.
    3. **Send Text or Voice**: Message your bot on Telegram (e.g. *"500 lunch"* or *"1500 petrol"*), and it will automatically parse and save it into your `expenses.csv`.
    """)

# TAB 5: PDF Reports
with tab5:
    st.subheader("📄 Official Statement Generator")
    if not df.empty:
        pdf_bytes = generate_pdf_report(df, currency, current_budget)
        st.download_button(
            label="📥 Export Monthly Statement (PDF)",
            data=pdf_bytes,
            file_name=f"financial_statement_{datetime.now().strftime('%Y_%m_%d')}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Log transactions to generate statements.")

# TAB 6: Ledger Console
with tab6:
    st.subheader("⚙️ Financial Ledger Console")
    if not df.empty:
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="ledger_editor")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("💾 Apply Ledger Modifications"):
                save_data(edited_df)
                st.success("Ledger synchronized.")
                st.rerun()
        with col_s2:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Raw Data (CSV)", data=csv_data, file_name="expenses.csv", mime="text/csv")
