"""
motd 颜色符号处理模块
"""
import re

def remove_color_codes(text: str) -> str:
    """移除 Minecraft 颜色代码"""
    if not text:
        return text
    # 移除 § 开头的颜色代码 (§0-9, §a-f, §k-o, §r)
    text = re.sub(r'§[0-9a-fk-or]', '', text)
    # 清理多余的空白
    text = '\n'.join(line.strip() for line in text.split('\n'))
    return text.strip()