# from logger import CustomLogger
from api import Api
import asyncio, json, os
from termcolor import colored
import logging

logger = logging.getLogger("TeneoBot")
api = Api()

class Teneo: 

    async def load_accounts(self):
        try:
            if not os.path.exists('accounts.json'):
                logger.error("File 'accounts.json' not found!")
                return

            with open('accounts.json', 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError:
            return []
        
    async def load_proxy(self):
        try:
            if not os.path.exists('proxies.txt'):
                logger.error("Proxy file 'proxies.txt' not found!")
                return

            with open('proxies.txt', "r") as f:
                proxies = f.read().splitlines()

            api.proxies = proxies
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Failed to load manual proxies: {e}")
            api.proxies = []

    async def get_choice(self):
        print("\n" + "="*50)
        print(colored("请选择:"))
        print(colored("1. 批量挂机", "cyan"))
        print(colored("2. 批量获取推荐奖励", "cyan"))
        print(colored("3. 批量获取挂机奖励", "cyan"))
        print(colored("4. 退出", "cyan"))
        print("="*50 + "\n")

    async def process_accounts(self, email: str, password: str):
        proxy = api.get_next_proxy()
        token = None
        while token is None:
            token = await api.user_login(email, password, proxy)
            if not token:
                logger.error(f'Email: {email} | Get Token Failed.')
                await asyncio.sleep(2)
                
                proxy = api.get_next_proxy()
                continue
            await api.connect_websocket(email, token, proxy)

    async def main(self):
        try:
            accounts = await self.load_accounts()
            await self.load_proxy()
            if not accounts:
                logger.error(f"No accounts loaded from 'accounts.json'.")
                return
            if not api.proxies:
                logger.error(f"No proxies loaded from 'proxies.txt'.")
                
            logger.info(f'Load Account {len(accounts)} 个, Proxy {len(api.proxies)} 个')

            await self.get_choice()

            choice = input("Enter your choice: ").strip()

            if choice == '1':
                # 挂机
                while True:
                    tasks = []
                    for account in accounts:
                        email = account.get('Email')
                        password = account.get('Password')
                        if email and password:
                            tasks.append(self.process_accounts(email, password))
                    await asyncio.gather(*tasks)
                    await asyncio.sleep(10)
            elif choice == '2':
                # 获取推荐奖励
                for account in accounts:
                    email = account.get('Email')
                    password = account.get('Password')
                    if email and password:
                        await api.claim_referals(email, password)    
            elif choice == '3':
                # 获取挂机奖励
                for account in accounts:
                    email = account.get('Email')
                    password = account.get('Password')
                    if email and password:
                        await api.claim_points(email, password)
                        
            else:
                # 退出
                logger.info("Exiting.")
        except Exception as e:
            logger.error(f"Error: {e}")



if __name__ == "__main__":
    try:
        bot = Teneo()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        logger.info("EXIT.....")