# LINKU — Student AI Ecosystem

**A syllabus-grounded learning assistant and personalized AI companion for students.**

[🚀 **Live Demo — Try LINKU**](https://linku-student-ai.streamlit.app/)

# LINKU — Student AI Ecosystem

**Status: In Progress** 🚧

LINKU is a student-focused AI ecosystem designed to support academic learning, PDF-based study workflows, and personalized conversational assistance.

## Features

### 📚 MILANO — Syllabus-Grounded Study Assistant
- Upload academic PDFs and retrieve relevant passages.
- Ask questions based on uploaded study material.
- Generate answers grounded in retrieved content.
- Display source-page references to help students verify answers.
- Uses lexical, BM25-inspired ranking to identify relevant text passages.

### 💜 ANAHIRA — Personalized AI Companion
- Interact with a conversational AI assistant.
- Choose between three personas:
  - **Patient Tutor** — explains concepts in a supportive way.
  - **Study Coach** — encourages planning and productive study habits.
  - **Supportive Companion** — offers empathetic conversation.
- Maintains separate conversation histories for each persona during the session.

## Technology Stack

- **Language:** Python
- **Interface:** Streamlit
- **AI:** Google Gemini API
- **PDF Processing:** pypdf
- **Environment Configuration:** python-dotenv

## How It Works

1. Students upload a PDF to MILANO.
2. LINKU extracts text and divides it into manageable chunks.
3. A lexical retrieval algorithm ranks passages according to their relevance to the question.
4. Relevant passages are supplied to Gemini to generate a grounded response with page references.
5. Students can switch to ANAHIRA for persona-guided conversations.

> **Technical note:** MILANO currently uses lexical, BM25-inspired retrieval rather than embedding-based vector search. ANAHIRA uses persona-guided prompting with a single Gemini model rather than a coordinated multi-agent architecture.

## Getting Started

### Prerequisites

- Python 3.10 or a compatible version
- A Google Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/milan9894/LINKU.git
cd LINKU
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

Replace the placeholder with your own Gemini API key.

**Security:** Never commit your `.env` file or expose your API key publicly.

### 5. Run LINKU locally

```bash
python -m streamlit run app.py
```

Open the local URL displayed in your terminal.

## Deployment

LINKU is deployed using [Streamlit Community Cloud](https://share.streamlit.io/).

**Live application:** https://linku-student-ai.streamlit.app/

For cloud deployment, configure `GEMINI_API_KEY` through the app's Streamlit Secrets settings rather than uploading your local `.env` file.

## Future Improvements

- Embedding-based semantic retrieval and vector search.
- Improved retrieval evaluation and source-grounding tests.
- More robust handling of long and complex academic documents.
- Expanded student workflows and learning features.
- Further development of multi-agent orchestration.

## Author

**Milan**

GitHub: [@milan9894](https://github.com/milan9894)

---

*LINKU — Learn, understand, and grow with AI.*
