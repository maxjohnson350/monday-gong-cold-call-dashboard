import streamlit as st
import google.generativeai as genai
from typing import Optional

st.set_page_config(
    page_title="Cold Call Script Generator",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    [data-testid="stMainBlockContainer"] {
        padding-top: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_resource
def get_gemini_client():
    """Initialize and cache the Gemini client."""
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("❌ GEMINI_API_KEY not found in secrets. Add it to .streamlit/secrets.toml")
        st.stop()
    genai.configure(api_key=api_key)
    return genai


def generate_cold_call_opener(name: str, title: str, company: str, industry: str) -> Optional[str]:
    """Generate a 15-second personalized cold call opener."""
    client = get_gemini_client()

    prompt = f"""You are an expert sales development representative. Generate a SINGLE, concise 15-second cold call opener (approximately 40-50 words).

Lead Information:
- Name: {name}
- Title: {title}
- Company: {company}
- Industry: {industry}

Requirements:
- Be personalized and reference their specific role/company
- Create urgency or interest immediately
- Be natural and conversational
- NO closing question (save that for real call)
- NO salutation like "Hi [Name]" - start directly with value

Generate ONLY the opener script, nothing else."""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating opener: {str(e)}")
        return None


def generate_objection_rebuttal(name: str, title: str, company: str, industry: str, objection: str) -> Optional[str]:
    """Generate a quick 1-sentence rebuttal to an objection."""
    client = get_gemini_client()

    objection_prompts = {
        "Price": "The prospect says your solution is too expensive.",
        "No Time": "The prospect says they don't have time to talk.",
        "Using Competitor": "The prospect says they're already using a competitor's solution."
    }

    objection_context = objection_prompts.get(objection, objection)

    prompt = f"""You are an expert sales development representative. Generate a SINGLE, punchy 1-sentence rebuttal (approximately 15-20 words max).

Lead Information:
- Name: {name}
- Title: {title}
- Company: {company}
- Industry: {industry}

Objection: {objection_context}

Requirements:
- Be direct and confident
- Acknowledge their concern briefly then redirect
- NO filler words or hesitation
- Make them want to keep listening
- Reference their specific situation if possible

Generate ONLY the rebuttal sentence, nothing else."""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Error generating rebuttal: {str(e)}")
        return None


def main():
    """Main app logic."""
    st.title("📞 Cold Call Script Generator")
    st.markdown("Generate personalized live call scripts powered by Google Gemini")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Lead Information")
        st.markdown("Paste the lead's details from Gong Engage below:")

        lead_input = st.text_area(
            "Lead Info (Name, Title, Company, Industry)",
            height=120,
            placeholder="Example:\nName: John Smith\nTitle: VP of Sales\nCompany: Acme Corp\nIndustry: SaaS",
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("###")
        st.info("ℹ️ **Paste Format:**\nName: ...\nTitle: ...\nCompany: ...\nIndustry: ...")

    st.divider()

    if st.button("🚀 Generate Live Call Script", use_container_width=True, type="primary"):
        if not lead_input.strip():
            st.warning("Please paste the lead's information first.")
            return

        parsed_data = parse_lead_input(lead_input)

        if not all([parsed_data.get("name"), parsed_data.get("title"),
                   parsed_data.get("company"), parsed_data.get("industry")]):
            st.error("Could not parse all required fields. Please ensure you have: Name, Title, Company, Industry")
            return

        with st.spinner("🤖 Generating personalized opener..."):
            opener = generate_cold_call_opener(
                parsed_data["name"],
                parsed_data["title"],
                parsed_data["company"],
                parsed_data["industry"]
            )

        if opener:
            st.session_state.current_lead = parsed_data
            st.session_state.current_opener = opener
            st.session_state.show_opener = True
            st.rerun()

    if st.session_state.get("show_opener"):
        st.divider()
        st.subheader("✅ Your 15-Second Cold Call Opener")

        lead = st.session_state.current_lead
        st.markdown(f"""
        **For:** {lead['name']} | {lead['title']} at {lead['company']}

        ---

        > {st.session_state.current_opener}
        """)

        st.divider()
        st.subheader("🎯 Objection Handlers")
        st.markdown("Click an objection to generate a quick rebuttal:")

        cols = st.columns(3)
        objections = ["Price", "No Time", "Using Competitor"]

        for idx, objection in enumerate(objections):
            with cols[idx]:
                if st.button(f"💬 {objection}", use_container_width=True):
                    with st.spinner(f"Generating {objection} rebuttal..."):
                        rebuttal = generate_objection_rebuttal(
                            lead["name"],
                            lead["title"],
                            lead["company"],
                            lead["industry"],
                            objection
                        )

                    if rebuttal:
                        st.session_state.last_rebuttal = rebuttal
                        st.session_state.last_objection = objection
                        st.rerun()

        if st.session_state.get("last_rebuttal"):
            st.info(f"""
            **Objection:** {st.session_state.last_objection}

            **Your Rebuttal:**
            > {st.session_state.last_rebuttal}
            """)

        if st.button("🔄 Start Over", use_container_width=False):
            st.session_state.clear()
            st.rerun()


def parse_lead_input(text: str) -> dict:
    """Parse lead information from pasted text."""
    data = {
        "name": "",
        "title": "",
        "company": "",
        "industry": ""
    }

    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if "name" in key and not data["name"]:
                data["name"] = value
            elif "title" in key and not data["title"]:
                data["title"] = value
            elif "company" in key and not data["company"]:
                data["company"] = value
            elif "industry" in key and not data["industry"]:
                data["industry"] = value

    return data


if __name__ == "__main__":
    if "show_opener" not in st.session_state:
        st.session_state.show_opener = False

    main()
