# encoding=utf-8
"""
将 stage0_test.jsonl 从 GBK 编码转换为 UTF-8 编码
"""
import shutil

try:
    # 读取 GBK 编码的文件
    with open('stage0_test.jsonl', 'r', encoding='gbk') as f_in:
        content = f_in.read()
    
    # 备份原文件
    shutil.copy('stage0_test.jsonl', 'stage0_test.jsonl.bak')
    
    # 写入 UTF-8 编码
    with open('stage0_test.jsonl', 'w', encoding='utf-8') as f_out:
        f_out.write(content)
    
    print("✓ 成功将 stage0_test.jsonl 从 GBK 转换为 UTF-8")
    print("✓ 原文件已备份为 stage0_test.jsonl.bak")
    
except Exception as e:
    print(f"转换失败: {e}")
    print("请检查文件是否存在或编码是否正确")


