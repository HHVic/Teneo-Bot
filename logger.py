import asyncio
import sys
import pytz
import json
import logging
from datetime import datetime
from colorama import Fore, Style

class CustomLogger:
    def __init__(self, timezone="Asia/Shanghai"):
        self.logger = logging.getLogger("TeneoBot")
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.timezone = timezone  # 定义时区

        # 定义日志级别到中文的映射
        self.level_map = {
            'info': '信息',
            'warn': '警告',
            'error': '错误',
            'success': '成功',
            'debug': '调试'
        }

    def log(self, level, message, value=''):
        now = get_timestamp(format="%Y-%m-%d %H:%M:%S", timezone=self.timezone)
        level_lower = level.lower()
        level_cn = self.level_map.get(level_lower, '信息')
        colors = {
            '信息': Fore.CYAN + Style.BRIGHT,
            '警告': Fore.YELLOW + Style.BRIGHT,
            '错误': Fore.RED + Style.BRIGHT,
            '成功': Fore.GREEN + Style.BRIGHT,
            '调试': Fore.MAGENTA + Style.BRIGHT
        }
        color = colors.get(level_cn, Fore.WHITE)
        level_tag = f"[ {level_cn} ]"
        timestamp = f"[ {now} ]"
        formatted_message = f"{Fore.CYAN + Style.BRIGHT}[ TeneoBot ]{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}{timestamp}{Style.RESET_ALL} {color}{level_tag}{Style.RESET_ALL} {message}"
        
        if value:
            if isinstance(value, dict) or isinstance(value, list):
                try:
                    serialized = json.dumps(value, ensure_ascii=False)
                    formatted_value = f" {Fore.GREEN}{serialized}{Style.RESET_ALL}" if level_cn != '错误' else f" {Fore.RED}{serialized}{Style.RESET_ALL}"
                except Exception as e:
                    self.error("序列化日志值时出错:", str(e))
                    formatted_value = f" {Fore.RED}无法序列化的值{Style.RESET_ALL}"
            else:
                if level_cn == '错误':
                    formatted_value = f" {Fore.RED}{value}{Style.RESET_ALL}"
                elif level_cn == '警告':
                    formatted_value = f" {Fore.YELLOW}{value}{Style.RESET_ALL}"
                else:
                    formatted_value = f" {Fore.GREEN}{value}{Style.RESET_ALL}"
            formatted_message += formatted_value

        # 使用 getattr 结合 level_upper 来获取对应的 logging 级别
        self.logger.log(getattr(logging, level_upper(level_cn), logging.INFO), formatted_message)

    def info(self, message, value=''):
        self.log('info', message, value)

    def warn(self, message, value=''):
        self.log('warn', message, value)

    def error(self, message, value=''):
        self.log('error', message, value)

    def success(self, message, value=''):
        self.log('success', message, value)

    def debug(self, message, value=''):
        self.log('debug', message, value)

def level_upper(level_cn):
    """辅助函数，将中文级别转换为 logging 模块的级别名"""
    mapping = {
        '信息': 'INFO',
        '警告': 'WARNING',
        '错误': 'ERROR',
        '成功': 'INFO',  # 成功映射为 INFO
        '调试': 'DEBUG'
    }
    return mapping.get(level_cn, 'INFO')

def get_timestamp(format="%Y-%m-%d %H:%M:%S", timezone="Asia/Shanghai"):
    """获取当前时间的字符串表示"""
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    return now.strftime(format)

async def delay(seconds):
    await asyncio.sleep(seconds)