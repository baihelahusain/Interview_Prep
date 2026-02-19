import streamlit as st
import yaml
import requests
import time
import os
import html
from urllib.parse import urlparse, parse_qs

# Import Google's Gen AI library for Gemini models
from google import genai
import yt_dlp

def _nested_get(data, keys, default=None):
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def load_settings():
    """Load settings from env vars, Streamlit secrets, or local config.yaml (in that order)."""
    local_config = {}
    for path in ["config/config.yaml", "config.yaml"]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                local_config = yaml.safe_load(f) or {}
            break

    secrets = {}
    try:
        if hasattr(st.secrets, "to_dict"):
            secrets = st.secrets.to_dict()
        else:
            secrets = dict(st.secrets)
    except Exception:
        secrets = {}

    gemini_api_key = (
        os.getenv("GEMINI_API_KEY")
        or _nested_get(secrets, ["apis", "google", "api_key"])
        or secrets.get("GEMINI_API_KEY")
        or _nested_get(local_config, ["apis", "google", "api_key"])
    )

    youtube_api_key = (
        os.getenv("YOUTUBE_API_KEY")
        or _nested_get(secrets, ["apis", "youtube", "api_key"])
        or secrets.get("YOUTUBE_API_KEY")
        or _nested_get(local_config, ["apis", "youtube", "api_key"])
        or ""
    )

    github_api_url = (
        os.getenv("GITHUB_API_URL")
        or _nested_get(secrets, ["sources", "github_api_url"])
        or secrets.get("GITHUB_API_URL")
        or _nested_get(local_config, ["sources", "github_api_url"])
        or "https://api.github.com"
    )

    app_title = (
        os.getenv("APP_TITLE")
        or _nested_get(secrets, ["app", "title"])
        or secrets.get("APP_TITLE")
        or _nested_get(local_config, ["app", "title"])
        or "InterviewPrep Pro"
    )

    if not gemini_api_key:
        st.error(
            "Missing Gemini API key. Set `GEMINI_API_KEY` in environment variables, "
            "or add it in Streamlit secrets."
        )
        st.stop()

    return gemini_api_key, youtube_api_key, github_api_url, app_title


GEMINI_API_KEY, YOUTUBE_API_KEY, GITHUB_API_URL, APP_TITLE = load_settings()

# Configure the Gemini API client
genai_client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options={"base_url": "https://generativelanguage.googleapis.com"}
)

st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    page_icon="🎯",
    initial_sidebar_state="expanded"
)

