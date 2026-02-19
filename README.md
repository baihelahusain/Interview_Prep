# 🎯 InterviewPrep Pro

> An AI-powered company research platform built for job seekers — combining Google Gemini, YouTube, and GitHub into a single, streamlined interview prep workflow.

**Live Demo:** [your-app.streamlit.app](https://your-app.streamlit.app) &nbsp;|&nbsp; **Built with:** Python · Streamlit · Gemini 2.0 Flash · yt-dlp

---

## 📸 Preview

> _(Add a screenshot or screen recording of the app here — this dramatically increases resume/portfolio impact)_

---

## 💡 Project Motivation

Preparing for a tech interview means scattered tabs: company wikis, YouTube vlogs, Glassdoor reviews, GitHub repos, and LeetCode filters. InterviewPrep Pro consolidates all of that into one AI-driven interface so candidates can focus on preparation rather than research logistics.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🤖 AI Company Overview | Gemini 2.0 Flash generates a role-specific profile — leadership, products, culture, growth paths |
| ▶️ Curated Video Feed | Aggregates YouTube content across 5 topic categories + role-specific videos |
| 🐙 GitHub Resource Discovery | Surfaces starred interview prep repos filtered by company and job role |
| 🎨 Dark-mode UI | Custom Streamlit theme with a professional design system (Syne + DM Sans) |
| ⚡ Role-specific results | All three data sources dynamically adjust when a job role is provided |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit + Custom CSS Design System |
| AI / LLM | Google Gemini 2.0 Flash (`google-genai`) |
| Video Aggregation | `yt-dlp` (YouTube search without API quota limits) |
| Repository Search | GitHub REST API v3 |
| Configuration | YAML + environment variable injection |
| Language | Python 3.9+ |

---

## 🏗️ Architecture

```
User Input (Company + Role)
        │
        ├──► Gemini 2.0 Flash ──► Company Overview
        │
        ├──► yt-dlp ──────────► YouTube Videos (5 topic categories)
        │
        └──► GitHub REST API ──► Interview Prep Repositories
                    │
                    └── Fallback: Curated static resource map
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- A [Google AI Studio](https://aistudio.google.com/app/apikey) account (free tier works)

### Installation

```bash
git clone https://github.com/your-username/interviewprep-pro.git
cd interviewprep-pro

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

Copy the example config — **never commit `config.yaml` with real keys**:

```bash
cp config.example.yaml config.yaml
```

Fill in your credentials:

```yaml
apis:
  google:
    api_key: "YOUR_GEMINI_API_KEY"
  youtube:
    api_key: "YOUR_YOUTUBE_API_KEY"
```

### Run

```bash
streamlit run main.py
```

Open [http://localhost:8501](http://localhost:8501).

### Deploy On Streamlit Community Cloud

1. Push this repository to GitHub.
2. Go to Streamlit Community Cloud and create a new app from your repo.
3. Set `main.py` as the entrypoint.
4. In app settings, open **Secrets** and paste:

```toml
[apis.google]
api_key = "YOUR_GEMINI_API_KEY"

[sources]
github_api_url = "https://api.github.com"

[app]
title = "InterviewPrep Pro"
```

5. Save and redeploy.

---

## 🔒 Security & YAML Best Practices

**Never commit API keys.** Here is a layered approach:

### 1. `.gitignore` — First line of defence

```gitignore
config.yaml
.env
*.pem
```

Commit only `config.example.yaml` with placeholder values.

### 2. Environment Variables — Preferred for production

```python
import os
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
```

Set in your shell or a `.env` file (also gitignored).

### 3. Streamlit Secrets — For cloud deployment

```toml
# .streamlit/secrets.toml  (gitignored)
[apis.google]
api_key = "your-gemini-key-here"
```

Access in code:

```python
GEMINI_API_KEY = st.secrets["apis"]["google"]["api_key"]
```

### 4. Rotate Immediately if Exposed

If a key is ever committed or shared, revoke it from your provider dashboard right away and generate a new one.

---

## 📁 Project Structure

```
interviewprep-pro/
├── main.py                  # Streamlit app — UI + all logic
├── config.yaml              # Local secrets (gitignored)
├── config.example.yaml      # Safe placeholder config (committed)
├── requirements.txt         # Python dependencies
├── .gitignore
└── README.md
```

---

## 🗺️ Roadmap

- [ ] Interview flashcard mode (AI-generated Q&A per company + role)
- [ ] PDF export of full research report
- [ ] Resume keyword gap analysis vs. job description
- [ ] Glassdoor / Levels.fyi salary data integration
- [ ] Authenticated sessions with saved research history

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [Tech Interview Handbook](https://github.com/yangshun/tech-interview-handbook) — Yangshun Tay
- [System Design Primer](https://github.com/donnemartin/system-design-primer) — Donne Martin
- [Coding Interview University](https://github.com/jwasham/coding-interview-university) — John Washam
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — Open-source YouTube extraction
- [Google Gemini](https://ai.google.dev/) — AI content generation

---

<p align="center">Built with ☕ and a lot of mock interviews</p>
