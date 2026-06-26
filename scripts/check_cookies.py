#!/usr/bin/env python3
"""检查Chrome中所有的cookie域名"""
import sqlite3
import shutil
import os
import ctypes
import ctypes.wintypes

src = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies")
tmp = os.path.join(os.environ.get("TEMP", "."), "chrome_cookies_check.db")
shutil.copy2(src, tmp)

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

crypt32 = ctypes.windll.crypt32
LocalFree = ctypes.windll.kernel32.LocalFree

def decrypt_dpapi(encrypted_data):
    if not encrypted_data:
        return ""
    if encrypted_data[:3] in (b"v10", b"v11"):
        encrypted_data = encrypted_data[3:]
    blob_in = DATA_BLOB(len(encrypted_data), ctypes.cast(encrypted_data, ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()
    if crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        data = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        LocalFree(blob_out.pbData)
        return data.decode("utf-8", errors="replace")
    return ""

conn = sqlite3.connect(tmp)
conn.text_factory = bytes

# 收集所有域名和前10个cookie值
cursor = conn.execute("SELECT host_key, name, encrypted_value FROM cookies ORDER BY host_key")
domains = {}
for row in cursor.fetchall():
    host = row[0].decode() if isinstance(row[0], bytes) else row[0]
    name = row[1].decode() if isinstance(row[1], bytes) else row[1]
    if host not in domains:
        domains[host] = 0
    domains[host] += 1

# 找抖音相关域名
print("=== Cookie域名统计 (前50) ===")
sorted_domains = sorted(domains.items(), key=lambda x: -x[1])[:50]
for host, count in sorted_domains:
    marker = " ← 抖音相关!" if ("douyin" in host or "dy" in host or "tiktok" in host or "ixigua" in host or "byte" in host) else ""
    print(f"  {host}: {count}个{marker}")

# 查找所有音相关域名
print("\n=== 抖音相关Cookie ===")
cursor2 = conn.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%douyin%' OR host_key LIKE '%tiktok%' OR host_key LIKE '%ixigua%'")
found = False
for row in cursor2.fetchall():
    found = True
    host = row[0].decode() if isinstance(row[0], bytes) else row[0]
    name = row[1].decode() if isinstance(row[1], bytes) else row[1]
    encrypted = row[2]
    value = decrypt_dpapi(encrypted)
    print(f"  {host} | {name} = {value[:50] if value else '(解密失败/空)'}")

if not found:
    print("  没有找到任何抖音相关cookie")
    print("  可能Chrome没有登录过抖音")

conn.close()
os.remove(tmp)
