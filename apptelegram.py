import logging
import httpx
from .config import settings

log = logging.getLogger("telegram")
API = "https://api.telegram.org/bot{token}/sendMessage"

async def notify(text: str, chat_id: str | None = None) -> bool:
    """Envoie un message HTML sur Telegram. Ne lève jamais d'exception."""
    if not settings.telegram_bot_token:
        log.warning("telegram non configuré, envoi ignoré")
        return False
    target = chat_id or settings.telegram_chat_id
    if not target:
        log.warning("TELEGRAM_CHAT_ID absent, envoi ignoré")
        return False
    url = API.format(token=settings.telegram_bot_token)
    payload = {
        "chat_id": target,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(url, json=payload)
            if r.status_code != 200:
                log.error("erreur telegram %s : %s", r.status_code, r.text)
                return False
            return True
    except Exception as e:
        log.error("exception telegram : %s", e)
        return False


def signup_message(user_id: str, email: str, source: str = "web") -> str:
    return (
        "🆕 <b>Nouvelle inscription</b>\n"
        f"👤 Utilisateur : <code>{user_id}</code>\n"
        f"📧 Email : {email}\n"
        f"🌐 Source : {source}\n"
        "🏷 Site : <b>CamHighLevel</b>"
    )

def order_message(order_id: str, amount_usd: float, amount_sats: int,
                  address: str, user_id: str | None = None) -> str:
    return (
        "🧾 <b>Nouvelle commande</b>\n"
        f"🆔 Commande : <code>{order_id}</code>\n"
        f"👤 Utilisateur : <code>{user_id or 'invité'}</code>\n"
        f"💵 Montant : <b>{amount_usd:.2f} $</b>\n"
        f"₿ Sats : <code>{amount_sats}</code>\n"
        f"📥 Adresse : <code>{address}</code>\n"
        "⏳ Statut : <b>en attente de paiement</b>\n"
        "🏷 Site : <b>CamHighLevel</b>"
    )

def paid_message(order_id: str, amount_sats: int, txid: str) -> str:
    return (
        "✅ <b>Paiement reçu</b>\n"
        f"🆔 Commande : <code>{order_id}</code>\n"
        f"₿ Sats : <code>{amount_sats}</code>\n"
        f"🔗 TxID : <code>{txid}</code>\n"
        "🏷 Site : <b>CamHighLevel</b>"
    )

def job_done_message(job_id: str, order_id: str, output_url: str) -> str:
    return (
        "🎬 <b>Deepfake terminé</b>\n"
        f"🆔 Job : <code>{job_id}</code>\n"
        f"🧾 Commande : <code>{order_id}</code>\n"
        f"🔗 Résultat : {output_url}\n"
        "🏷 Site : <b>CamHighLevel</b>"
    )

def error_message(where: str, detail: str) -> str:
    return (
        "⚠️ <b>Erreur</b>\n"
        f"📍 Endroit : {where}\n"
        f"📝 Détail : <code>{detail[:500]}</code>\n"
        "🏷 Site : <b>CamHighLevel</b>"
    )