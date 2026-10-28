import httpx
from .config import settings

SATOSHIS_PER_BTC = 100_000_000

async def btc_price_usd() -> float:
    """Récupère le prix BTC/USD depuis mempool.space."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{settings.btc_api}/v1/prices")
        r.raise_for_status()
        return float(r.json()["USD"])

async def usd_to_sats(amount_usd: float) -> int:
    price = await btc_price_usd()
    return int(round((amount_usd / price) * SATOSHIS_PER_BTC))

async def check_payment(address: str, expected_sats: int) -> dict | None:
    """Cherche une transaction reçue sur l'adresse avec assez de confirmations."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{settings.btc_api}/address/{address}/txs")
        r.raise_for_status()
        txs = r.json()
    for tx in txs:
        received = 0
        for vout in tx.get("vout", []):
            if vout.get("scriptpubkey_address") == address:
                received += vout.get("value", 0)
        if received >= expected_sats:
            status = tx.get("status", {})
            if status.get("confirmed") and status.get("block_height"):
                return {"txid": tx["txid"], "sats": received}
    return None