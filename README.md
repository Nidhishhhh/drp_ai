# Fashion Search — AI-Powered Visual Fashion Search Engine

Upload a clothing or sneaker image and find visually similar products sorted by price across multiple shopping sites.

## Tech Stack

- **Detection:** YOLOv8 (Ultralytics)
- **Embeddings:** CLIP (OpenAI via open-clip-torch)
- **Similarity Search:** FAISS
- **Preprocessing:** OpenCV
- **Backend:** FastAPI + Celery + Redis
- **Database:** PostgreSQL + SQLAlchemy
- **Scraping:** Selenium + BeautifulSoup
- **Storage:** Cloudflare R2
- **Deployment:** Docker + Railway

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/fashion-search.git
cd fashion-search
```

### 2. Create virtual environment (Python 3.10 required)
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install PyTorch with CUDA (RTX 3050 / CUDA 12.1)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 4. Install remaining dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure environment
```bash
copy .env.example .env       # Windows
cp .env.example .env         # Mac/Linux
# Edit .env with your values
```

### 6. Verify setup
```bash
python verify_setup.py
```

### 7. Run the server
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Project Structure

```
fashion-search/
├── app/                  # Core application modules
│   ├── routes.py         # Phase 2: API endpoints
│   ├── detection.py      # Phase 3: YOLOv8
│   ├── preprocessing.py  # Phase 4: OpenCV
│   ├── embedding.py      # Phase 5: CLIP
│   ├── search.py         # Phase 6: FAISS
│   ├── models.py         # Phase 8: Database models
│   └── auth.py           # Phase 9: JWT auth
├── scraper/
│   └── price_scraper.py  # Phase 10: Selenium
├── models/               # AI model weights (gitignored)
├── data/                 # FAISS index + product catalog
├── static/uploads/       # Uploaded images (gitignored)
├── templates/            # HTML templates
├── tests/                # Test suite
├── logs/                 # Application logs (gitignored)
├── config.py             # Central configuration
├── main.py               # App entry point
├── verify_setup.py       # Phase 1 verification
└── requirements.txt
```

## Build Phases

- [x] Phase 1 — Environment & project setup
- [ ] Phase 2 — FastAPI upload endpoint
- [ ] Phase 3 — YOLOv8 detection pipeline
- [ ] Phase 4 — OpenCV preprocessing
- [ ] Phase 5 — CLIP embedding generation
- [ ] Phase 6 — FAISS index & product catalog
- [ ] Phase 7 — Redis + Celery job queue
- [ ] Phase 8 — PostgreSQL database
- [ ] Phase 9 — JWT authentication
- [ ] Phase 10 — Selenium price scraping
- [ ] Phase 11 — Cloudflare R2 storage
- [ ] Phase 12 — Frontend (HTMX)
- [ ] Phase 13 — Logging & Sentry
- [ ] Phase 14 — Docker + deployment

## GPU Requirements

- NVIDIA GPU with CUDA 12.1+ support
- Minimum 4GB VRAM (RTX 3050 or better)
- CPU fallback supported (slower inference)
