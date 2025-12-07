# encoding:utf-8
"""
增强版网盘搜索转存插件
支持分页浏览、选择转存功能
"""

import json
import re
import requests
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PanSearchPluginEnhanced:
    """增强版网盘搜索转存插件（支持分页和选择）"""
    
    def __init__(self, config: Dict):
        """
        初始化插件
        
        Args:
            config: 配置字典
        """
        self.pansou_api_url = config.get("pansou_api_url", "http://localhost:8888")
        self.ziliao_api_url = config.get("ziliao_api_url", "https://www.ziliao.xyz")
        self.ziliao_api_key = config.get("ziliao_api_key", "")
        self.ziliao_api_path = config.get("ziliao_api_path", "/api/open/transfer")
        self.max_results = config.get("max_results", 50)  # 增加最大结果数
        self.timeout = config.get("timeout", 30)
        self.page_size = 6  # 每页显示6个结果（夸克2条 -> 百度2条 -> UC2条）
        self.links_per_type = 2  # 每种网盘每轮显示2条
        
        # 确保 API URL 不以 / 结尾
        self.pansou_api_url = self.pansou_api_url.rstrip('/')
        self.ziliao_api_url = self.ziliao_api_url.rstrip('/')
        
        # 会话状态管理（存储用户的搜索结果和分页状态）
        # 格式：{user_id: {'keyword': str, 'results': list, 'timestamp': datetime}}
        self.user_sessions = {}
        self.session_timeout = timedelta(minutes=10)  # 会话10分钟过期
        
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
        logger.info(f"[PanSearch] Pansou API: {self.pansou_api_url}")
        logger.info(f"[PanSearch] Ziliao API: {self.ziliao_api_url}{self.ziliao_api_path}")
    
    def _cleanup_expired_sessions(self):
        """清理过期的会话"""
        now = datetime.now()
        expired_users = []
        for user_id, session in self.user_sessions.items():
            if now - session['timestamp'] > self.session_timeout:
                expired_users.append(user_id)
        for user_id in expired_users:
            del self.user_sessions[user_id]
    
    def search_resources(self, keyword: str) -> Dict:
        """
        调用 pansou API 搜索资源
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            搜索结果字典
        """
        try:
            url = f"{self.pansou_api_url}/api/search"
            payload = {
                "kw": keyword,
                "res": "merge",
                "src": "all"
            }
            
            logger.info(f"[PanSearch] 搜索关键词: {keyword}")
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 0 and result.get("data"):
                data = result.get("data", {})
                logger.info(f"[PanSearch] 搜索成功，找到 {data.get('total', 0)} 条结果")
                return data
            else:
                logger.error(f"[PanSearch] 搜索失败: {result.get('message', '未知错误')}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[PanSearch] 搜索请求异常: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"[PanSearch] 搜索处理异常: {str(e)}")
            return {}
    
    def extract_all_links(self, search_result: Dict) -> List[Dict]:
        """
        从搜索结果中提取网盘链接
        只提取：夸克、百度、UC、迅雷这4种网盘
        每种网盘取足够多的链接（用于分页），然后按轮次排列：
        第1轮：夸克3条 -> 百度3条 -> UC3条 -> 迅雷3条
        第2轮：夸克再3条 -> 百度再3条 -> UC再3条 -> 迅雷再3条
        以此类推
        
        Args:
            search_result: 搜索结果字典
            
        Returns:
            链接列表（按指定顺序排列）
        """
        merged_by_type = search_result.get("merged_by_type", {})
        
        # 只支持这4种网盘类型，按顺序：夸克、百度、UC、迅雷
        cloud_types = ["quark", "baidu", "uc", "xunlei"]
        
        # 按类型收集链接，每种取足够多的链接（用于分页）
        # 假设最多显示10页，每页12条，每种网盘需要约30条
        max_links_per_type = 100  # 每种网盘最多取100条，足够分页使用
        all_links_by_type = {}
        for cloud_type in cloud_types:
            if cloud_type in merged_by_type:
                type_links = []
                for link in merged_by_type[cloud_type][:max_links_per_type]:
                    type_links.append({
                        "url": link.get("url", ""),
                        "password": link.get("password", ""),
                        "note": link.get("note", ""),
                        "type": cloud_type,
                        "source": link.get("source", "")
                    })
                if type_links:
                    all_links_by_type[cloud_type] = type_links
        
        # 按轮次排列：每轮都是 夸克2条 -> 百度2条 -> UC2条 -> 迅雷2条
        links = []
        # 计算最多能有多少轮（每种网盘的总数除以2）
        max_rounds = max([len(links) // self.links_per_type for links in all_links_by_type.values()], default=0)
        
        # 每轮：夸克2条 -> 百度2条 -> UC2条 -> 迅雷2条
        for round_num in range(max_rounds):
            for cloud_type in cloud_types:
                if cloud_type in all_links_by_type:
                    type_links = all_links_by_type[cloud_type]
                    # 每轮取3条
                    start_idx = round_num * self.links_per_type
                    end_idx = start_idx + self.links_per_type
                    round_links = type_links[start_idx:end_idx]
                    if round_links:  # 只有当还有链接时才添加
                        links.extend(round_links)
        
        logger.info(f"[PanSearch] 提取到 {len(links)} 个链接（只包含夸克、百度、UC、迅雷）")
        
        # 统计各类型数量
        type_counts = {}
        for link in links:
            link_type = link.get("type", "unknown")
            type_counts[link_type] = type_counts.get(link_type, 0) + 1
        
        logger.info(f"[PanSearch] 网盘类型统计: {type_counts}")
        
        return links
    
    def transfer_link(self, url: str, password: str = "") -> Optional[Dict]:
        """
        调用 ziliao 网站 API 转存链接
        
        Args:
            url: 网盘链接
            password: 提取码/密码
            
        Returns:
            转存结果字典，失败返回 None
        """
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
            else:
                payload["api_key"] = ""
            
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
    
    def format_results_page(self, results: List[Dict], page: int = 1) -> Tuple[str, int]:
        """
        格式化分页结果
        
        Args:
            results: 结果列表
            page: 页码（从1开始）
            
        Returns:
            (格式化后的字符串, 总页数)
        """
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
            output += f"    📦 {cloud_name}\n\n"
        
        if total_pages > 1:
            output += f"💡 输入「下一页」或「上一页」翻页\n"
            output += f"💡 输入「第X个」或「X」选择资源（如：第1个、1）\n"
        
        return output, total_pages
    
    def handle_message(self, message: str, user_id: str = "default") -> str:
        """
        处理消息（主入口函数）
        
        Args:
            message: 用户消息内容
            user_id: 用户ID（用于会话管理）
            
        Returns:
            回复内容
        """
        # 清理过期会话
        self._cleanup_expired_sessions()
        
        message = message.strip()
        
        # 1. 检测搜索命令（支持：搜XX、求XX、搜索XX、找XX）
        search_patterns = [
            r'^搜(.+)$',
            r'^求(.+)$',
            r'^搜索(.+)$',
            r'^找(.+)$',
            r'^/搜索(.+)$',
            r'^/search(.+)$',
        ]
        
        keyword = None
        for pattern in search_patterns:
            match = re.match(pattern, message)
            if match:
                keyword = match.group(1).strip()
                break
        
        # 2. 如果检测到搜索关键词，执行搜索
        if keyword:
            try:
                # 搜索资源
                search_result = self.search_resources(keyword)
                if not search_result:
                    return "❌ 搜索失败，请稍后重试"
                
                total = search_result.get("total", 0)
                if total == 0:
                    return f"🔍 未找到关键词「{keyword}」的相关资源"
                
                # 提取所有链接
                links = self.extract_all_links(search_result)
                if not links:
                    return f"🔍 找到 {total} 条结果，但无法提取有效链接"
                
                # 保存到会话
                self.user_sessions[user_id] = {
                    'keyword': keyword,
                    'results': links,
                    'timestamp': datetime.now(),
                    'current_page': 1
                }
                
                # 格式化第一页
                output, total_pages = self.format_results_page(links, 1)
                return output
                
            except Exception as e:
                logger.error(f"搜索处理异常: {str(e)}")
                return f"❌ 搜索失败: {str(e)}"
        
        # 3. 检测翻页命令
        if message in ["下一页", "下一頁", "next", "下页", "下頁"]:
            if user_id not in self.user_sessions:
                return "❌ 请先搜索资源"
            
            session = self.user_sessions[user_id]
            results = session['results']
            current_page = session.get('current_page', 1)
            total_pages = (len(results) + self.page_size - 1) // self.page_size
            
            if current_page >= total_pages:
                return f"❌ 已经是最后一页了（共 {total_pages} 页）"
            
            current_page += 1
            session['current_page'] = current_page
            session['timestamp'] = datetime.now()
            
            output, _ = self.format_results_page(results, current_page)
            return output
        
        if message in ["上一页", "上一頁", "prev", "previous", "上页", "上頁"]:
            if user_id not in self.user_sessions:
                return "❌ 请先搜索资源"
            
            session = self.user_sessions[user_id]
            results = session['results']
            current_page = session.get('current_page', 1)
            
            if current_page <= 1:
                return "❌ 已经是第一页了"
            
            current_page -= 1
            session['current_page'] = current_page
            session['timestamp'] = datetime.now()
            
            output, _ = self.format_results_page(results, current_page)
            return output
        
        # 4. 检测选择命令（支持：第X个、X、选择X）
        select_patterns = [
            r'^第(\d+)个$',
            r'^第(\d+)個$',
            r'^(\d+)$',
            r'^选择(\d+)$',
            r'^選擇(\d+)$',
        ]
        
        selected_index = None
        for pattern in select_patterns:
            match = re.match(pattern, message)
            if match:
                selected_index = int(match.group(1))
                break
        
        if selected_index is not None:
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
            
            transfer_result = self.transfer_link(url, password)
            
            if transfer_result:
                share_url = transfer_result.get("share_url", "")
                title = transfer_result.get("title", note)
                
                output = f"✅ 转存成功！\n\n"
                output += f"📝 标题: {title}\n"
                output += f"🔗 链接: {share_url}\n"
                if password:
                    output += f"🔑 提取码: {password}\n"
                output += f"📦 网盘: {cloud_name}\n"
                
                # 清除会话（转存完成后）
                if user_id in self.user_sessions:
                    del self.user_sessions[user_id]
                
                return output
            else:
                return f"❌ 转存失败，请稍后重试\n\n原始链接: {url}"
        
        # 5. 其他消息不处理
        return None


# 使用示例
if __name__ == "__main__":
    # 配置
    config = {
        "pansou_api_url": "http://154.12.83.97:8085",
        "ziliao_api_url": "https://www.ziliao.xyz",
        "ziliao_api_path": "/api/open/transfer",
        "ziliao_api_key": "",
        "max_results": 50,
        "timeout": 30
    }
    
    # 创建插件实例
    plugin = PanSearchPluginEnhanced(config)
    
    # 模拟用户交互
    user_id = "test_user"
    
    print("=" * 60)
    print("增强版网盘搜索插件测试")
    print("=" * 60)
    
    # 测试1: 搜索
    print("\n【测试1】用户发送: 搜仙逆")
    result = plugin.handle_message("搜仙逆", user_id)
    print(result)
    
    # 测试2: 翻页
    print("\n【测试2】用户发送: 下一页")
    result = plugin.handle_message("下一页", user_id)
    print(result)
    
    # 测试3: 选择
    print("\n【测试3】用户发送: 第1个")
    result = plugin.handle_message("第1个", user_id)
    print(result)

