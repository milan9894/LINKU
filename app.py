import os
import re
import math
from io import BytesIO
from collections import Counter

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pypdf import PdfReader

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="LINKU — Your Student Ecosystem",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
DEBUG = os.getenv("LINKU_DEBUG", "false").lower() == "true"

# If the whole PDF text fits under this many characters (~60k tokens),
# MILANO can read all of it instead of relying on keyword retrieval.
FULL_DOC_CHAR_LIMIT = 250_000

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        api_key = None

client = genai.Client(api_key=api_key) if api_key else None


# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --bg:#0B0A14; --panel:#141222; --panel2:#1B1830;
        --purple:#A78BFA; --pink:#E9A8F7; --muted:#AAA5C1;
        --white:#F8F6FF;
    }
    html {font-size:17px}
    .stApp {
        background:radial-gradient(ellipse at 10% 0%,#28204B 0%,transparent 38%),
        radial-gradient(ellipse at 95% 40%,#241630 0%,transparent 32%),var(--bg);
        color:var(--white);font-family:'DM Sans',sans-serif;font-size:1.05rem;
    }
    [data-testid="stHeader"] {background:transparent}
    [data-testid="stAppViewContainer"] .main .block-container {
        max-width:1200px;padding-top:2rem;padding-bottom:4rem;
    }
    h1,h2,h3 {font-family:'Manrope',sans-serif!important;color:var(--white)!important;letter-spacing:-.5px}
    h1 {font-size:2.8rem!important} h2 {font-size:2rem!important} h3 {font-size:1.55rem!important}
    p,li {color:#D1CCE2;font-size:1.05rem;line-height:1.8}
    label {font-size:1rem!important}
    [data-testid="stSidebar"] {background:rgba(16,14,29,.96);border-right:1px solid #302846}
    [data-testid="stSidebar"] p {color:#C9C1DF;font-size:1rem;line-height:1.7}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {font-size:.9rem}
    .brand {
        font-family:'Manrope',sans-serif;font-size:2.9rem;font-weight:800;letter-spacing:-2px;
        background:linear-gradient(100deg,#FFF 10%,#C4B5FD 55%,#F0ABFC 100%);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0;
    }
    .eyebrow {color:#C4B5FD;text-transform:uppercase;letter-spacing:2.4px;font-size:.85rem;font-weight:700}

    /* Compact hero so the tools are reachable without long scrolling */
    .hero {padding:.6rem 0 .6rem}
    .hero h1 {font-size:clamp(2.4rem,4.6vw,3.6rem)!important;line-height:1.12;margin:.5rem 0 .8rem}
    .hero p {max-width:760px;color:#B8B1D0;font-size:1.1rem;line-height:1.8;margin:0}

    .module-card {
        background:linear-gradient(145deg,rgba(35,29,58,.94),rgba(19,17,33,.96));
        border:1px solid #39304F;border-radius:20px;padding:1.2rem 1.5rem;
        margin:.6rem 0 .4rem;box-shadow:0 12px 40px rgba(0,0,0,.12);
    }
    .module-card h3 {margin:.7rem 0 .3rem;font-size:1.5rem!important}
    .module-card p {font-size:1rem;line-height:1.7;color:#B9B2CE;margin:0}
    .pill {display:inline-block;border:1px solid #51416F;border-radius:100px;color:#D8C9FF;
        padding:6px 12px;font-size:.75rem;letter-spacing:1px;font-weight:700}
    .section-label {font-size:.9rem;color:#B8A5F5;letter-spacing:2px;text-transform:uppercase;
        font-weight:700;margin:1rem 0 .4rem}

    /* Tabs: purple highlight, no red focus box */
    div[data-testid="stTabs"] button {color:#BEB5D6;font-size:1.05rem;font-weight:600;
        border-radius:10px;padding:.7rem 1rem;outline:none!important;box-shadow:none!important}
    div[data-testid="stTabs"] button:focus,
    div[data-testid="stTabs"] button:focus-visible,
    div[data-testid="stTabs"] button:active {outline:none!important;box-shadow:none!important;border-color:transparent!important}
    div[data-testid="stTabs"] button[aria-selected="true"] {color:#E6DFFF;background:#292142}
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {background-color:#B8A5F5!important}
    div[data-testid="stTabs"] [data-baseweb="tab-border"] {background-color:#302846!important}

    /* Buttons: primary is filled, secondary (e.g. Clear) is outlined */
    .stButton>button {border:1px solid #59477D;border-radius:12px;
        background:linear-gradient(115deg,#7C5AC8,#A278D8);color:white;
        font-size:1rem;font-weight:700;padding:.8rem 1.1rem;min-height:48px;transition:all .2s}
    .stButton>button:hover {border-color:#D4C1FF;background:linear-gradient(115deg,#906EE0,#B38AE8);color:white}
    .stButton>button[kind="secondary"],
    .stButton>button[data-testid="stBaseButton-secondary"] {
        background:transparent;border:1px solid #59477D;color:#D8C9FF;font-weight:600}
    .stButton>button[kind="secondary"]:hover,
    .stButton>button[data-testid="stBaseButton-secondary"]:hover {
        background:rgba(167,139,250,.14);border-color:#B8A5F5;color:#F0EAFF}

    [data-testid="stFileUploader"] {background:rgba(29,24,47,.7);border:1px dashed #75619D;
        border-radius:16px;padding:1.3rem}
    [data-testid="stFileUploader"] section {background:transparent}
    [data-testid="stFileUploader"] p,[data-testid="stFileUploader"] small {font-size:.98rem;line-height:1.7}
    [data-testid="stChatMessage"] {background:rgba(30,25,48,.7);border:1px solid #332A49;
        border-radius:16px;padding:1.2rem;margin-bottom:.9rem}
    [data-testid="stChatMessage"] p,[data-testid="stChatMessage"] li {font-size:1.05rem;line-height:1.85}
    [data-testid="stChatInput"] {border-color:#625080;border-radius:16px}
    [data-testid="stChatInput"] textarea {color:#F8F6FF;font-size:1.05rem}
    [data-testid="stCaptionContainer"] p {font-size:.9rem;line-height:1.65;color:#AAA2C3}
    [data-testid="stAlert"] {border-radius:12px}
    hr {border-color:#302742}
    #MainMenu,footer {visibility:hidden}
    .stAppDeployButton,[data-testid="stAppDeployButton"] {display:none}
    @media(max-width:700px) {
        html {font-size:15px}
        [data-testid="stAppViewContainer"] .main .block-container {padding-left:1rem;padding-right:1rem}
        .hero h1 {font-size:2.2rem!important}
        .hero p {font-size:1.02rem}
        .module-card {padding:1rem}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SHARED API HANDLING
# ============================================================

def friendly_api_error(exc):
    detail = str(exc).lower()

    if "resource_exhausted" in detail or "quota" in detail or "rate limit" in detail \
            or re.search(r"\b429\b", detail):
        return (
            "The AI service has reached its current request limit. "
            "Please try again later."
        )
    if any(x in detail for x in ("permission_denied", "api key", "unauthenticated")) \
            or re.search(r"\b(401|403)\b", detail):
        return "The AI service could not authorize this request. Check the API configuration."
    if "not_found" in detail or "not found" in detail or re.search(r"\b404\b", detail):
        return "The configured AI model may be unavailable to this API project. Check the model configuration."
    return "The AI service couldn't complete that request. Please try again in a moment."


def stream_answer(contents, system_instruction=None, temperature=0.4):
    """Yield the model's answer piece by piece (for st.write_stream)."""
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
    )

    for chunk in client.models.generate_content_stream(
        model=MODEL, contents=contents, config=config
    ):
        text = getattr(chunk, "text", None)
        if text:
            yield text


def show_api_error(exc):
    st.warning(friendly_api_error(exc))
    if DEBUG:
        st.caption(f"Developer detail: {exc}")


def to_contents(history):
    """Convert chat history into Gemini role-based contents."""
    contents = []
    for m in history:
        role = "user" if m["role"] == "user" else "model"
        part = types.Part(text=m["content"])

        if not contents and role == "model":
            continue  # the conversation must start with a user turn
        if contents and contents[-1].role == role:
            contents[-1].parts.append(part)  # merge consecutive same-role turns
        else:
            contents.append(types.Content(role=role, parts=[part]))

    return contents


# ============================================================
# PDF EXTRACTION AND CHUNKING
# ============================================================

@st.cache_data(show_spinner="Reading your PDF...")
def extract_pdf_cached(data: bytes):
    """Extract selectable PDF text while retaining original page numbers."""
    reader = PdfReader(BytesIO(data))
    pages = []

    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        if text:
            pages.append({"page": number, "text": text})

    return pages


def split_text(text, size=1100, overlap=180):
    """Split text with overlap, preferring paragraph or sentence boundaries."""
    if size <= 0:
        raise ValueError("Chunk size must be positive.")

    overlap = max(0, min(overlap, size - 1))
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))

        if end < len(text):
            # Avoid cutting off a sentence or paragraph when practical.
            boundary = max(
                text.rfind("\n", start + size // 2, end),
                text.rfind(". ", start + size // 2, end),
            )
            if boundary > start:
                end = boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(start + 1, end - overlap)

    return chunks


# ============================================================
# EXPERIMENT-AWARE QUERY EXPANSION
# ============================================================

ORDINALS = {
    "first": 1, "one": 1,
    "second": 2, "two": 2,
    "third": 3, "three": 3,
    "fourth": 4, "four": 4,
    "fifth": 5, "five": 5,
    "sixth": 6, "six": 6,
    "seventh": 7, "seven": 7,
    "eighth": 8, "eight": 8,
    "ninth": 9, "nine": 9,
    "tenth": 10, "ten": 10,
    "eleventh": 11, "eleven": 11,
    "twelfth": 12, "twelve": 12,
    "thirteenth": 13, "thirteen": 13,
    "fourteenth": 14, "fourteen": 14,
    "fifteenth": 15, "fifteen": 15,
    "sixteenth": 16, "sixteen": 16,
    "seventeenth": 17, "seventeen": 17,
    "eighteenth": 18, "eighteen": 18,
    "nineteenth": 19, "nineteen": 19,
    "twentieth": 20, "twenty": 20,
}

STOPWORDS = {
    "what", "when", "where", "which", "with", "that", "this",
    "from", "have", "does", "explain", "describe", "about",
    "your", "their", "there", "into", "also", "tell", "the",
    "and", "for", "are", "was", "were", "how", "key", "points",
    "state", "list", "give", "show", "can", "you", "all", "its",
    "important", "write", "mention", "summarize", "summary",
    "please", "could", "would", "should", "need", "want",
    "experiment", "experiments", "exp", "one", "th",
}


def tokenize(text):
    return [
        word.lower()
        for word in re.findall(r"\b[a-zA-Z0-9]+\b", text)
    ]


def get_experiment_number(question):
    """Recognize 'experiment 12', '12th experiment', or '12th one'."""
    q = question.lower()

    numeric = re.search(
        r"\b(?:experiment|experiments|exp\.?)\s*(?:no\.?|number)?\s*[:#.-]?\s*(\d{1,2})\b"
        r"|\b(\d{1,2})(?:st|nd|rd|th)\s*(?:experiment|one)\b",
        q,
    )

    if numeric:
        return int(numeric.group(1) or numeric.group(2))

    if re.search(r"\b(experiment|experiments|exp\.?)\b", q) or re.search(
        r"\b\d{1,2}(?:st|nd|rd|th)\s+one\b", q
    ):
        for word, number in sorted(ORDINALS.items(), key=lambda x: -len(x[0])):
            if re.search(rf"\b{re.escape(word)}\b", q):
                return number

    return None


def extract_experiment_titles(pages):
    """
    Find possible experiment titles in explicit "Experiment N: Title" headings
    and, on contents/index pages only, in numbered lists.
    Results are hypotheses for retrieval only; the model must verify evidence.
    """
    titles = {}

    for page in pages:
        is_contents = bool(re.search(
            r"\b(table of contents|contents|index|list of experiments)\b",
            page["text"][:500],
            re.IGNORECASE,
        ))
        lines = [re.sub(r"\s+", " ", line).strip() for line in page["text"].splitlines()]

        for line in lines:
            if not line or len(line) > 220:
                continue

            patterns = [
                # Experiment 12: Title / Exp. No. 12 - Title
                r"^\s*(?:experiment|exp\.?|ex\.?)\s*(?:no\.?|number)?\s*"
                r"(\d{1,2})\s*[:.)\-–]\s*(.{5,160})$",
                # 12. Title / 12) Title -- only trusted on contents pages,
                # otherwise numbered procedure steps look like titles.
                r"^\s*(\d{1,2})\s*[.)]\s+(.{5,160})$",
            ]

            for pattern_index, pattern in enumerate(patterns):
                if pattern_index == 1 and not is_contents:
                    continue

                match = re.match(pattern, line, re.IGNORECASE)
                if not match:
                    continue

                number = int(match.group(1))
                title = match.group(2).strip(" .:-–")

                if number < 1 or len(title) < 5:
                    continue

                if any(
                    phrase in title.lower()
                    for phrase in ("table of contents", "page number", "contents")
                ):
                    continue

                # Explicit "Experiment" headings are more reliable.
                confidence = 2 if pattern_index == 0 else 1

                current = titles.get(number)
                if current is None or confidence > current["confidence"]:
                    titles[number] = {
                        "title": title,
                        "page": page["page"],
                        "confidence": confidence,
                    }

                break

    return titles


# ============================================================
# MILANO RETRIEVAL
# ============================================================

def empty_result():
    return {"matches": [], "experiment_number": None, "experiment_title": None}


@st.cache_data(show_spinner=False)
def build_index(pages):
    """Chunk and tokenize the document once; reused for every question."""
    chunks = []
    for page in pages:
        for chunk in split_text(page["text"]):
            words = tokenize(chunk)
            if not words:
                continue

            chunks.append({
                "page": page["page"],
                "text": chunk,
                "words": words,
                "normalized": re.sub(r"\s+", " ", chunk.lower()).strip(),
            })

    document_frequency = Counter()
    for chunk in chunks:
        document_frequency.update(set(chunk["words"]))

    average_length = (
        sum(len(c["words"]) for c in chunks) / len(chunks) if chunks else 1
    )

    return {
        "chunks": chunks,
        "df": document_frequency,
        "avg_len": average_length,
        "titles": extract_experiment_titles(pages),
    }


def retrieve_chunks(question, index, limit=6):
    """
    BM25-inspired lexical retrieval with title expansion, experiment matching,
    phrase boosting, duplicate suppression, and page diversity.

    This is not embedding-based semantic RAG.
    """
    chunks = index["chunks"]
    if not chunks:
        return empty_result()

    title_index = index["titles"]
    experiment_number = get_experiment_number(question)
    target_title = title_index.get(experiment_number, {}).get("title", "")

    original_terms = {
        word for word in tokenize(question)
        if len(word) >= 2 and word not in STOPWORDS
    }
    expanded_terms = {
        word for word in tokenize(target_title)
        if len(word) >= 2 and word not in STOPWORDS
    }

    query_terms = original_terms | expanded_terms

    if not query_terms:
        query_terms = {
            word for word in tokenize(question) if len(word) >= 3
        }

    if not query_terms:
        return empty_result()

    document_frequency = index["df"]
    total_chunks = len(chunks)
    average_length = index["avg_len"]
    normalized_question = re.sub(r"\s+", " ", question.lower()).strip()
    ranked = []

    for chunk in chunks:
        counts = Counter(chunk["words"])
        length = len(chunk["words"])
        score = 0.0

        # BM25-inspired term score.
        for term in query_terms:
            frequency = counts.get(term, 0)
            if not frequency:
                continue

            df = document_frequency[term]
            inverse_frequency = math.log(
                1 + (total_chunks - df + 0.5) / (df + 0.5)
            )

            k1, b = 1.5, 0.75
            denominator = frequency + k1 * (
                1 - b + b * length / max(average_length, 1)
            )
            score += inverse_frequency * (
                frequency * (k1 + 1) / denominator
            )

            # Original query terms matter more than expanded title terms.
            if term in original_terms:
                score += 0.25 * inverse_frequency

        # Exact query phrase boost.
        if len(normalized_question) >= 5 and normalized_question in chunk["normalized"]:
            score += 3.0

        # Experiment identifier boost.
        if experiment_number is not None:
            text = chunk["text"]
            patterns = [
                rf"\bexperiment\s*(?:no\.?|number)?\s*[:#.-]?\s*{experiment_number}\b",
                rf"\bexp\.?\s*(?:no\.?)?\s*[:#.-]?\s*{experiment_number}\b",
            ]
            if any(re.search(p, text, re.IGNORECASE) for p in patterns):
                score += 4.0

            # A passage containing the recovered experiment title is useful.
            if target_title:
                title_terms = {
                    t for t in tokenize(target_title)
                    if len(t) >= 3 and t not in STOPWORDS
                }
                title_overlap = title_terms & set(chunk["words"])
                if title_overlap:
                    score += 2.0 * len(title_overlap) / max(len(title_terms), 1)

        if any(
            marker in chunk["normalized"]
            for marker in ("bibliography", "references", "acknowledgement")
        ):
            score *= 0.4

        if score > 0:
            ranked.append({
                "score": score,
                "page": chunk["page"],
                "text": chunk["text"],
                "normalized": chunk["normalized"],
            })

    ranked.sort(key=lambda item: item["score"], reverse=True)

    # Drop duplicate passages.
    pool, seen = [], set()
    for item in ranked:
        if item["normalized"] in seen:
            continue
        seen.add(item["normalized"])
        pool.append(item)

    # Greedy selection: each time a page is used, its other passages are
    # discounted so evidence comes from several pages when scores are close.
    selected = []
    page_counts = Counter()
    while pool and len(selected) < limit:
        best = max(
            pool,
            key=lambda it: it["score"] / (1 + 0.25 * page_counts[it["page"]]),
        )
        pool.remove(best)
        selected.append({"page": best["page"], "text": best["text"]})
        page_counts[best["page"]] += 1

    title_info = None
    if experiment_number is not None and experiment_number in title_index:
        info = title_index[experiment_number]
        title_info = {"title": info["title"], "page": info["page"]}

    return {
        "matches": selected,
        "experiment_number": experiment_number,
        "experiment_title": title_info,
    }


def full_document_context(pages):
    """Use every page as context (for short PDFs)."""
    result = empty_result()
    result["matches"] = [{"page": p["page"], "text": p["text"]} for p in pages]
    result["mode"] = "full"
    return result


def make_retrieval_query(question, prior):
    """Short follow-ups ('explain more simply') borrow the previous question."""
    if get_experiment_number(question) is None and len(tokenize(question)) <= 6:
        for m in reversed(prior):
            if m["role"] == "user":
                return f"{question} {m['content']}"
    return question


MILANO_SYSTEM = """
You are MILANO, the academic tutor in LINKU.

STRICT SOURCE RULES:
1. Use the supplied excerpts as evidence; do not claim you read other pages.
2. Cite every important document-specific claim with [PDF page N].
3. Only cite page numbers explicitly supplied in the excerpts.
4. Never invent facts, experiment details, results, or citations.
5. If the sources are insufficient, state what is missing.
6. A contents page or title alone is not evidence for a complete procedure.
7. If the question refers to a numbered experiment, verify that the excerpts
   actually relate to it before giving a detailed answer.
8. Distinguish the document's statements from your own explanation.
9. Explain concepts clearly for a student.
10. For experiment questions, use Aim, Principle/Theory, Requirements,
    Procedure, and Result headings only when the sources support them.
11. If only partial information is available, answer the supported part
    and clearly identify what you could not retrieve.
12. Do not claim citations guarantee correctness.
13. The recent conversation is only for understanding follow-up questions;
    it is not evidence for claims about the document.

Provide the most useful answer supported by the evidence.
"""


def build_milano_prompt(question, retrieved, prior):
    excerpts = "\n\n".join(
        f"[PDF page {item['page']}]\n{item['text']}"
        for item in retrieved["matches"]
    )

    title_note = ""
    title_info = retrieved.get("experiment_title")
    if title_info:
        title_note = (
            f"Experiment title candidate found on PDF page "
            f"{title_info['page']}: {title_info['title']}\n"
            "Treat this as a retrieval hint, not proof of the procedure.\n"
        )

    recent = prior[-4:]
    conversation = "\n\n".join(
        ("Student: " if m["role"] == "user" else "MILANO: ") + m["content"][:700]
        for m in recent
    ) or "(none)"

    return f"""
RECENT CONVERSATION:
{conversation}

STUDENT QUESTION:
{question}

RETRIEVAL HINT:
{title_note or "(none)"}

SOURCE EXCERPTS:
{excerpts}
"""


def render_sources(message):
    """Caption + expander of evidence attached to an assistant message."""
    if message.get("mode") == "full":
        st.caption(
            "Answered using the full document. "
            "Check cited pages against the original."
        )
        return

    sources = message.get("sources")
    if not sources:
        return

    st.caption(
        "Based on retrieved PDF passages. "
        "Check cited pages against the original document."
    )
    with st.expander("View retrieved source passages"):
        hint = message.get("hint")
        if hint:
            st.caption(
                f"Experiment lookup hint: {hint['title']} (PDF page {hint['page']})"
            )
        for item in sources:
            st.markdown(f"**PDF page {item['page']}**")
            st.write(item["text"])
            st.divider()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        '<div class="brand">LINKU<span style="color:#C4B5FD">.</span></div>',
        unsafe_allow_html=True,
    )
    st.caption("THE STUDENT ECOSYSTEM")
    st.divider()
    st.markdown("### How it works")
    st.markdown(
        "**✦ MILANO** — upload a course PDF and ask questions. "
        "Answers cite PDF pages.\n\n"
        "**♡ ANAHIRA** — pick a conversation style and chat."
    )
    st.divider()
    if client:
        st.success("AI connected")
    else:
        st.warning("Add GEMINI_API_KEY to your .env file to enable the AI.")
    st.caption(f"Model: {MODEL}")
    st.caption("Learn smarter. Plan better. Grow at your pace.")
    st.caption("LINKU · Working prototype")


# ============================================================
# LANDING PAGE
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">✦ YOUR PERSONAL LEARNING SPACE</div>
        <h1>Learning that feels<br>
        <span style="color:#BDA8FF">more like you.</span></h1>
        <p>
            Meet your academic tutor and personal AI companion.
            A thoughtful digital space designed around the way students
            learn, plan, and navigate college life.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns(2, gap="medium")

with left:
    st.markdown(
        """
        <div class="module-card">
            <div class="pill">01 / ACADEMIC INTELLIGENCE</div>
            <h3>✧ MILANO</h3>
            <p>Bring your syllabus. Ask better questions.
            Learn from the material your course actually uses.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
        <div class="module-card">
            <div class="pill">02 / PERSONALIZED SUPPORT</div>
            <h3>♡ ANAHIRA</h3>
            <p>Find your rhythm with an AI companion that adapts
            its conversation style to what you need.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="section-label">YOUR WORKSPACE</div>',
    unsafe_allow_html=True,
)

milano, anahira = st.tabs([
    "✧  MILANO  /  Study",
    "♡  ANAHIRA  /  Companion",
])


# ============================================================
# MILANO UI
# ============================================================

with milano:
    st.markdown("### Your syllabus, understood.")
    st.write("Upload a course PDF to ground your questions in your own learning material.")

    pdf = st.file_uploader(
        "Drop your study material here",
        type=["pdf"],
        key="milano_pdf",
    )

    pages = []
    index = None
    use_full = False

    if pdf:
        try:
            pages = extract_pdf_cached(pdf.getvalue())
            if pages:
                st.success(f"Ready · Extracted text from {len(pages)} pages")
                index = build_index(pages)

                total_chars = sum(len(p["text"]) for p in pages)
                fits = total_chars <= FULL_DOC_CHAR_LIMIT
                toggle = st.toggle(
                    "Read the whole document for each answer "
                    "(more accurate, a little slower)",
                    value=True,
                    disabled=not fits,
                    key="milano_full_doc",
                )
                use_full = fits and toggle
                if not fits:
                    st.caption(
                        "This PDF is too long to read in full, so MILANO "
                        "will search it for the most relevant passages."
                    )
            else:
                st.warning("No selectable text was found. Scanned PDFs may need OCR.")
        except Exception as exc:
            st.error("LINKU couldn't read this PDF. Check that it is a valid, readable PDF.")
            if DEBUG:
                st.caption(f"Developer detail: {exc}")

    if not client:
        st.warning("MILANO needs a GEMINI_API_KEY to answer. Add it to your .env file and restart.")
    elif not pages:
        st.info("Upload a PDF above to start asking questions.")

    if "milano_history" not in st.session_state:
        st.session_state.milano_history = []

    for message in st.session_state.milano_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                render_sources(message)

    question = st.chat_input(
        "Ask MILANO about your study material...",
        key="milano_question",
        disabled=not pages or not client,
    )

    if question:
        prior = list(st.session_state.milano_history)

        st.session_state.milano_history.append({
            "role": "user",
            "content": question,
        })

        with st.chat_message("user"):
            st.markdown(question)

        if use_full:
            retrieved = full_document_context(pages)
        else:
            retrieved = retrieve_chunks(
                make_retrieval_query(question, prior), index, limit=6
            )

        with st.chat_message("assistant"):
            if not retrieved["matches"]:
                answer = (
                    "I couldn't find a relevant passage in the extracted PDF text. "
                    "Try a specific topic, heading, or term from your material."
                )
                st.markdown(answer)
                st.session_state.milano_history.append({
                    "role": "assistant",
                    "content": answer,
                })
            else:
                try:
                    prompt = build_milano_prompt(question, retrieved, prior)
                    answer = st.write_stream(
                        stream_answer(prompt, system_instruction=MILANO_SYSTEM, temperature=0.2)
                    )
                    if not answer or not answer.strip():
                        raise RuntimeError("The model returned an empty response.")

                    entry = {
                        "role": "assistant",
                        "content": answer,
                        "mode": retrieved.get("mode", "retrieval"),
                        "sources": None if retrieved.get("mode") == "full" else retrieved["matches"],
                        "hint": retrieved.get("experiment_title"),
                    }
                    render_sources(entry)
                    st.session_state.milano_history.append(entry)

                except Exception as exc:
                    # Errors are shown but not saved into the conversation.
                    show_api_error(exc)

    if st.button("Clear MILANO conversation", type="secondary"):
        st.session_state.milano_history = []
        st.rerun()


# ============================================================
# ANAHIRA UI
# ============================================================

SAFETY_RULE = (
    "If the student mentions self-harm, suicide, abuse, or being in immediate "
    "danger, respond with calm care, do not give methods or graphic detail, "
    "and encourage them to reach out right now to a trusted person or a "
    "professional. Mention that in India they can call Tele-MANAS at 14416, "
    "or local emergency services if they are in immediate danger."
)

INSTRUCTIONS = {
    "Patient Tutor": (
        "Teach concepts patiently and step by step. Use simple "
        "explanations and examples. Check understanding without "
        "making the student feel judged."
    ),
    "Study Coach": (
        "Help the student plan studies, break tasks into manageable "
        "steps, prioritize deadlines, and build realistic routines. "
        "Avoid unrealistic promises or demanding schedules."
    ),
    "Supportive Companion": (
        "Listen with empathy, acknowledge feelings, and help the "
        "student reflect. Offer practical suggestions when wanted. "
        "Do not claim to be human or a mental-health professional. "
        "Do not diagnose the student."
    ),
}


def build_anahira_system(persona):
    return f"""
You are ANAHIRA, a student-support AI within LINKU.

CURRENT PERSONA: {persona}

PERSONA INSTRUCTIONS:
{INSTRUCTIONS[persona]}

GUIDELINES:
- Be respectful, warm, helpful, and clear.
- Respond to the latest message in the context of the conversation.
- Do not claim to be human or invent personal experiences.
- Do not invent facts about the student.
- Do not shame, pressure, or belittle the student.
- Give practical steps when the student wants solutions.
- Ask one useful follow-up question when appropriate.
- Do not present yourself as a substitute for professional care.

SAFETY:
{SAFETY_RULE}
"""


with anahira:
    st.markdown("### A space that meets you where you are.")
    st.write("Choose a conversation style that suits what you need today.")

    persona = st.selectbox(
        "Choose your companion",
        list(INSTRUCTIONS.keys()),
        key="anahira_persona",
    )

    st.caption(
        "ANAHIRA is an AI, not a counselor. If you're in crisis, contact local "
        "emergency services or Tele-MANAS (India): 14416."
    )

    if "anahira_histories" not in st.session_state:
        st.session_state.anahira_histories = {name: [] for name in INSTRUCTIONS}

    for name in INSTRUCTIONS:
        st.session_state.anahira_histories.setdefault(name, [])

    history = st.session_state.anahira_histories[persona]

    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    anahira_question = st.chat_input(
        "Share what's on your mind...",
        key="anahira_question",
        disabled=not client,
    )

    if anahira_question:
        history.append({"role": "user", "content": anahira_question})

        with st.chat_message("user"):
            st.markdown(anahira_question)

        with st.chat_message("assistant"):
            try:
                answer = st.write_stream(
                    stream_answer(
                        to_contents(history[-12:]),
                        system_instruction=build_anahira_system(persona),
                        temperature=0.7,
                    )
                )
                if not answer or not answer.strip():
                    raise RuntimeError("The model returned an empty response.")
                history.append({"role": "assistant", "content": answer})
            except Exception as exc:
                show_api_error(exc)

    if st.button("Clear ANAHIRA conversation", type="secondary"):
        st.session_state.anahira_histories[persona] = []
        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center;padding:14px 0 4px">
        <div style="font-family:Manrope,sans-serif;font-weight:800;
        letter-spacing:2px;color:#C4B5FD">LINKU</div>
        <div style="font-size:.8rem;color:#8E87A8;margin-top:6px">
        Built around students, not just subjects.</div>
    </div>
    """,
    unsafe_allow_html=True,
)