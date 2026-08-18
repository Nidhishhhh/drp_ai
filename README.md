# drp.ai – AI-Powered Visual Fashion Search

> **Spot it. Find it. Wear it.**

drp.ai is an AI-driven visual search engine that allows users to upload a photo of any clothing item and instantly find visually similar products available for purchase online. The system leverages deep learning for object detection, computer vision for image embedding, and scalable vector databases for fast retrieval.

---

## 🚀 Features

- **Object Detection:** Uses a fine-tuned YOLOv8 model (on DeepFashion2) to detect and crop clothing items from any photo (street shots, screenshots, magazines).
- **Visual Embeddings:** Uses OpenAI's CLIP model to convert the cropped clothing image into a high-dimensional vector.
- **Fast Similarity Search:** Utilizes Facebook AI Similarity Search (FAISS) to find the top 10 visually matching products from a pre-indexed catalog.
- **Visual Search Enrichment:** Integrates with the Real-Time Lens Data API (RapidAPI) to fetch real-world buy links and pricing.
- **Real-Time Price Conversion:** Automatically converts USD prices to INR using a live exchange rate API.
- **Gender Detection:** Uses CLIP to classify the gender of the person in the photo to refine search results.
- **Interactive Frontend:** A sleek, dark-themed React web interface with drag-and-drop functionality.
- **Auto-Cropping:** Automatically crops the detected item from the photo before processing.

---

## 🛠️ Tech Stack

### Backend
- **Python 3.10** – Core language.
- **FastAPI** – High-performance web framework with automatic Swagger Docs.
- **Uvicorn** – ASGI server for running the API.
- **Ultralytics (YOLOv8)** – Deep learning model for clothing detection.
- **OpenAI CLIP** – Zero-shot image embedding model.
- **FAISS** – Facebook's library for efficient similarity search.
- **SQLAlchemy & AsyncPG** – Database ORM and connection.
- **Celery & Redis** – Background task queue for image processing.
- **Requests & HTTPx** – For external API integration.  

### Frontend
- **React.js** – Modern UI library.
- **HTML/CSS** – Dark minimalist styling with responsive layout.
- **Netlify** – Continuous deployment hosting.

### Hosting & Deployment
- **Backend:** Hosted on Google Colab (with 12GB RAM) + Cloudflare Tunnel (Public URL).
- **Frontend:** Hosted on Netlify (CDN & Build pipelines).