# ─── Professional Design System ───────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

  /* ── Reset & Base ── */
  html, body, [class*="css"] {
      font-family: 'DM Sans', sans-serif;
      color: #e8e4dc;
  }

  /* ── App Background ── */
  .stApp {
      background: #0d0d0f;
      background-image:
          radial-gradient(ellipse 80% 50% at 20% -10%, rgba(255,140,50,0.08) 0%, transparent 60%),
          radial-gradient(ellipse 60% 40% at 85% 10%, rgba(255,200,80,0.05) 0%, transparent 50%);
  }

  /* ── Hide Streamlit chrome ── */
  #MainMenu, footer { visibility: hidden; }
  header { visibility: visible; }
  [data-testid="stHeader"] { background: transparent; }
  .block-container { padding-top: 2rem !important; max-width: 1200px; }

  /* ── Hero Header ── */
  .hero-header {
      text-align: center;
      padding: 3.5rem 2rem 2rem;
      position: relative;
  }
  .hero-eyebrow {
      font-family: 'DM Sans', sans-serif;
      font-size: 0.72rem;
      font-weight: 500;
      letter-spacing: 0.25em;
      text-transform: uppercase;
      color: #f59e0b;
      margin-bottom: 1rem;
      display: block;
  }
  .hero-title {
      font-family: 'Syne', sans-serif;
      font-size: clamp(2.6rem, 5vw, 4rem);
      font-weight: 800;
      line-height: 1.05;
      margin: 0 0 1rem;
      background: linear-gradient(135deg, #fde68a 0%, #f59e0b 40%, #fbbf24 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
  }
  .hero-subtitle {
      font-size: 1.05rem;
      font-weight: 300;
      color: #9ca3af;
      max-width: 520px;
      margin: 0 auto 2rem;
      line-height: 1.6;
  }
  .hero-divider {
      width: 60px;
      height: 2px;
      background: linear-gradient(90deg, #f59e0b, transparent);
      margin: 0 auto;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
      background: #111115 !important;
      border-right: 1px solid rgba(255,255,255,0.06) !important;
  }
  [data-testid="stSidebar"] .block-container { padding-top: 2rem; }

  .sidebar-brand {
      font-family: 'Syne', sans-serif;
      font-size: 1.1rem;
      font-weight: 700;
      color: #f59e0b;
      letter-spacing: 0.04em;
      padding: 0 0 1.5rem;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      margin-bottom: 1.5rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
  }
  .sidebar-label {
      font-size: 0.7rem;
      font-weight: 500;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: #6b7280;
      margin-bottom: 0.4rem;
      display: block;
  }

  /* ── Input fields ── */
  .stTextInput > div > div > input {
      background: #1a1a1f !important;
      border: 1px solid rgba(255,255,255,0.1) !important;
      border-radius: 8px !important;
      color: #e8e4dc !important;
      font-family: 'DM Sans', sans-serif !important;
      font-size: 0.9rem !important;
      padding: 0.6rem 0.9rem !important;
      transition: border-color 0.2s;
  }
  .stTextInput > div > div > input:focus {
      border-color: #f59e0b !important;
      box-shadow: 0 0 0 2px rgba(245,158,11,0.15) !important;
  }
  .stTextInput > div > div > input::placeholder { color: #4b5563 !important; }

  /* ── Research Button ── */
  .stButton > button {
      width: 100%;
      background: linear-gradient(135deg, #f59e0b, #d97706) !important;
      color: #0d0d0f !important;
      font-family: 'Syne', sans-serif !important;
      font-weight: 700 !important;
      font-size: 0.85rem !important;
      letter-spacing: 0.06em !important;
      text-transform: uppercase !important;
      border: none !important;
      border-radius: 8px !important;
      padding: 0.7rem 1.5rem !important;
      cursor: pointer !important;
      margin-top: 1rem !important;
      transition: opacity 0.2s, transform 0.15s !important;
  }
  .stButton > button:hover {
      opacity: 0.9 !important;
      transform: translateY(-1px) !important;
  }

  /* ── Section Headers ── */
  .section-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin: 2.5rem 0 1.2rem;
      padding-bottom: 0.75rem;
      border-bottom: 1px solid rgba(255,255,255,0.07);
  }
  .section-icon {
      width: 36px; height: 36px;
      background: rgba(245,158,11,0.1);
      border: 1px solid rgba(245,158,11,0.25);
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 1rem;
      flex-shrink: 0;
  }
  .section-title {
      font-family: 'Syne', sans-serif;
      font-size: 1.25rem;
      font-weight: 700;
      color: #fde68a;
      margin: 0;
  }
  .section-badge {
      margin-left: auto;
      font-size: 0.68rem;
      font-weight: 500;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #f59e0b;
      background: rgba(245,158,11,0.08);
      border: 1px solid rgba(245,158,11,0.2);
      border-radius: 20px;
      padding: 0.2rem 0.7rem;
  }

  /* ── Company Overview Card ── */
  .overview-card {
      background: #111115;
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 14px;
      padding: 2rem;
      line-height: 1.75;
      font-size: 0.93rem;
      color: #c9c5bd;
      position: relative;
      overflow: hidden;
  }
  .overview-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 2px;
      background: linear-gradient(90deg, #f59e0b, #fde68a, transparent);
  }

  /* ── Video Cards ── */
  .video-topic-label {
      font-family: 'Syne', sans-serif;
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: #f59e0b;
      margin: 1.8rem 0 0.8rem;
  }
  .video-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
      margin-bottom: 0.5rem;
  }
  .video-card {
      background: #111115;
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 12px;
      overflow: hidden;
      transition: border-color 0.2s, transform 0.2s;
      text-decoration: none;
      display: block;
  }
  .video-card:hover {
      border-color: rgba(245,158,11,0.35);
      transform: translateY(-2px);
  }
  .video-thumb {
      width: 100%;
      aspect-ratio: 16/9;
      object-fit: cover;
      display: block;
  }
  .video-card-body {
      padding: 0.75rem 0.9rem 0.9rem;
  }
  .video-card-title {
      font-size: 0.82rem;
      font-weight: 500;
      color: #e8e4dc;
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      margin: 0;
  }
  .video-play-tag {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      margin-top: 0.5rem;
      font-size: 0.7rem;
      color: #f59e0b;
      font-weight: 500;
  }

  /* ── Resource Links ── */
  .resource-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 0.75rem;
  }
  .resource-card {
      background: #111115;
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 10px;
      padding: 0.9rem 1rem;
      display: flex;
      align-items: center;
      gap: 0.75rem;
      text-decoration: none;
      transition: border-color 0.2s, background 0.2s;
  }
  .resource-card:hover {
      border-color: rgba(245,158,11,0.3);
      background: #16161b;
  }
  .resource-icon {
      font-size: 1.1rem;
      flex-shrink: 0;
  }
  .resource-name {
      font-size: 0.83rem;
      font-weight: 500;
      color: #d1cdc5;
      line-height: 1.3;
  }
  .resource-arrow {
      margin-left: auto;
      color: #4b5563;
      font-size: 0.8rem;
      flex-shrink: 0;
  }

  /* ── Info / Warning boxes ── */
  .custom-info {
      background: rgba(245,158,11,0.06);
      border: 1px solid rgba(245,158,11,0.18);
      border-radius: 8px;
      padding: 0.75rem 1rem;
      font-size: 0.82rem;
      color: #9ca3af;
      margin-top: 0.75rem;
  }
  .custom-warn {
      background: rgba(239,68,68,0.06);
      border: 1px solid rgba(239,68,68,0.18);
      border-radius: 8px;
      padding: 0.75rem 1rem;
      font-size: 0.82rem;
      color: #9ca3af;
      margin-top: 0.75rem;
  }

  /* ── Recommended Table ── */
  .rec-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
  .rec-table th {
      font-size: 0.7rem; letter-spacing: 0.12em; text-transform: uppercase;
      color: #6b7280; font-weight: 500; text-align: left;
      padding: 0.5rem 0.75rem;
      border-bottom: 1px solid rgba(255,255,255,0.06);
  }
  .rec-table td {
      padding: 0.65rem 0.75rem;
      font-size: 0.85rem;
      border-bottom: 1px solid rgba(255,255,255,0.04);
      color: #c9c5bd;
  }
  .rec-table a { color: #fbbf24; text-decoration: none; }
  .rec-table a:hover { text-decoration: underline; }
  .rec-table tr:last-child td { border-bottom: none; }

  /* ── Streamlit element overrides ── */
  h1, h2, h3 { font-family: 'Syne', sans-serif !important; color: #fde68a !important; }
  .stSubheader { font-family: 'Syne', sans-serif !important; }
  p, li { color: #c9c5bd; }
  hr { border-color: rgba(255,255,255,0.06) !important; }
  [data-testid="stSpinner"] > div { color: #f59e0b !important; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0d0d0f; }
  ::-webkit-scrollbar-thumb { background: #2d2d35; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ─── Hero Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <span class="hero-eyebrow">AI-Powered Interview Intelligence</span>
    <h1 class="hero-title">InterviewPrep Pro</h1>
    <p class="hero-subtitle">Deep company research, curated resources, and role-specific insights — everything you need to walk in confident.</p>
    <div class="hero-divider"></div>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">🎯 InterviewPrep Pro</div>', unsafe_allow_html=True)
    st.markdown('<span class="sidebar-label">Target Company</span>', unsafe_allow_html=True)
    company_name = st.text_input("Company Name", placeholder="e.g. Google, Amazon, Stripe", label_visibility="collapsed")
    st.markdown('<span class="sidebar-label" style="margin-top:1rem;display:block">Job Role (optional)</span>', unsafe_allow_html=True)
    job_role = st.text_input("Job Role", placeholder="e.g. Software Engineer", label_visibility="collapsed")
    research_button = st.button("🔍  Research Now")
    st.markdown("""
    <div style="margin-top:2rem;padding-top:1.5rem;border-top:1px solid rgba(255,255,255,0.06)">
        <p style="font-size:0.72rem;color:#4b5563;line-height:1.6;margin:0">
            Powered by <span style="color:#f59e0b">Gemini 2.0 Flash</span> · YouTube · GitHub
        </p>
    </div>
    """, unsafe_allow_html=True)

###############################################################################
# Section 1: Company Overview using Gemini model
###############################################################################
def generate_company_overview(company, role):
    # First prompt to validate if the company exists and is well-known
    validation_prompt = f"Does the company '{company}' exist as a known business entity? Respond with 'yes' or 'no'."
    
    try:
        # Validate if company exists
        validation_response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=validation_prompt
        )
        company_exists = "yes" in (validation_response.text or "").lower()
        
        # If company doesn't seem to exist or is very obscure, provide appropriate message
        if not company_exists:
            return f"Sorry, I couldn't find reliable information about '{company}'. Please verify the company name or try a different company."
        
        # Build the prompt for company overview
        prompt = (
            f"Generate a detailed overview for the company '{company}'. Include details such as its foundation, "
            "CEO, services, and the countries where its products or services are available. "
            "If you're not confident about specific information, DO NOT include guesses or placeholders. "
            "Only include verified facts about the company. If you can't find enough information about this company, "
            "state clearly what information is available and what isn't."
        )
        
        if role:
            prompt += (
                f"\n\nAlso, include specific information about '{role}' positions at {company}, such as: "
                f"1. Typical job responsibilities for {role} at {company}, "
                f"2. Required skills and qualifications for this role, "
                f"3. Career growth opportunities for {role} positions, "
                f"4. Any specific technologies or tools used by {role}s at {company}."
                f"\n\nIf you don't have specific information about this role at {company}, clearly state that."
            )
            
        # Generate the company overview
        response = genai_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        overview = response.text or "No response generated."
        
        # Check if the response contains uncertainty indicators
        uncertainty_phrases = ["I don't have", "I cannot", "I'm not able", "insufficient information"]
        if any(phrase in overview.lower() for phrase in uncertainty_phrases):
            # Content indicates uncertainty - wrap it appropriately
            return f"Based on available information about '{company}':\n\n{overview}"
        
        return overview
        
    except Exception as e:
        return f"Sorry, I couldn't generate information about '{company}' at this time. Error: {e}"

###############################################################################
# Section 2: YouTube Videos Aggregation
###############################################################################
def get_video_id(youtube_url):
    """Extract video ID from YouTube URL"""
    parsed_url = urlparse(youtube_url)
    if parsed_url.hostname in ('youtu.be',):
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
        if parsed_url.path.startswith('/embed/'):
            return parsed_url.path.split('/')[2]
        if parsed_url.path.startswith('/v/'):
            return parsed_url.path.split('/')[2]
    return None

def search_youtube_videos(company, topic, max_results=3):
    """
    Scrape YouTube search results using yt_dlp.
    Returns up to max_results number of videos (default: 3).
    """
    query = f"{company} {topic}"
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'extract_flat': True,
        'default_search': 'ytsearch',
        'max_downloads': max_results
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            
        videos = []
        if 'entries' in search_results:
            for entry in search_results['entries']:
                # Only add videos with title and ID
                if entry.get('title') and entry.get('id'):
                    video_id = entry['id']
                    videos.append({
                        "title": entry['title'],
                        "video_url": f"https://www.youtube.com/watch?v={video_id}",
                        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                    })
        
        return videos
    except Exception as e:
        st.error(f"Error searching YouTube videos: {str(e)}")
        return []

def display_video_with_thumbnail(video):
    """Display a video card with thumbnail rendered inline via HTML."""
    safe_title = html.escape(video.get("title", ""), quote=True)
    safe_video_url = html.escape(video.get("video_url", ""), quote=True)
    safe_thumbnail_url = html.escape(video.get("thumbnail_url", ""), quote=True)
    return (
        f'<a class="video-card" href="{safe_video_url}" target="_blank">'
        f'<img class="video-thumb" src="{safe_thumbnail_url}" alt="{safe_title}" loading="lazy">'
        '<div class="video-card-body">'
        f'<p class="video-card-title">{safe_title}</p>'
        '<span class="video-play-tag">Watch on YouTube</span>'
        '</div>'
        '</a>'
    )

###############################################################################
# Section 3: GitHub Resources
###############################################################################
def is_english(text):
    """
    Returns True if the given text appears to be in English (simple ASCII check).
    """
    try:
        text.encode("ascii")
    except UnicodeEncodeError:
        return False
    return True

def get_github_resources(company, job_role=None, max_results=8):
    """
    Fetch GitHub repositories focused on interview preparation and job materials 
    specifically relevant to the given company and job role.
    """
    # Create multiple targeted queries to improve results
    company_lower = company.lower()
    
    # Base queries focused on interview preparation
    queries = [
        f'"{company}" interview questions',
        f'{company} "technical interview"',
        f'{company} "coding interview"',
        f'{company} "interview preparation"',
        f'{company} "interview experience"'
    ]
    
    # Add job role specific queries if provided
    if job_role and job_role.strip():
        job_role = job_role.strip().lower()
        role_queries = [
            f'"{company}" {job_role} interview',
            f'{company} {job_role} "interview questions"',
            f'{company} {job_role} "technical interview"',
            f'{job_role} "interview preparation" {company}'
        ]
        # Add role-specific queries to the beginning for higher priority
        queries = role_queries + queries
    
    all_results = []
    
    # Try each query to collect a variety of resources
    for query in queries:
        search_url = f"{GITHUB_API_URL}/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }
        
        try:
            response = requests.get(search_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                all_results.extend(data.get("items", []))
                # Short delay to avoid rate limiting
                time.sleep(0.2)
        except Exception:
            continue
    
    # If we couldn't get results with any query, return empty list
    if not all_results:
        return []
    
    # Keywords that strongly indicate a resource is specifically for interview preparation
    interview_keywords = [
        'interview question', 'hiring process', 'coding challenge', 
        'assessment', 'interview experience', 'interview prep',
        'technical interview', 'onsite interview', 'online assessment',
        'leetcode', 'interview problem'
    ]
    
    # Add job role specific keywords if provided
    if job_role and job_role.strip():
        job_role = job_role.strip().lower()
        role_keywords = [job_role, job_role.replace(' ', '')]
        interview_keywords.extend(role_keywords)
    
    # Process and deduplicate results
    seen_urls = set()
    company_resources = []
    
    for repo in all_results:
        # Skip if we've already seen this repo
        repo_url = repo.get("html_url")
        if not repo_url or repo_url in seen_urls:
            continue
        
        name = repo.get("name", "").lower()
        description = (repo.get("description") or "").lower()
        content = f"{name} {description}"
        
        # Check for company name in content to ensure relevance
        if company_lower not in content:
            continue
        
        # Prioritize repositories that match job role if provided
        is_role_specific = False
        if job_role and job_role.strip():
            is_role_specific = any(role_term in content for role_term in job_role.lower().split())
        
        # Only add to results if it's highly relevant for interview preparation
        if any(keyword in content for keyword in interview_keywords):
            resource = {
                "name": repo["full_name"],
                "url": repo_url,
                "role_specific": is_role_specific
            }
            company_resources.append(resource)
            seen_urls.add(repo_url)
            
        # Stop once we have enough results
        if len(company_resources) >= max_results * 2:  # Get more than needed so we can prioritize
            break
    
    # Prioritize role-specific resources if job role was provided
    if job_role and job_role.strip():
        # Sort putting role-specific resources first
        company_resources.sort(key=lambda x: not x.get("role_specific", False))
    
    # Remove the role_specific field before returning
    for resource in company_resources:
        if "role_specific" in resource:
            del resource["role_specific"]
    
    # If we found some resources, return them
    if company_resources:
        return company_resources[:max_results]
    
    # If we couldn't find good matches, return empty list
    return []

def get_improved_fallback_resources(company, job_role=None):
    """
    Provides curated fallback resources for popular companies when specific company resources aren't found.
    Only returns resources for specifically mapped companies, otherwise returns empty list.
    If job_role is specified, it will try to return role-specific resources for that company.
    """
    # Map popular companies to their interview preparation resources
    company_resources = {
        "amazon": [
            {"name": "Amazon Interview Guide", "url": "https://github.com/jwasham/coding-interview-university"},
            {"name": "Amazon Assessment Questions", "url": "https://github.com/twowaits/SDE-Interview-Questions/tree/master/Amazon"},
            {"name": "Amazon Interview Questions", "url": "https://github.com/krishnadey30/LeetCode-Questions-CompanyWise/blob/master/amazon_alltime.txt"}
        ],
        "google": [
            {"name": "Google Interview Questions", "url": "https://github.com/mgechev/google-interview-preparation-problems"},
            {"name": "Google Tech Dev Guide", "url": "https://github.com/jayshah19949596/CodingInterviews"},
            {"name": "Google Interview Resources", "url": "https://github.com/krishnadey30/LeetCode-Questions-CompanyWise/blob/master/google_alltime.txt"}
        ],
        "facebook": [
            {"name": "Meta/Facebook Interview Questions", "url": "https://github.com/twowaits/SDE-Interview-Questions/tree/master/Facebook"},
            {"name": "Meta Technical Interview Guide", "url": "https://github.com/khanhnamle1994/cracking-the-data-science-interview"},
            {"name": "Facebook Interview Resources", "url": "https://github.com/krishnadey30/LeetCode-Questions-CompanyWise/blob/master/facebook_alltime.txt"}
        ],
        "meta": [
            {"name": "Meta/Facebook Interview Questions", "url": "https://github.com/twowaits/SDE-Interview-Questions/tree/master/Facebook"},
            {"name": "Meta Technical Interview Guide", "url": "https://github.com/khanhnamle1994/cracking-the-data-science-interview"},
            {"name": "Facebook Interview Resources", "url": "https://github.com/krishnadey30/LeetCode-Questions-CompanyWise/blob/master/facebook_alltime.txt"}
        ],
        "microsoft": [
            {"name": "Microsoft Interview Questions", "url": "https://github.com/twowaits/SDE-Interview-Questions/tree/master/Microsoft"},
            {"name": "Microsoft Interview Preparation", "url": "https://github.com/Olshansk/interview"},
            {"name": "Microsoft Interview Resources", "url": "https://github.com/krishnadey30/LeetCode-Questions-CompanyWise/blob/master/microsoft_alltime.txt"}
        ],
        "apple": [
            {"name": "Apple Interview Preparation", "url": "https://github.com/hxu296/leetcode-company-wise-problems-2022"},
            {"name": "Apple Interview Questions", "url": "https://github.com/krishnadey30/LeetCode-Questions-CompanyWise/blob/master/apple_alltime.txt"},
            {"name": "Apple Technical Interview", "url": "https://github.com/checkcheckzz/system-design-interview"}
        ],
        "netflix": [
            {"name": "Netflix Interview Questions", "url": "https://github.com/twowaits/SDE-Interview-Questions"},
            {"name": "Netflix Technical Interview", "url": "https://github.com/yangshun/tech-interview-handbook"}
        ],
        "tesla": [
            {"name": "Tesla Interview Prep", "url": "https://github.com/krishnadey30/LeetCode-Questions-CompanyWise"},
            {"name": "Tesla Technical Questions", "url": "https://github.com/h5bp/Front-end-Developer-Interview-Questions"}
        ]
    }
    
    # Role-specific resources for common job roles
    role_resources = {
        "software engineer": [
            {"name": "Software Engineering Interview Preparation", "url": "https://github.com/jwasham/coding-interview-university"},
            {"name": "Software Engineer Coding Questions", "url": "https://github.com/twowaits/SDE-Interview-Questions"}
        ],
        "frontend": [
            {"name": "Frontend Interview Questions", "url": "https://github.com/h5bp/Front-end-Developer-Interview-Questions"},
            {"name": "Frontend Interview Handbook", "url": "https://github.com/yangshun/front-end-interview-handbook"}
        ],
        "backend": [
            {"name": "Backend Interview Questions", "url": "https://github.com/arialdomartini/Back-End-Developer-Interview-Questions"},
            {"name": "System Design for Backend Engineers", "url": "https://github.com/donnemartin/system-design-primer"}
        ],
        "data scientist": [
            {"name": "Data Science Interview Resources", "url": "https://github.com/khanhnamle1994/cracking-the-data-science-interview"},
            {"name": "Data Science Interview Questions", "url": "https://github.com/alexeygrigorev/data-science-interviews"}
        ],
        "machine learning": [
            {"name": "Machine Learning Interviews", "url": "https://github.com/chiphuyen/machine-learning-systems-design"},
            {"name": "ML Interview Guide", "url": "https://github.com/khangich/machine-learning-interview"}
        ],
        "devops": [
            {"name": "DevOps Interview Questions", "url": "https://github.com/bregman-arie/devops-exercises"},
            {"name": "DevOps Resource Collection", "url": "https://github.com/MichaelCade/90DaysOfDevOps"}
        ]
    }
    
    # Check if we have resources for this specific company
    company_lower = company.lower()
    company_specific = []
    
    for key in company_resources:
        if key in company_lower or company_lower in key:
            company_specific = company_resources[key]
            break
    
    # If job role is provided, try to find role-specific resources
    if job_role and company_specific:
        job_role_lower = job_role.lower()
        
        # Check if the job role matches any of our predefined roles
        role_specific = []
        for role_key in role_resources:
            if role_key in job_role_lower or any(term in job_role_lower for term in role_key.split()):
                role_specific = role_resources[role_key]
                break
        
        # If we found role-specific resources, combine them with company resources
        if role_specific:
            # Create a combined list with role-specific resources first
            return role_specific + company_specific
    
    # Return company-specific resources or empty list
    return company_specific

# Function to display recommended interview and career resources
def display_recommended_resources():
    st.markdown("""
    <div class="section-header">
        <div class="section-icon">📚</div>
        <span class="section-title">General Interview Resources</span>
        <span class="section-badge">Community Favourites</span>
    </div>
    <div class="overview-card" style="padding:0.5rem 0">
        <table class="rec-table">
            <thead><tr><th>Repository</th><th>Description</th></tr></thead>
            <tbody>
                <tr><td><a href="https://github.com/yangshun/tech-interview-handbook" target="_blank">Tech Interview Handbook</a></td><td>Curated coding interview preparation materials</td></tr>
                <tr><td><a href="https://github.com/donnemartin/system-design-primer" target="_blank">System Design Primer</a></td><td>Learn how to design large-scale systems</td></tr>
                <tr><td><a href="https://github.com/jwasham/coding-interview-university" target="_blank">Coding Interview University</a></td><td>A complete computer science study plan</td></tr>
                <tr><td><a href="https://github.com/h5bp/Front-end-Developer-Interview-Questions" target="_blank">Front-end Interview Questions</a></td><td>Questions for front-end developer interviews</td></tr>
                <tr><td><a href="https://github.com/arialdomartini/Back-End-Developer-Interview-Questions" target="_blank">Back-end Interview Questions</a></td><td>Questions for back-end developer interviews</td></tr>
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

###############################################################################
# Main: Execute sections when Research button is clicked
###############################################################################
if research_button:
    if not company_name:
        st.markdown('<div class="custom-warn">⚠️ Please enter a company name to begin your research.</div>', unsafe_allow_html=True)
    else:
        # ── Section 1: Company Overview ──────────────────────────────────────
        st.markdown(f"""
        <div class="section-header">
            <div class="section-icon">🏢</div>
            <span class="section-title">Company Overview</span>
            <span class="section-badge">AI Generated</span>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("Researching company profile..."):
            overview = generate_company_overview(company_name, job_role)

        st.markdown(f'<div class="overview-card">{overview}</div>', unsafe_allow_html=True)

        # ── Section 2: YouTube Videos ────────────────────────────────────────
        st.markdown(f"""
        <div class="section-header" style="margin-top:3rem">
            <div class="section-icon">▶️</div>
            <span class="section-title">Video Resources</span>
            <span class="section-badge">YouTube</span>
        </div>
        """, unsafe_allow_html=True)

        topics = [
            ("company overview", "Company Overview"),
            ("roadmap to get a job", "How to Get Hired"),
            ("interview preparation", "Interview Preparation"),
            ("employee experience", "Employee Experience"),
            ("interview questions", "Interview Questions"),
        ]

        for topic_key, topic_label in topics:
            st.markdown(f'<p class="video-topic-label">— {topic_label}</p>', unsafe_allow_html=True)
            videos = search_youtube_videos(company_name, topic_key)
            if videos:
                cards_html = '<div class="video-grid">' + "".join(display_video_with_thumbnail(v) for v in videos) + '</div>'
                st.markdown(cards_html, unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="custom-warn">No videos found for "{topic_label}".</div>', unsafe_allow_html=True)

        # Role-specific videos
        if job_role:
            st.markdown(f'<p class="video-topic-label">— {job_role.title()} at {company_name}</p>', unsafe_allow_html=True)
            job_videos = search_youtube_videos(f"{company_name} {job_role} position", "interview experience", 3)
            relevant_job_videos = []
            job_role_terms = job_role.lower().split()
            if job_videos:
                for video in job_videos:
                    video_title = video["title"].lower()
                    if company_name.lower() in video_title and any(term in video_title for term in job_role_terms):
                        relevant_job_videos.append(video)

            if relevant_job_videos:
                cards_html = '<div class="video-grid">' + "".join(display_video_with_thumbnail(v) for v in relevant_job_videos) + '</div>'
                st.markdown(cards_html, unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="custom-warn">No role-specific videos found for {job_role} at {company_name}.</div>', unsafe_allow_html=True)

        # ── Section 3: GitHub Resources ──────────────────────────────────────
        st.markdown(f"""
        <div class="section-header" style="margin-top:3rem">
            <div class="section-icon">🐙</div>
            <span class="section-title">{company_name} Interview Resources</span>
            <span class="section-badge">GitHub</span>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("Finding interview prep repositories..."):
            resources = get_github_resources(company_name, job_role)
            if not resources:
                resources = get_improved_fallback_resources(company_name, job_role)

        if resources:
            resource_cards = "".join([
                f'''<a class="resource-card" href="{res['url']}" target="_blank">
                    <span class="resource-icon">📁</span>
                    <span class="resource-name">{res['name']}</span>
                    <span class="resource-arrow">↗</span>
                </a>'''
                for res in resources
            ])
            st.markdown(f'<div class="resource-grid">{resource_cards}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="custom-info">💡 These repositories can help you prepare for the {company_name} hiring process{(" for " + job_role + " roles") if job_role else ""}.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="custom-warn">No specific repositories found for {company_name}. See general resources below.</div>', unsafe_allow_html=True)

        # ── General Resources ────────────────────────────────────────────────
        st.markdown("<div style='margin-top:3rem'></div>", unsafe_allow_html=True)
        display_recommended_resources()

