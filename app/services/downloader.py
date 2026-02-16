import aiohttp

async def download_bytes(url: str, timeout_total: int = 90) -> bytes:
    timeout = aiohttp.ClientTimeout(total=timeout_total)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.read()
