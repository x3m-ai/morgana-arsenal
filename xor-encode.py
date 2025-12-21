import sys

key = 0x42
with open(sys.argv[1], 'rb') as f:
    data = f.read()

encoded = bytes([b ^ key for b in data])

with open(sys.argv[2], 'wb') as f:
    f.write(encoded)

print(f"Encoded {len(data)} bytes with XOR key 0x{key:02x}")
