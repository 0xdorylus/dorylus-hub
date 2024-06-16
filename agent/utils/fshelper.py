import hashlib


async def get_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk =  f.read(8192)
            if not chunk:
                break
            sha256_hash.update(chunk)
        file_hash = sha256_hash.hexdigest()
    return file_hash