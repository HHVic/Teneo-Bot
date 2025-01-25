from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
    )
from aiohttp_socks import ProxyConnector
from fake_useragent import UserAgent
import asyncio, json, random

from logger import CustomLogger

logger = CustomLogger()

ua = UserAgent()

class Api:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "Origin": "https://dashboard.teneo.pro",
            "Referer": "https://dashboard.teneo.pro/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": ua.random,
            "X-Api-Key": "OwAG3kib1ivOJG4Y0OCZ8lJETa6ypvsDtGmdhcjA"
        }
        self.proxies = []
        self.proxy_index = 0

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        
        return f"http://{proxies}" # Change with yours proxy schemes if your proxy not have schemes [http:// or socks5://]

    def get_next_proxy(self):
        if not self.proxies:
            logger.error(f"No proxies available!")
            return None
        proxy = self.proxies[self.proxy_index]
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.check_proxy_schemes(proxy)

    def make_headers(self, token=None):
        """生成请求头"""
        hdr = self.headers.copy()
        hdr['Content-Type'] = 'application/json'
        if token:
            hdr['Authorization'] = f'Bearer {token}'
        return hdr

    def new_agent(self, proxy=None):
        """根据代理类型创建代理字典"""
        if proxy:
            if proxy.startswith('http://') or proxy.startswith('https://') or \
            proxy.startswith('socks4://') or proxy.startswith('socks5://'):
                return proxy
            else:
                logger.warn(f"不支持的代理类型: {proxy}")
                return None
        return None

    async def get_ip(self, proxy):
        logger.info(f"Getting IP from {proxy}")
        async with self.new_agent(proxy) as session:
            async with session.get('http://ip-api.com/line/') as response:
                data = await response.text()
                logger.info(data)
                return data.split('\n')[0]
            
    async def claim_referal(self, token, referal_id, proxy=None, retries=5):
        url = "https://api.teneo.pro/api/users/referrals/claim"
        data = {
            "referralId": referal_id
        }
        headers = self.make_headers(token)
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        if response.status == 401:
                            return logger.error('User Not Found')
                        response.raise_for_status()
                        result = await response.json()
                        return result
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                return None
                
    async def get_referal(self, token, proxy=None, retries=5):
        url = "https://api.teneo.pro/api/users/referrals"
        headers = {
            **self.headers,
            'authorization': f'Bearer {token}'
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        if response.status == 401:
                            return logger.error('User Not Found')
                        response.raise_for_status()
                        result = await response.json()
                        return result
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                return None
            
    async def claim_point(self, token, id, proxy=None, retries=5):
        url = f"https://api.teneo.pro/api/campaigns/{id}/claim"
        
        headers = {
            **self.headers,
            'authorization': f'Bearer {token}'
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers) as response:
                        if response.status == 401:
                            return logger.error('User Not Found')
                        response.raise_for_status()
                        result = await response.json()
                        return result
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue

                return None

    async def get_heartbeat_status(self, token, proxy=None, retries=5):
        url = "https://api.teneo.pro/api/campaigns/heartbeat/status"
        headers = {
            **self.headers,
            'authorization': f'Bearer {token}'
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.get(url=url, headers=headers) as response:
                        if response.status == 401:
                            return logger.error('User Not Found')
                        response.raise_for_status()
                        result = await response.json()
                        return result
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                return None
        
    async def claim_points(self, email, password, retries=5):
        proxy = None

        proxy = self.get_next_proxy()

        token = None
        while token is None:
            token = await self.user_login(email, password, proxy)
            if not token:
                logger.error(f'Email: {email} | Get Token Failed.')
                await asyncio.sleep(1)
                
                proxy = self.get_next_proxy()
                continue
        status_resp = await self.get_heartbeat_status(token, proxy)
        logger.info(f'Email: {email} 获取推荐奖励列表....')
        if status_resp:
            for status in status_resp:
                if status['status'] == 'claimable':
                    id = status['id']
                    claim_resp = await self.claim_point(token, id, proxy)
                    if claim_resp and claim_resp['success']:
                        logger.success(f'Claim Point Success. email: {email}, id: {id}')
                        await asyncio.sleep(4)
        logger.success(f'Email: {email} 所有奖励已经领取完毕!')  
            
    async def claim_referals(self, email, password, retries=5):
        proxy = self.get_next_proxy()

        token = None
        while token is None:
            token = await self.user_login(email, password, proxy)
            if not token:
                logger.error(f'Email: {email} | Get Token Failed.')
                await asyncio.sleep(1)    
                proxy = self.get_next_proxy()
                continue
        # 获取所有的推荐列表
        logger.info(f'Email: {email} 获取推荐奖励列表....')
        referal_resp = await self.get_referal(token, proxy, retries)
        if referal_resp and 'success' in referal_resp and referal_resp['success']:
            referal_data = referal_resp['referrals']
            for referal in referal_data:
                if referal and 'canClaim' in referal and referal['canClaim']:
                    referal_id = referal['id']
                    invitee_email = referal['inviteeEmail']
                    claim_data = await self.claim_referal(token, referal_id, proxy, retries)
                    if claim_data and 'success' in claim_data and claim_data['success']:
                        logger.success(
                            f'====claim success: invitee_email: {invitee_email}, referal_id: {referal_id}'
                        )
                        await asyncio.sleep(5)
        logger.success(f'Email: {email} 所有奖励已经领取完毕!')  
        
    async def user_login(self, email: str, password: str, proxy=None, retries=5):
        url = "https://auth.teneo.pro/api/login"
        data = json.dumps({"email": email, "password": password})
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        if response.status == 401:
                            logger.error('User Not Found')
                            return None
                        response.raise_for_status()
                        result = await response.json()
                        return result['access_token']
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                logger.warn(f'Email: {email} Login Failed. retries: {retries}')
        
    async def connect_websocket(self, email: str, token: str, proxy=None, retries=5):
        wss_url = f"wss://secure.ws.teneo.pro/websocket?accessToken={token}&version=v0.2"
        headers = {
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "Cache-Control": "no-cache",
            "Connection": "Upgrade",
            "Host": "secure.ws.teneo.pro",
            "Origin": "chrome-extension://emcclcoaglgcpoognfiggmhnhgabppkm",
            "Pragma": "no-cache",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
            "Sec-WebSocket-Key": "g0PDYtLWQOmaBE5upOBXew==",
            "Sec-WebSocket-Version": "13",
            "Upgrade": "websocket",
            "User-Agent": ua.random
        }
        message = {"type":"PING"}
        delay = random.randint(5, 10)

        while True:
            try:
                connector = ProxyConnector.from_url(proxy) if proxy else None
                session = ClientSession(connector=connector, timeout=ClientTimeout(total=120))
                for attempt in range(retries):
                    try:
                        async with session:
                            async with session.ws_connect(wss_url, headers=headers) as wss:
                                while True:
                                    try:
                                        response = await wss.receive_json(timeout=120)
                                        if response and response.get("message") == "Connected successfully":
                                            today_point = response.get("pointsToday", 0)
                                            total_point = response.get("pointsTotal", 0)
                                            logger.info(f'Account: {email} | Proxy: {proxy} | Earning Today: {today_point} | Earning Total: {total_point}')
                                        elif response and response.get("message") == "Pulse from server":
                                            today_point = response.get("pointsToday", 0)
                                            total_point = response.get("pointsTotal", 0)
                                            heartbeat_today = response.get("heartbeats", 0)
                                            logger.info(f'Account: {email} | Proxy: {proxy} | Earning Today: {today_point} | Earning Total: {total_point} | Heartbeat Today: {heartbeat_today}')
                                        await asyncio.sleep(delay)

                                        for _ in range(90):
                                            await wss.send_json(message)
                                            await asyncio.sleep(10)

                                        await asyncio.sleep(delay)

                                    except Exception as e:
                                        logger.error(f'Account: {email} | Proxy: {proxy} | Status: Websocket Connection Closed. Wait for next ping....')
                                        break

                    except Exception as e:
                        if attempt < retries - 1:
                            await asyncio.sleep(3)
                            continue
                        
                        logger.error(f'Account: {email} | Proxy: {proxy} | Websocket Connect Failed. Attempt For Next retries')
                        proxy = self.get_next_proxy()

            except asyncio.CancelledError:
                logger.error(f'Account: {email} | Proxy: {proxy} | Websocket Closed')
                break
            finally:
                await session.close()