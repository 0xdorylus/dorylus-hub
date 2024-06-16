
import base58
import hashlib

def calc_file_digest(file_path):
    # 文件路径
    # 创建 SHA-256 哈希对象
    sha256_hash = hashlib.sha256()
    # 打开文件并逐块读取数据计算哈希值
    with open(file_path, 'rb') as file:
        while True:
            # 读取数据块
            data = file.read(4096)  # 每次读取 4KB 数据块
            # 如果数据为空，表示已读取完文件，则退出循环
            if not data:
                break
            # 更新哈希对象
            sha256_hash.update(data)

    # 获取哈希值的十六进制表示
    file_hash = sha256_hash.hexdigest()
    print(f"SHA-256 Hash: {file_hash}")
    digest_str = base58.b58encode_int(int(file_hash, 16)).decode('utf-8')
    print(digest_str)
    return digest_str

# calc_file_digest('./demo.txt')