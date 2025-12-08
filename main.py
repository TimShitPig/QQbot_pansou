from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.core.star.filter.event_message_type import EventMessageType
import json
import re
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import os
from pathlib import Path

# 配置文件路径（保留用于兼容旧版本）
CONFIG_FILE = Path(__file__).parent / "config.json"

@register("helloworld", "YourName", "一个集成了网盘搜索转存功能的插件", "2.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        
        # 初始化网盘搜索转存功能
        self.pansou_api_url = self.config.get("pansou_api_url", "http://154.12.83.97:8085")
        self.ziliao_api_url = self.config.get("ziliao_api_url", "https://www.ziliao.xyz")
        self.ziliao_api_key = self.config.get("ziliao_api_key", "")
        self.ziliao_api_path = self.config.get("ziliao_api_path", "/api/open/transfer")
        self.max_results = self.config.get("max_results", 50)
        self.timeout = self.config.get("timeout", 30)
        self.group_owner_id = self.config.get("group_owner_id", "")
        self.page_size = self.config.get("page_size", 6)  # 每页显示6个结果
        self.links_per_type = self.config.get("links_per_type", 3)  # 每种网盘每轮显示2条
        
        # 确保 API URL 不以 / 结尾
        self.pansou_api_url = self.pansou_api_url.rstrip('/')
        self.ziliao_api_url = self.ziliao_api_url.rstrip('/')
        
        # 会话状态管理（存储用户的搜索结果和分页状态）
        self.user_sessions = {}  # {user_id: {'keyword': str, 'results': list, 'timestamp': datetime, 'current_page': int}}
        self.session_timeout = timedelta(minutes=5)  # 会话5分钟过期
        
        # 网盘类型中文名称映射
        self.cloud_type_names = {
            "baidu": "百度网盘",
            "aliyun": "阿里云盘",
            "quark": "夸克网盘",
            "tianyi": "天翼云盘",
            "uc": "UC网盘",
            "mobile": "移动云盘",
            "115": "115网盘",
            "pikpak": "PikPak",
            "xunlei": "迅雷网盘",
            "123": "123网盘",
            "magnet": "磁力链接",
            "ed2k": "电驴链接",
            "others": "其他"
        }
        
        logger.info(f"[PanSearch] 增强版插件初始化完成")

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent, *args, **kwargs):
        """这是一个 hello world 指令"""
        user_name = event.get_sender_name()
        message_str = event.message_str # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了 {message_str}!") # 发送一条纯文本消息
    
    # 注册指令：搜索
    @filter.command("search")
    async def search(self, event: AstrMessageEvent, *args, **kwargs):
        """搜索网盘资源，格式：/search 关键词"""
        message_str = event.message_str.strip()
        if not message_str:
            yield event.plain_result("❌ 请输入搜索关键词，格式：/search 关键词")
            return
            
        user_id = str(event.get_sender_id())
        result = self._handle_search(message_str, user_id)
        yield event.plain_result(result)
    
    # 注册指令：转存
    @filter.command("transfer")
    async def transfer(self, event: AstrMessageEvent, *args, **kwargs):
        """转存网盘资源，格式：/transfer 序号"""
        message_str = event.message_str.strip()
        if not message_str:
            yield event.plain_result("❌ 请输入序号，格式：/transfer 序号")
            return
            
        user_id = str(event.get_sender_id())
        result = self._handle_transfer(message_str, user_id)
        yield event.plain_result(result)
    
    # 注册指令：翻页
    @filter.command("next")
    async def next_page(self, event: AstrMessageEvent, *args, **kwargs):
        """查看下一页搜索结果"""
        user_id = str(event.get_sender_id())
        result = self._handle_page_navigation("next", user_id)
        yield event.plain_result(result)
    
    @filter.command("prev")
    async def prev_page(self, event: AstrMessageEvent, *args, **kwargs):
        """查看上一页搜索结果"""
        user_id = str(event.get_sender_id())
        result = self._handle_page_navigation("prev", user_id)
        yield event.plain_result(result)
    
    # 处理普通消息
    @filter.event_message_type(EventMessageType.ALL)
    async def handle_any_message(self, event: AstrMessageEvent, *args, **kwargs):
        """处理所有消息，支持：搜XX、求XX、搜索XX、找XX"""
        # 检查是否为群成员加入事件
        try:
            # 获取事件类型
            event_type = None
            if hasattr(event, 'event_type'):
                event_type = event.event_type
            elif hasattr(event, 'message_type'):
                event_type = event.message_type
            
            # 检查消息内容是否包含群成员加入的特征
            message_str = event.message_str
            message_chain = event.get_messages()
            
            # 常见的群成员加入消息特征
            join_keywords = ['加入了群聊', '加入群聊', '已加入', '新成员', 'welcome', 'Welcome']
            is_join_event = False
            
            # 检查消息字符串中是否包含加入关键词
            if any(keyword in message_str for keyword in join_keywords):
                is_join_event = True
            
            # 检查消息链中是否有相关元素
            if message_chain and not is_join_event:
                for msg in message_chain:
                    if hasattr(msg, 'type') and msg.type in ['MemberJoin', 'MemberJoinEvent', '群成员加入', '入群']:
                        is_join_event = True
                        break
                    # 检查消息内容
                    if hasattr(msg, 'content') and any(keyword in msg.content for keyword in join_keywords):
                        is_join_event = True
                        break
            
            # 如果是群成员加入事件，发送欢迎消息
            if is_join_event:
                # 获取新加入的用户信息
                user_name = event.get_sender_name()
                # 发送欢迎消息
                welcome_message = f"@{user_name} 欢迎小伙伴，想要看啥剧，输入搜+剧名发群里并输入数字即可获取链接\n\nPS:搜索功能是机器人回复的，群主没法实时看群，有问题@群主等待处理"
                yield event.plain_result(welcome_message)
                return
        except Exception as e:
            logger.error(f"[PanSearch] 处理群成员加入事件异常: {str(e)}")
        
        message_str = event.message_str.strip()
        user_id = str(event.get_sender_id())
        message_chain = event.get_messages()
        
        # 检查是否被@
        is_at_me = False
        try:
            # 获取机器人自身信息
            if hasattr(event, 'bot'):
                bot = event.bot
                bot_id = str(bot.get('user_id', ''))
                bot_name = bot.get('nickname', '')
            else:
                # 如果没有bot属性，尝试使用其他方式获取机器人信息
                bot_id = ''
                bot_name = ''
            
            # 检查消息链中是否有@机器人的元素
            if message_chain:
                for msg in message_chain:
                    # 检查是否是At类型的消息
                    if hasattr(msg, 'type') and msg.type in ['At', 'at']:
                        # 检查At的对象是否是机器人
                        if hasattr(msg, 'target') and str(msg.target) == bot_id:
                            is_at_me = True
                            break
                        elif hasattr(msg, 'qq') and str(msg.qq) == bot_id:
                            is_at_me = True
                            break
                    # 检查消息内容中是否包含机器人名称
                    if hasattr(msg, 'content') and bot_name in msg.content:
                        is_at_me = True
                        break
        except Exception as e:
            logger.error(f"[PanSearch] 检查@事件异常: {str(e)}")
        
        # 如果被@，发送使用说明
        if is_at_me:
            help_message = "想要看啥剧，输入搜+剧名发群里并输入数字即可获取链接\n如 \"搜仙逆\" 跳出来的对话 如 \"2\"\nPS:搜索功能是机器人回复的，群主没法实时看群，有问题@群主等群主来解决就行"
            yield event.plain_result(help_message)
            return
        
        # 处理搜索指令（支持：搜XX、百度XX、夸克XX、UCXX、迅雷XX）
        search_patterns = [
            r'^搜(.+)$',  # 原有的搜索格式
            r'^百度(.+)$',  # 百度网盘搜索
            r'^夸克(.+)$',  # 夸克网盘搜索
            r'^UC(.+)$',   # UC网盘搜索
            r'^迅雷(.+)$',  # 迅雷网盘搜索
        ]
        
        keyword = None
        cloud_type = "all"  # 默认搜索所有网盘
        
        for pattern in search_patterns:
            match = re.match(pattern, message_str)
            if match:
                keyword = match.group(1).strip()
                # 根据匹配的模式确定网盘类型
                if pattern == r'^百度(.+)$':
                    cloud_type = "baidu"
                elif pattern == r'^夸克(.+)$':
                    cloud_type = "quark"
                elif pattern == r'^UC(.+)$':
                    cloud_type = "uc"
                elif pattern == r'^迅雷(.+)$':
                    cloud_type = "xunlei"
                break
        
        if keyword:
            # 发送搜索中提示
            yield event.plain_result("🔍 搜索中，请等待")
            
            # 记录开始时间
            start_time = datetime.now()
            
            result = self._handle_search(keyword, user_id, cloud_type)
            
            # 计算耗时
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            
            # 获取用户名称用于@
            user_name = event.get_sender_name()
            
            # 添加@用户、有效期和耗时信息
            session = self.user_sessions.get(user_id, {})
            current_page = session.get('current_page', 1)
            
            # 组合最终结果
            final_result = f"@{user_name}\n"
            final_result += result
            final_result += f"\n💡 序号有效期5分钟，过期请重新搜索\n"
            final_result += f"⏱️  本次操作耗时：{elapsed_time:.2f}秒\n"
            final_result += f"📄 当前页：{current_page}"
            
            yield event.plain_result(final_result)
            return
        
        # 处理翻页命令
        if message_str in ["下一页", "下一頁", "next", "下页", "下頁"]:
            # 记录开始时间
            start_time = datetime.now()
            
            result = self._handle_page_navigation("next", user_id)
            
            # 计算耗时
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            
            # 获取用户名称用于@
            user_name = event.get_sender_name()
            
            # 添加@用户、有效期和耗时信息
            session = self.user_sessions.get(user_id, {})
            current_page = session.get('current_page', 1)
            
            # 组合最终结果
            final_result = f"@{user_name}\n"
            final_result += result
            final_result += f"\n💡 序号有效期5分钟，过期请重新搜索\n"
            final_result += f"⏱️  本次操作耗时：{elapsed_time:.2f}秒\n"
            final_result += f"📄 当前页：{current_page}"
            
            yield event.plain_result(final_result)
            return
        
        if message_str in ["上一页", "上一頁", "prev", "previous", "上页", "上頁"]:
            # 记录开始时间
            start_time = datetime.now()
            
            result = self._handle_page_navigation("prev", user_id)
            
            # 计算耗时
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            
            # 获取用户名称用于@
            user_name = event.get_sender_name()
            
            # 添加@用户、有效期和耗时信息
            session = self.user_sessions.get(user_id, {})
            current_page = session.get('current_page', 1)
            
            # 组合最终结果
            final_result = f"@{user_name}\n"
            final_result += result
            final_result += f"\n💡 序号有效期5分钟，过期请重新搜索\n"
            final_result += f"⏱️  本次操作耗时：{elapsed_time:.2f}秒\n"
            final_result += f"📄 当前页：{current_page}"
            
            yield event.plain_result(final_result)
            return
        
        # 处理选择命令（支持：第X个、X、选择X）
        # 只有在用户搜索之后才会处理选择命令
        if user_id in self.user_sessions:
            select_patterns = [
                r'^第(\d+)个$',
                r'^第(\d+)個$',
                r'^(\d+)$',
                r'^选择(\d+)$',
                r'^選擇(\d+)$',
                r'^转存(\d+)$',
            ]
            
            selected_index = None
            for pattern in select_patterns:
                match = re.match(pattern, message_str)
                if match:
                    selected_index = int(match.group(1))
                    break
            
            if selected_index is not None:
                # 记录开始时间
                start_time = datetime.now()
                
                result = self._handle_select(selected_index, user_id)
                
                # 计算耗时
                end_time = datetime.now()
                elapsed_time = (end_time - start_time).total_seconds()
                
                # 添加耗时信息
                result += f"\n⏱️  本次操作耗时：{elapsed_time:.2f}秒"
                
                yield event.plain_result(result)
                return

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
        logger.info(f"[PanSearch] 插件已卸载")
    
    # 内部方法：清理过期会话
    def _cleanup_expired_sessions(self):
        now = datetime.now()
        expired_users = []
        for user_id, session in self.user_sessions.items():
            if now - session['timestamp'] > self.session_timeout:
                expired_users.append(user_id)
        for user_id in expired_users:
            del self.user_sessions[user_id]
    
    # 内部方法：搜索资源
    def _search_resources(self, keyword: str, src: str = "all") -> Dict:
        try:
            url = f"{self.pansou_api_url}/api/search"
            payload = {
                "kw": keyword,
                "res": "merge",
                "src": src
            }
            
            logger.info(f"[PanSearch] 搜索关键词: {keyword}, 网盘类型: {src}")
            logger.info(f"[PanSearch] API请求URL: {url}")
            logger.info(f"[PanSearch] API请求参数: {json.dumps(payload)}")
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[PanSearch] API响应: {json.dumps(result)}")
            logger.info(f"[PanSearch] API响应类型: {type(result)}")
            logger.info(f"[PanSearch] API响应包含的键: {list(result.keys())}")
            
            if result.get("code") == 0:
                logger.info(f"[PanSearch] API返回成功状态码")
                
                # 检查各种可能的数据结构
                if result.get("data"):
                    data = result.get("data", {})
                    logger.info(f"[PanSearch] 从data字段获取搜索结果")
                    logger.info(f"[PanSearch] data字段类型: {type(data)}")
                    logger.info(f"[PanSearch] data包含的键: {list(data.keys())}")
                    
                    # 检查data字段是否包含有效数据
                    if isinstance(data, dict) and (data.get('total', 0) > 0 or data.get('links', []) or data.get('merged_by_type', {})):
                        logger.info(f"[PanSearch] 搜索成功，找到 {data.get('total', 0)} 条结果")
                        return data
                    elif isinstance(data, list):
                        logger.info(f"[PanSearch] data字段是列表，长度: {len(data)}")
                        # 如果data是列表，可能直接包含结果
                        return {"total": len(data), "links": data}
                
                # 检查是否有其他可能的数据结构
                elif "links" in result:
                    logger.info(f"[PanSearch] 直接从API响应获取links字段")
                    links = result.get("links", [])
                    return {"total": len(links), "links": links}
                
                elif "merged_by_type" in result:
                    logger.info(f"[PanSearch] 直接从API响应获取merged_by_type字段")
                    merged_by_type = result.get("merged_by_type", {})
                    # 计算总结果数
                    total = sum(len(links) for links in merged_by_type.values())
                    return {"total": total, "merged_by_type": merged_by_type}
                
                # 如果没有找到预期的数据结构，但返回码是0
                logger.warning(f"[PanSearch] API返回成功，但数据结构不符合预期: {json.dumps(result)}")
                return result
            else:
                logger.error(f"[PanSearch] 搜索失败: {result.get('message', '未知错误')}")
                # 即使返回码不是0，也尝试返回可能的数据
                if result.get("data"):
                    logger.info(f"[PanSearch] API返回错误码，但包含data字段")
                    return result.get("data", {})
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[PanSearch] 搜索请求异常: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"[PanSearch] 搜索处理异常: {str(e)}")
            logger.exception("[PanSearch] 搜索异常详细信息")
            return {}
    
    # 内部方法：提取链接
    def _extract_all_links(self, search_result: Dict) -> List[Dict]:
        logger.info(f"[PanSearch] 提取链接开始，搜索结果类型: {type(search_result)}, 内容: {json.dumps(search_result)}")
        logger.info(f"[PanSearch] 搜索结果包含的键: {list(search_result.keys())}")
        merged_by_type = search_result.get("merged_by_type", {})
        
        # 只支持这4种网盘类型，按顺序：夸克、百度、UC、迅雷
        cloud_types = ["quark", "baidu", "uc", "xunlei"]
        
        # 按类型收集链接
        max_links_per_type = 100
        all_links_by_type = {}
        
        # 检查是否有merged_by_type字段（全类型搜索时返回）
        if merged_by_type:
            logger.info(f"[PanSearch] 找到merged_by_type字段，类型: {type(merged_by_type)}, 内容: {json.dumps(merged_by_type)}")
            logger.info(f"[PanSearch] merged_by_type包含的键: {list(merged_by_type.keys())}")
            for cloud_type in cloud_types:
                if cloud_type in merged_by_type:
                    logger.info(f"[PanSearch] 找到{cloud_type}类型的链接，数量: {len(merged_by_type[cloud_type])}")
                    type_links = []
                    for link in merged_by_type[cloud_type][:max_links_per_type]:
                        logger.info(f"[PanSearch] 处理链接: {link}")
                        type_links.append({
                            "url": link.get("url", ""),
                            "password": link.get("password", ""),
                            "note": link.get("note", ""),
                            "type": cloud_type,
                            "source": link.get("source", "")
                        })
                    if type_links:
                        all_links_by_type[cloud_type] = type_links
                        logger.info(f"[PanSearch] 提取到{cloud_type}类型的{len(type_links)}个链接")
        else:
            logger.info(f"[PanSearch] 没有找到merged_by_type字段，尝试其他数据结构")
            # 没有merged_by_type字段，可能是特定网盘类型搜索
            # 尝试从直接结果中提取链接
            links = search_result.get("links", [])
            logger.info(f"[PanSearch] 直接links字段数量: {len(links)}")
            if links:
                logger.info(f"[PanSearch] 找到直接links字段: {len(links)}个链接")
                logger.info(f"[PanSearch] 第一个链接内容: {links[0] if links else '无'}")
                # 确定当前搜索的网盘类型
                current_src = search_result.get("src", "")
                logger.info(f"[PanSearch] 当前搜索的网盘类型: {current_src}")
                if current_src in cloud_types:
                    # 创建该类型的链接列表
                    type_links = []
                    for link in links[:max_links_per_type]:
                        type_links.append({
                            "url": link.get("url", ""),
                            "password": link.get("password", ""),
                            "note": link.get("note", ""),
                            "type": current_src,
                            "source": link.get("source", "")
                        })
                    if type_links:
                        all_links_by_type[current_src] = type_links
                        logger.info(f"[PanSearch] 提取到{current_src}类型的{len(type_links)}个链接")
            else:
                logger.info(f"[PanSearch] 没有找到直接links字段，尝试按网盘类型查找")
                # 尝试另一种可能的数据结构
                for cloud_type in cloud_types:
                    if cloud_type in search_result:
                        logger.info(f"[PanSearch] 找到{cloud_type}字段，内容: {search_result[cloud_type]}")
                        type_links = []
                        for link in search_result[cloud_type][:max_links_per_type]:
                            type_links.append({
                                "url": link.get("url", ""),
                                "password": link.get("password", ""),
                                "note": link.get("note", ""),
                                "type": cloud_type,
                                "source": link.get("source", "")
                            })
                        if type_links:
                            all_links_by_type[cloud_type] = type_links
                            logger.info(f"[PanSearch] 提取到{cloud_type}类型的{len(type_links)}个链接")
            
            # 尝试一种新的可能数据结构（特定网盘搜索可能返回的结构）
            if not all_links_by_type and "data" in search_result:
                logger.info(f"[PanSearch] 尝试从data字段提取链接")
                data = search_result.get("data", {})
                logger.info(f"[PanSearch] data字段内容: {json.dumps(data)}")
                logger.info(f"[PanSearch] data包含的键: {list(data.keys())}")
                
                # 检查data字段是否包含links
                data_links = data.get("links", [])
                if data_links:
                    logger.info(f"[PanSearch] 从data字段找到links: {len(data_links)}个链接")
                    current_src = data.get("src", "") or search_result.get("src", "")
                    logger.info(f"[PanSearch] 当前搜索的网盘类型: {current_src}")
                    if current_src in cloud_types:
                        type_links = []
                        for link in data_links[:max_links_per_type]:
                            type_links.append({
                                "url": link.get("url", ""),
                                "password": link.get("password", ""),
                                "note": link.get("note", ""),
                                "type": current_src,
                                "source": link.get("source", "")
                            })
                        if type_links:
                            all_links_by_type[current_src] = type_links
                            logger.info(f"[PanSearch] 从data字段提取到{current_src}类型的{len(type_links)}个链接")
            
            # 最后尝试一种可能的数据结构
            if not all_links_by_type:
                logger.info(f"[PanSearch] 尝试直接从搜索结果提取所有可能的链接")
                for key, value in search_result.items():
                    if isinstance(value, list):
                        logger.info(f"[PanSearch] 检查{key}字段，类型为列表，长度: {len(value)}")
                        if value and isinstance(value[0], dict):
                            logger.info(f"[PanSearch] {key}字段包含字典列表，尝试提取链接")
                            # 确定可能的网盘类型
                            possible_types = [t for t in cloud_types if t in str(key).lower() or t in str(search_result.get("src", ""))]
                            cloud_type = possible_types[0] if possible_types else "other"
                            
                            type_links = []
                            for link in value[:max_links_per_type]:
                                if "url" in link or "link" in link:
                                    type_links.append({
                                        "url": link.get("url", link.get("link", "")),
                                        "password": link.get("password", link.get("pwd", "")),
                                        "note": link.get("note", link.get("title", "")),
                                        "type": cloud_type,
                                        "source": link.get("source", "")
                                    })
                            if type_links:
                                all_links_by_type[cloud_type] = type_links
                                logger.info(f"[PanSearch] 直接提取到{cloud_type}类型的{len(type_links)}个链接")
        
        # 按轮次排列：每轮都是 夸克2条 -> 百度2条 -> UC2条 -> 迅雷2条
        links = []
        
        # 计算最大需要多少轮
        max_links_per_type = max([len(links) for links in all_links_by_type.values()], default=0)
        max_rounds = (max_links_per_type + self.links_per_type - 1) // self.links_per_type
        
        logger.info(f"[PanSearch] 最大轮次: {max_rounds}, 每轮链接数: {self.links_per_type}")
        
        for round_num in range(max_rounds):
            for cloud_type in cloud_types:
                if cloud_type in all_links_by_type:
                    type_links = all_links_by_type[cloud_type]
                    start_idx = round_num * self.links_per_type
                    end_idx = start_idx + self.links_per_type
                    round_links = type_links[start_idx:end_idx]
                    if round_links:
                        logger.info(f"[PanSearch] 第{round_num+1}轮，{cloud_type}类型，添加{len(round_links)}个链接")
                        links.extend(round_links)
        
        # 如果没有轮次排列的链接，直接返回所有收集到的链接
        if not links:
            logger.info(f"[PanSearch] 没有轮次排列的链接，直接返回所有收集到的链接")
            for cloud_type in cloud_types:
                if cloud_type in all_links_by_type:
                    logger.info(f"[PanSearch] 直接添加{cloud_type}类型的{len(all_links_by_type[cloud_type])}个链接")
                    links.extend(all_links_by_type[cloud_type][:max_links_per_type])
        
        logger.info(f"[PanSearch] 提取到 {len(links)} 个链接")
        return links
    
    # 内部方法：转存链接
    def _transfer_link(self, url: str, password: str = "") -> Optional[Dict]:
        try:
            api_url = f"{self.ziliao_api_url}{self.ziliao_api_path}"
            
            payload = {
                "url": url,
                "code": password,
                "expired_type": 1,
                "isType": 0
            }
            
            if self.ziliao_api_key:
                payload["api_key"] = self.ziliao_api_key
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            logger.info(f"[PanSearch] 转存链接: {url[:50]}...")
            response = requests.post(
                api_url,
                data=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("code") == 200 and result.get("data"):
                data = result.get("data", {})
                logger.info(f"[PanSearch] 转存成功")
                return data
            elif result.get("code") == 0 and result.get("data"):
                data = result.get("data", {})
                logger.info(f"[PanSearch] 转存成功")
                return data
            else:
                error_msg = result.get("message", result.get("error", "转存失败"))
                logger.error(f"[PanSearch] 转存失败: {error_msg}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[PanSearch] 转存请求异常: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"[PanSearch] 转存处理异常: {str(e)}")
            return None
    
    # 内部方法：格式化分页结果
    def _format_results_page(self, results: List[Dict], page: int = 1) -> Tuple[str, int]:
        if not results:
            return "❌ 没有找到结果", 0
        
        total_pages = (len(results) + self.page_size - 1) // self.page_size
        
        if page < 1:
            page = 1
        if page > total_pages:
            page = total_pages
        
        start_idx = (page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_results = results[start_idx:end_idx]
        
        output = f"🔍 搜索结果（共 {len(results)} 个，第 {page}/{total_pages} 页）\n\n"
        
        for i, result in enumerate(page_results, start=start_idx + 1):
            cloud_type = result.get("type", "unknown")
            cloud_name = self.cloud_type_names.get(cloud_type, cloud_type)
            note = result.get("note", "无标题")
            
            output += f"【{i}】{note}\n"
            output += f"    📦 {cloud_name}\n"
            # 添加分割符，最后一个结果不添加
            if i < end_idx and i < len(results):
                output += "" + "-" * 40 + "\n\n"
            else:
                output += "\n"
        
        if total_pages > 1:
            output += f"💡 输入「下一页」或「上一页」翻页\n"
            output += f"💡 输入「第X个」或「X」选择资源（如：第1个、1）\n"
        
        return output, total_pages
    
    # 内部方法：处理搜索
    def _handle_search(self, keyword: str, user_id: str, cloud_type: str = "all") -> str:
        self._cleanup_expired_sessions()
        
        try:
            # 搜索资源
            search_result = self._search_resources(keyword, cloud_type)
            logger.info(f"[PanSearch] _handle_search: 搜索结果: {json.dumps(search_result)}")
            
            if not search_result:
                logger.info(f"[PanSearch] _handle_search: 搜索结果为空")
                return ">>>查询失败<<<<\n--------------------\n剧名宁少写，不多写、错写\n不要标点、演员名、第几季\n如再查询不到@群主帮你找"
            
            # 计算可能的总结果数
            if isinstance(search_result, dict):
                # 尝试从不同字段获取总结果数
                total = search_result.get("total", 0)
                if total == 0:
                    # 计算实际存在的链接数
                    if "merged_by_type" in search_result:
                        total = sum(len(links) for links in search_result["merged_by_type"].values())
                    elif "links" in search_result:
                        total = len(search_result["links"])
            else:
                total = 0
            
            logger.info(f"[PanSearch] _handle_search: 总结果数: {total}")
            
            if total == 0:
                return ">>>查询失败<<<<\n--------------------\n剧名宁少写，不多写、错写\n不要标点、演员名、第几季\n如再查询不到@群主帮你找"
            
            # 提取所有链接
            links = self._extract_all_links(search_result)
            logger.info(f"[PanSearch] _handle_search: 提取到的链接数量: {len(links)}")
            if not links:
                return ">>>查询失败<<<<\n--------------------\n剧名宁少写，不多写、错写\n不要标点、演员名、第几季\n如再查询不到@群主帮你找"
            
            # 保存到会话
            self.user_sessions[user_id] = {
                'keyword': keyword,
                'results': links,
                'timestamp': datetime.now(),
                'current_page': 1
            }
            
            # 格式化第一页
            output, total_pages = self._format_results_page(links, 1)
            return output
            
        except Exception as e:
            logger.error(f"搜索处理异常: {str(e)}")
            return f"❌ 搜索失败: {str(e)}"
    
    # 内部方法：处理分页导航
    def _handle_page_navigation(self, direction: str, user_id: str) -> str:
        self._cleanup_expired_sessions()
        
        if user_id not in self.user_sessions:
            return "❌ 请先搜索资源"
        
        session = self.user_sessions[user_id]
        results = session['results']
        current_page = session.get('current_page', 1)
        total_pages = (len(results) + self.page_size - 1) // self.page_size
        
        if direction == "next":
            if current_page >= total_pages:
                return f"❌ 已经是最后一页了（共 {total_pages} 页）"
            current_page += 1
        else:  # prev
            if current_page <= 1:
                return "❌ 已经是第一页了"
            current_page -= 1
        
        session['current_page'] = current_page
        session['timestamp'] = datetime.now()
        
        output, _ = self._format_results_page(results, current_page)
        return output
    
    # 内部方法：处理选择
    def _handle_select(self, selected_index: int, user_id: str) -> str:
        self._cleanup_expired_sessions()
        
        if user_id not in self.user_sessions:
            return "❌ 请先搜索资源"
        
        session = self.user_sessions[user_id]
        results = session['results']
        
        if selected_index < 1 or selected_index > len(results):
            return f"❌ 序号无效，请输入 1-{len(results)} 之间的数字"
        
        # 获取选中的资源
        selected_result = results[selected_index - 1]
        url = selected_result.get("url", "")
        password = selected_result.get("password", "")
        note = selected_result.get("note", "")
        cloud_type = selected_result.get("type", "")
        cloud_name = self.cloud_type_names.get(cloud_type, cloud_type)
        
        if not url:
            return "❌ 该资源链接无效"
        
        # 执行转存
        output = f"⏳ 正在转存第 {selected_index} 个资源...\n"
        output += f"📦 类型: {cloud_name}\n\n"
        
        transfer_result = self._transfer_link(url, password)
        
        if transfer_result:
            share_url = transfer_result.get("share_url", "")
            title = transfer_result.get("title", note)
            
            output = f"✅ 转存成功！\n\n"
            output += f"📝 标题: {title}\n"
            output += f"🔗 链接: {share_url}\n"
            if password:
                output += f"🔑 提取码: {password}\n"
            output += f"📦 网盘: {cloud_name}\n"
            
            # 更新会话时间戳，延长会话有效期
            session['timestamp'] = datetime.now()
            
            return output
        else:
            error_message = "❌ 转存失败，请稍后重试\n\n❌ 转存失败，请更换链接"
            if self.group_owner_id:
                error_message += f"\n\n@{self.group_owner_id} 群主，有人转存失败了！"
            return error_message
    
    # 内部方法：处理转存指令
    def _handle_transfer(self, message_str: str, user_id: str) -> str:
        try:
            selected_index = int(message_str)
            # 记录开始时间
            start_time = datetime.now()
            
            result = self._handle_select(selected_index, user_id)
            
            # 计算耗时
            end_time = datetime.now()
            elapsed_time = (end_time - start_time).total_seconds()
            
            # 添加耗时信息
            result += f"\n⏱️  本次操作耗时：{elapsed_time:.2f}秒"
            
            return result
        except ValueError:
            return "❌ 请输入有效的数字序号"
