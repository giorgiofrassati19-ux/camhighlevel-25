from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, time, uuid, secrets, httpx, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("camhighlevel")

app = FastAPI(title="CamHighLevel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Configuration ----------
BTC_ADDRESS = os.getenv("BTC_ADDRESS", "bc1qj0s0ghvzjqtcfcgcp5ayqc3taydyksu64c6gaq")
BTC_PRICE_USD = float(os.getenv("BTC_PRICE_USD", "9.00"))
BTC_API = os.getenv("BTC_API", "https://mempool.space/api")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "9049546556:AAH_Au85760962CP0MrZtNdeUehYF0j1Sts")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7300732179")

# ---------- Stockage mémoire (Vercel est serverless : pas de disque persistant) ----------
ORDERS: dict = {}
JOBS: dict = {}

# ---------- Telegram ----------
async def notify(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML",
               "disable_web_page_preview": True}
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(url, json=payload)
            return r.status_code == 200
    except Exception as e:
        log.error("telegram: %s", e)
        return False

# ---------- Modèles ----------
class OrderIn(BaseModel):
    user_id: str | None = None

class SignupIn(BaseModel):
    email: str
    user_id: str | None = None

# ---------- Routes ----------
@app.get("/")
def root():
    index = Path(__file__).parent / "static" / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"status": "ok", "service": "CamHighLevel API"}

@app.get("/api/health")
def health():
    return {"status": "ok", "time": int(time.time())}

@app.post("/api/signup")
async def signup(body: SignupIn):
    user_id = body.user_id or f"u_{secrets.token_hex(4)}"
    await notify(
        "🆕 <b>Nouvelle inscription</b>\n"
        f"👤 Utilisateur : <code>{user_id}</code>\n"
        f"📧 Email : {body.email}\n"
        "🌐 Source : web\n"
        "🏷 Site : <b>CamHighLevel</b>"
    )
    return {"ok": True, "user_id": user_id}

@app.post("/api/order")
async def create_order(body: OrderIn):
    order_id = f"ord_{secrets.token_hex(5)}"
    amount_sats = int(BTC_PRICE_USD / 60000 * 100_000_000)  # taux indicatif, à brancher sur un vrai cours
    order = {
        "id": order_id,
        "created_at": int(time.time()),
        "amount_usd": BTC_PRICE_USD,
        "amount_sats": amount_sats,
        "address": BTC_ADDRESS,
        "status": "pending",
        "user_id": body.user_id,
    }
    ORDERS[order_id] = order
    await notify(
        "🧾 <b>Nouvelle commande</b>\n"
        f"🆔 Commande : <code>{order_id}</code>\n"
        f"👤 Utilisateur : <code>{body.user_id or 'invité'}</code>\n"
        f"💵 Montant : <b>{BTC_PRICE_USD:.2f} $</b>\n"
        f"₿ Sats : <code>{amount_sats}</code>\n"
        f"📥 Adresse : <code>{BTC_ADDRESS}</code>\n"
        "⏳ Statut : <b>en attente de paiement</b>\n"
        "🏷 Site : <b>CamHighLevel</b>"
    )
    return {
        "id": order_id,
        "amount_usd": BTC_PRICE_USD,
        "amount_sats": amount_sats,
        "address": BTC_ADDRESS,
        "status": "pending",
        "btc_uri": f"bitcoin:{BTC_ADDRESS}?amount={amount_sats/1e8:.8f}",
    }

@app.get("/api/order/{order_id}")
def get_order(order_id: str):
    o = ORDERS.get(order_id)
    if not o:
        raise HTTPException(404, "commande introuvable")
    return o

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    key = f"up_{secrets.token_hex(6)}_{file.filename}"
    # Sur Vercel, il faut un stockage externe (S3/R2). Ici on retourne juste la clé.
    return {"ok": True, "key": key, "size": len(data), "filename": file.filename}

@app.post("/api/render")
async def render(order_id: str = Form(...), source_key: str = Form(...), target_key: str = Form(...)):
    o = ORDERS.get(order_id)
    if not o:
        raise HTTPException(404, "commande introuvable")
    job_id = f"job_{secrets.token_hex(5)}"
    JOBS[job_id] = {
        "id": job_id, "order_id": order_id, "status": "queued",
        "source_key": source_key, "target_key": target_key,
        "output_url": None, "error": None, "created_at": int(time.time()),
    }
    return {"id": job_id, "status": "queued"}

@app.get("/api/job/{job_id}")
def get_job(job_id: str):
    j = JOBS.get(job_id)
    if not j:
        raise HTTPException(404, "job introuvable")
    return j

# ---------- Fichiers statiques ----------
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")