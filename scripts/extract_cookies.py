#!/usr/bin/env python3
"""从Chrome浏览器提取抖音Cookie"""
import sqlite3
import shutil
import os
import json
import ctypes
import ctypes.wintypes

# 复制Cookie文件到临时路径（避免文件锁）
src = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies")
tmp = os.path.join(os.environ.get("TEMP", "."), "chrome_cookies_tmp.db")
shutil.copy2(src, tmp)

# Windows DPAPI 解密
class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

crypt32 = ctypes.windll.crypt32
LocalFree = ctypes.windll.kernel32.LocalFree

def decrypt_dpapi(encrypted_data):
    """解密 DPAPI 加密的数据"""
    if not encrypted_data:
        return ""
    # Chrome v80+ 使用版本前缀
    if encrypted_data[:3] in (b"v10", b"v11"):
        encrypted_data = encrypted_data[3:]
    
    blob_in = DATA_BLOB(len(encrypted_data), ctypes.cast(encrypted_data, ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()
    
    if crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)
    ):
        data = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        LocalFree(blob_out.pbData)
        return data.decode("utf-8", errors="replace")
    return ""

# 读取cookie数据库
conn = sqlite3.connect(tmp)
conn.text_factory = bytes

# 先看表结构
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0].decode() if isinstance(row[0], bytes) else row[0] for row in cursor.fetchall()]

# 查询 douyin.com 的 cookies
try:
    cursor = conn.execute(
        "SELECT host_key, name, path, encrypted_value, has_expires, expires_utc, is_secure, is_httponly "
        "FROM cookies WHERE host_key LIKE '%douyin%' OR host_key LIKE '%dy%'"
    )
    
    cookies = []
    for row in cursor.fetchall():
        host = row[0].decode() if isinstance(row[0], bytes) else row[0]
        name = row[1].decode() if isinstance(row[1], bytes) else row[1]
        path = row[2].decode() if isinstance(row[2], bytes) else row[2]
        encrypted = row[3]
        
        value = decrypt_dpapi(encrypted)
        
        if value:
            cookies.append({
                "host": host,
                "name": name,
                "path": path,
                "value": value,
            })
    
    print(f"找到 {len(cookies)} 个 douyin.com 的 Cookie\n")
    
    if cookies:
        # 输出为 Netscape cookie 格式
        print("# Netscape HTTP Cookie File")
        print("# 从 Chrome 导出\n")
        for c in cookies:
            print(f"{c['host']}\tTRUE\t{c['path']}\tFALSE\t2147483647\t{c['name']}\t{c['value']}")
        
        # 同时保存文件
        with open("douyin_cookies.txt", "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# 从 Chrome 导出\n\n")
            for c in cookies:
                f.write(f"{c['host']}\tTRUE\t{c['path']}\tFALSE\t2147483647\t{c['name']}\t{c['value']}\n")
        print(f"\n已保存到 douyin_cookies.txt")
    
except Exception as e:
    print(f"查询错误: {e}")

conn.close()
os.remove(tmp)
