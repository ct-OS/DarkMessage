#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct

TEA_BLOCK_SIZE = 8
TEA_KEY_SIZE   = 16

def xtea_encrypt(key,block,n=64,endian="!"):
    v0, v1 = struct.unpack(endian + "2L", block)
    k = struct.unpack(endian + "4L", key)
    sum, delta, mask = 0L, 0x9e3779b9L, 0xffffffffL
    for round in range(n):
        v0 = (v0 + (((v1<<4 ^ v1>>5) + v1) ^ (sum + k[sum & 3]))) & mask
        sum = (sum + delta) & mask
        v1 = (v1 + (((v0<<4 ^ v0>>5) + v0) ^ (sum + k[sum>>11 & 3]))) & mask
    return struct.pack(endian + "2L", v0, v1)

def crypt(key,data,iv='\00\00\00\00\00\00\00\00',n=32):
        
    def keygen(key,iv,n):
        while True:
            iv = xtea_encrypt(key,iv,n)
            for k in iv:
                yield ord(k)
    xor = [ chr(x^y) for (x, y) in zip(map(ord, data), keygen(key, iv, n)) ]
    return "".join(xor)

def xtea_decrypt(key,block,n=64,endian="!"):
    v0,v1 = struct.unpack(endian+"2L",block)
    k = struct.unpack(endian+"4L",key)
    delta,mask = 0x9e3779b9L,0xffffffffL
    sum = (delta * n) & mask
    for round in range(n):
        v1 = (v1 - (((v0<<4 ^ v0>>5) + v0) ^ (sum + k[sum>>11 & 3]))) & mask
        sum = (sum - delta) & mask
        v0 = (v0 - (((v1<<4 ^ v1>>5) + v1) ^ (sum + k[sum & 3]))) & mask
    return struct.pack(endian+"2L",v0,v1)

def xtea_cbc_decrypt(key, iv, data, n=32, endian="!"):
    global TEA_BLOCK_SIZE
    size = len(data)
    if (size % TEA_BLOCK_SIZE != 0):
        raise Exception("El tamaño de los datos no es un múltiplo de TEA \ tamaño de bloque (%d)" % (TEA_BLOCK_SIZE))
    decrypted = ""
    i = 0
    while (i < size):
        result = xtea_decrypt(key,
                              data[i:i + TEA_BLOCK_SIZE],
                              n, endian)

        j = 0
        while (j < TEA_BLOCK_SIZE):
            decrypted += chr(ord(result[j]) ^ ord(iv[j]))
            j += 1

        iv = data[i:i + TEA_BLOCK_SIZE]
        i += TEA_BLOCK_SIZE
    return decrypted.strip(chr(0))

def xtea_cbc_encrypt(key, iv, data, n=32, endian="!"):
    global TEA_BLOCK_SIZE
    size = len(data)
    if (size % TEA_BLOCK_SIZE != 0):
        data += chr(0) * (TEA_BLOCK_SIZE-(size%TEA_BLOCK_SIZE))
    encrypted = ""
    i = 0
    while (i < size):
        block = ""
        j = 0
        while (j < TEA_BLOCK_SIZE):
            block += chr(ord(data[i+j]) ^ ord(iv[j]))
            j += 1
        
        encrypted += xtea_encrypt(key,
                              block,
                              n, endian)
        
        iv = encrypted[i:i + TEA_BLOCK_SIZE]
        i += TEA_BLOCK_SIZE
    return encrypted


if __name__ == '__main__':
    import os
    import random
    data = os.urandom(random.randint(0x000000001, 0x00001000))
    key  = os.urandom(TEA_KEY_SIZE)
    iv1  = iv2 = os.urandom(TEA_BLOCK_SIZE)
    print data == xtea_cbc_decrypt(key, iv2, xtea_cbc_encrypt(key, iv1, data))
    
    
