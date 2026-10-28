import asyncio, time, uuid
import aiosqlite
from .config import settings
from .storage import public_url
from .telegram import notify, job_done_message, error_message

# Remplace par ton vrai pipeline deepfake (InsightFace, Roop, SimSwap...)
async def run_deepfake(source_path: str, target_path: str, out_path: str):
    await asyncio.sleep(3)  # simulation
    with open(out_path, "wb") as f:
        f.write(b"fake-video-placeholder")

async def worker_loop():
    while True:
        async with aiosqlite.connect(settings.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cur = await conn.execute("SELECT * FROM jobs WHERE status='queued' LIMIT 1")
            job = await cur.fetchone()
            if job:
                await conn.execute(
                    "UPDATE jobs SET status='running', updated_at=? WHERE id=?",
                    (int(time.time()), job["id"]),
                )
                await conn.commit()
                src = f"{settings.local_storage_dir}/{job['source_key']}"
                tgt = f"{settings.local_storage_dir}/{job['target_key']}"
                out_key = f"{uuid.uuid4().hex}.mp4"
                out_path = f"{settings.local_storage_dir}/{out_key}"
                try:
                    await run_deepfake(src, tgt, out_path)
                    url = public_url(out_key)
                    await conn.execute(
                        "UPDATE jobs SET status='done', output_url=?, updated_at=? WHERE id=?",
                        (url, int(time.time()), job["id"]),
                    )
                    await conn.commit()
                    await notify(job_done_message(job["id"], job["order_id"], url))
                except Exception as e:
                    await conn.execute(
                        "UPDATE jobs SET status='error', error=?, updated_at=? WHERE id=?",
                        (str(e), int(time.time()), job["id"]),
                    )
                    await conn.commit()
                    await notify(error_message("worker", str(e)))
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(worker_loop())