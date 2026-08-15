import { useState, useCallback, useRef, useEffect } from "react";

const API_BASE = "http://localhost:8000/api/v1";

const COLORS = {
  bg: "#0A0A0A",
  surface: "#141414",
  card: "#1C1C1C",
  border: "#2A2A2A",
  accent: "#8B5CF6",
  accentDim: "#6D28D9",
  text: "#F5F5F5",
  textMuted: "#888",
  textDim: "#555",
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function pollResults(taskId, onStep) {
  for (let i = 0; i < 60; i++) {
    await sleep(1000);
    const res = await fetch(`${API_BASE}/results/${taskId}`);
    const data = await res.json();
    if (data.status === "complete") return data.result;
    if (data.status === "failed") throw new Error(data.error || "Search failed");
    if (data.step) onStep(data.step);
  }
  throw new Error("Search timed out");
}

const STEP_LABELS = {
  queued: "Getting in line...",
  detecting: "Finding the garment...",
  embedding: "Understanding the style...",
  searching: "Scanning 364,000 items...",
  enriching: "Finding where to buy...",
};

export default function App() {
  const [phase, setPhase] = useState("upload");
  const [preview, setPreview] = useState(null);
  const [step, setStep] = useState("queued");
  const [results, setResults] = useState(null);
  const [sortBy, setSortBy] = useState("relevance");
  const [error, setError] = useState(null);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef();

  const handleFile = useCallback(async (file) => {
    if (!file || !file.type.startsWith("image/")) {
      setError("Please upload an image file (JPG, PNG, WEBP)");
      return;
    }
    setError(null);
    setPreview(URL.createObjectURL(file));
    setPhase("searching");
    setStep("queued");

    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/search?sort_by=${sortBy}&top_k=10`, {
        method: "POST",
        body: form,
      });
      const { task_id } = await res.json();
      const result = await pollResults(task_id, setStep);
      
      // DEBUG: Log the response to check price_display
      console.log("[drp.ai] Full results:", result);
      console.log("[drp.ai] First item metadata:", result.similar_items?.[0]?.metadata);
      console.log("[drp.ai] Price display check:", result.similar_items?.map(item => ({
        name: item.metadata.product_name,
        price: item.metadata.price,
        currency: item.metadata.currency,
        price_display: item.metadata.price_display
      })));
      
      setResults(result);
      setPhase("results");
    } catch (e) {
      setError(e.message);
      setPhase("upload");
    }
  }, [sortBy]);

  useEffect(() => {
    const handlePaste = (e) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.type.startsWith("image/")) {
          const file = item.getAsFile();
          if (file) handleFile(file);
          break;
        }
      }
    };
    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, [handleFile]);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const reset = () => {
    setPhase("upload");
    setPreview(null);
    setResults(null);
    setError(null);
    setStep("queued");
  };

  return (
    <div style={{ minHeight: "100vh", background: COLORS.bg, color: COLORS.text, fontFamily: "'Inter', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: ${COLORS.bg}; }
        ::selection { background: ${COLORS.accent}40; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: ${COLORS.surface}; }
        ::-webkit-scrollbar-thumb { background: ${COLORS.border}; border-radius: 3px; }

        @keyframes pulse-ring {
          0% { box-shadow: 0 0 0 0 ${COLORS.accent}40; }
          70% { box-shadow: 0 0 0 20px ${COLORS.accent}00; }
          100% { box-shadow: 0 0 0 0 ${COLORS.accent}00; }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .upload-zone {
          border: 2px dashed ${COLORS.border};
          border-radius: 50%;
          width: 280px;
          height: 280px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s ease;
          position: relative;
          overflow: hidden;
        }
        .upload-zone:hover, .upload-zone.dragging {
          border-color: ${COLORS.accent};
          animation: pulse-ring 1.5s ease infinite;
          background: ${COLORS.accent}08;
        }
        .upload-zone img {
          width: 100%;
          height: 100%;
          object-fit: cover;
          border-radius: 50%;
        }

        .sort-btn {
          background: transparent;
          border: 1px solid ${COLORS.border};
          color: ${COLORS.textMuted};
          padding: 6px 14px;
          border-radius: 20px;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s;
          font-family: 'Inter', sans-serif;
        }
        .sort-btn:hover, .sort-btn.active {
          border-color: ${COLORS.accent};
          color: ${COLORS.text};
          background: ${COLORS.accent}15;
        }
        .sort-btn.active { color: ${COLORS.accent}; }

        .product-card {
          background: ${COLORS.card};
          border: 1px solid ${COLORS.border};
          border-radius: 12px;
          overflow: hidden;
          transition: all 0.25s ease;
          animation: fadeUp 0.4s ease both;
        }
        .product-card:hover {
          border-color: ${COLORS.accent}60;
          transform: translateY(-3px);
          box-shadow: 0 8px 32px ${COLORS.accent}15;
        }

        .product-image {
          height: 200px;
          background: linear-gradient(135deg, ${COLORS.surface} 0%, ${COLORS.border} 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          overflow: hidden;
        }
        .product-image img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        .product-image .emoji-placeholder {
          font-size: 48px;
        }

        .product-info {
          padding: 14px;
        }

        .buy-btn {
          background: ${COLORS.accent};
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 8px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s;
          font-family: 'Inter', sans-serif;
          width: 100%;
        }
        .buy-btn:hover { background: ${COLORS.accentDim}; }
        .buy-btn:disabled {
          background: ${COLORS.border};
          color: ${COLORS.textDim};
          cursor: not-allowed;
        }

        .spinner {
          width: 40px; height: 40px;
          border: 3px solid ${COLORS.border};
          border-top-color: ${COLORS.accent};
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        .tag {
          display: inline-block;
          background: ${COLORS.accent}20;
          color: ${COLORS.accent};
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 500;
          text-transform: capitalize;
          position: absolute;
          top: 10px;
          right: 10px;
        }
      `}</style>

      {/* Header */}
      <header style={{ padding: "24px 48px", borderBottom: `1px solid ${COLORS.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, letterSpacing: "-0.5px" }}>
            drp<span style={{ color: COLORS.accent }}>.</span>ai
          </span>
          <span style={{ marginLeft: 12, fontSize: 12, color: COLORS.textDim, fontWeight: 400 }}>visual fashion search</span>
        </div>
        {phase === "results" && (
          <button onClick={reset} style={{ background: "transparent", border: `1px solid ${COLORS.border}`, color: COLORS.textMuted, padding: "8px 18px", borderRadius: 8, cursor: "pointer", fontSize: 13, fontFamily: "'Inter', sans-serif" }}>
            ← New search
          </button>
        )}
      </header>

      {/* Upload Phase */}
      {phase === "upload" && (
        <main style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 73px)", padding: "48px 24px", gap: 40 }}>
          <div style={{ textAlign: "center", maxWidth: 480 }}>
            <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 42, fontWeight: 700, lineHeight: 1.1, letterSpacing: "-1px", marginBottom: 16 }}>
              Spot it.<br />
              <span style={{ color: COLORS.accent }}>Find it.</span><br />
              Wear it.
            </h1>
            <p style={{ color: COLORS.textMuted, fontSize: 16, lineHeight: 1.6 }}>
              Drop a photo of any outfit — we'll find where to buy it.
            </p>
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            {[["relevance", "Best match"], ["price_asc", "Cheapest first"], ["price_desc", "Most expensive"]].map(([val, label]) => (
              <button key={val} className={`sort-btn ${sortBy === val ? "active" : ""}`} onClick={() => setSortBy(val)}>{label}</button>
            ))}
          </div>

          <div
            className={`upload-zone ${dragging ? "dragging" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current.click()}
          >
            {preview ? (
              <img src={preview} alt="preview" />
            ) : (
              <div style={{ textAlign: "center", padding: 24 }}>
                <div style={{ fontSize: 36, marginBottom: 12 }}>↑</div>
                <div style={{ fontSize: 14, color: COLORS.textMuted, lineHeight: 1.5 }}>
                  Drop a photo here<br />
                  <span style={{ fontSize: 12, color: COLORS.textDim }}>or click to browse · ctrl+v to paste</span>
                </div>
              </div>
            )}
          </div>
          <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }} onChange={(e) => handleFile(e.target.files[0])} />

          {error && <p style={{ color: "#EF4444", fontSize: 14 }}>{error}</p>}

          <p style={{ color: COLORS.textDim, fontSize: 12 }}>
            Works with street photos, screenshots, magazine shots — anything with clothing.
          </p>
        </main>
      )}

      {/* Searching Phase */}
      {phase === "searching" && (
        <main style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "calc(100vh - 73px)", gap: 32 }}>
          {preview && (
            <div style={{ width: 120, height: 120, borderRadius: "50%", overflow: "hidden", border: `2px solid ${COLORS.accent}` }}>
              <img src={preview} alt="searching" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            </div>
          )}
          <div className="spinner" />
          <div style={{ textAlign: "center" }}>
            <p style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
              {STEP_LABELS[step] || "Processing..."}
            </p>
            <p style={{ color: COLORS.textDim, fontSize: 13 }}>This usually takes 5–10 seconds</p>
          </div>
        </main>
      )}

      {/* Results Phase */}
      {phase === "results" && results && (
        <main style={{ padding: "40px 48px", maxWidth: 1200, margin: "0 auto" }}>
          {/* Detection badge */}
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 32 }}>
            {preview && (
              <div style={{ width: 64, height: 64, borderRadius: "50%", overflow: "hidden", border: `2px solid ${COLORS.accent}`, flexShrink: 0 }}>
                <img src={preview} alt="query" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              </div>
            )}
            <div>
              <p style={{ color: COLORS.textMuted, fontSize: 13, marginBottom: 4 }}>Detected</p>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, textTransform: "capitalize" }}>
                  {results.detection?.detected_item?.replace(/_/g, " ")}
                </span>
                <span style={{ fontSize: 13, color: COLORS.textMuted }}>
                  {Math.round((results.detection?.confidence || 0) * 100)}% confidence
                </span>
              </div>
            </div>
          </div>

          {/* Sort controls */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
            <p style={{ color: COLORS.textMuted, fontSize: 14 }}>
              {results.similar_items?.length} similar items found
            </p>
            <div style={{ display: "flex", gap: 8 }}>
              {[["relevance", "Best match"], ["price_asc", "Cheapest"], ["price_desc", "Most expensive"]].map(([val, label]) => (
                <button key={val} className={`sort-btn ${sortBy === val ? "active" : ""}`}
                  onClick={() => {
                    setSortBy(val);
                    const sorted = [...results.similar_items];
                    if (val === "price_asc") sorted.sort((a, b) => (a.metadata.price || 0) - (b.metadata.price || 0));
                    else if (val === "price_desc") sorted.sort((a, b) => (b.metadata.price || 0) - (a.metadata.price || 0));
                    else sorted.sort((a, b) => b.score - a.score);
                    setResults({ ...results, similar_items: sorted });
                  }}>{label}</button>
              ))}
            </div>
          </div>

          {/* Results grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 20 }}>
            {results.similar_items?.map((item, i) => (
              <div key={item.item_id} className="product-card" style={{ animationDelay: `${i * 40}ms` }}>
                {/* Image */}
                <div className="product-image">
                  {item.metadata.product_image ? (
                    <img src={item.metadata.product_image} alt={item.metadata.product_name || "product"} />
                  ) : (
                    <span className="emoji-placeholder">👗</span>
                  )}
                </div>

                {/* Info */}
                <div className="product-info">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                    <div>
                      <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 2, textTransform: "capitalize" }}>
                        {item.metadata.product_name || item.metadata.category?.replace(/_/g, " ") || "Product"}
                      </p>
                      <p style={{ fontSize: 12, color: COLORS.textMuted }}>{item.metadata.store || "Online store"}</p>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <p style={{ fontSize: 16, fontWeight: 700, color: COLORS.accent }}>
                        {item.metadata.price_display && item.metadata.price_display !== "USD" && item.metadata.price_display !== "$" 
                          ? item.metadata.price_display 
                          : item.metadata.price && item.metadata.price > 0
                            ? (item.metadata.currency === "INR" ? `₹${Math.round(item.metadata.price)}` : `$${item.metadata.price?.toFixed(2)}`)
                            : "Check price"}
                      </p>
                    </div>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                    <span style={{ fontSize: 11, color: COLORS.textDim }}>
                      {Math.round(item.score * 100)}% match
                    </span>
                    {/* REMOVED: The URL (www2.hm.com) and the "Lens" text */}
                  </div>

                  <button
                    className="buy-btn"
                    disabled={!item.metadata.buy_link}
                    onClick={() => item.metadata.buy_link && window.open(item.metadata.buy_link, "_blank")}
                  >
                    {item.metadata.buy_link ? "Buy now →" : "Coming soon"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </main>
      )}
    </div>
  );
}