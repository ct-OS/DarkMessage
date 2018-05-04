#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    import Image
except:
    from PIL import Image

import argparse
import hashlib
import hmac
import os
import steganohide as stg
import xtea
import sys


def create_hmac(mac_pass, msg_bytes):
    return hmac.new(
        mac_pass, msg_bytes, digestmod=hashlib.sha256).digest()


def get_msg(img):
    i = Image.open('%s.ste' % img)
    secret = stg.extract_msg(i)
    mac = secret.split('--:--')[0]
    print 'HMAC hex es: \n%s\n' % mac.encode('hex')
    data = secret.split('--:--')[1]
    print 'El mensaje oculto es: \n%s\n' % data
    check_hmac(mac)
    i.show()


def check_hmac(mac, data):
    h_mac = hmac.new(args['m'], bytes(data), digestmod=hashlib.sha256).digest()
    print 'Validación de HMAC: \n%s\n' % str(h_mac == mac)


def hash_128_bit_pass(passwd):
    h = hashlib.sha256()
    h.update(passwd)
    return h.hexdigest()[:16]


def crypt(key, data, iv):
    return xtea.crypt(key, data, iv)


def read_image(image_path):
    if not os.path.exists(image_path):
        raise IOError('El archivo no existe: %s' % image_path)
    else:
        return Image.open(image_path)


def read_text(text_path):
    if not os.path.exists(text_path):
            raise IOError('El archivo no existe: %s' % text_path)
    return open(text_path).read()


def encrypt(data_type):
    h_mac = create_hmac(args['m'], bytes(data))
    secret = '%s--:--%s' % (h_mac, data)
    key = hash_128_bit_pass(args['k'])
    iv = os.urandom(8)
    encrypted_secret = crypt(key, secret, iv)
    dark = stg.hide_msg(image, '%s--:--%s--:--%s' % (
        data_type, iv, encrypted_secret))
    dark.save(args['image'])
    print "Cifrado con éxito su mensaje secreto"
    dark.show()


def decrypt():
    image = Image.open(args['image'])
    dark = stg.extract_msg(image)
    data_type, iv, encrypted_secret = dark.split('--:--')
    key = hash_128_bit_pass(args['k'])
    decrypted_secret = crypt(key, encrypted_secret, iv)
    mac, data = decrypted_secret.split('--:--')

    if data_type == 'image':
        ipath = "resources/secret-image.png"
        print "la imagen secreta se almacena en: " + ipath
        fh = open(ipath, "wb")
        fh.write(data.decode('base64'))
        fh.close()
        Image.open(ipath).show()
    else:
        print 'El mensaje oculto es: \n%s\n' % data

    print 'HMAC hex es: \n%s\n' % mac.encode('hex')
    check_hmac(mac, data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Descripción de tu programa')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-hide', help='encrypt', action='store_true')
    group.add_argument('-open', help='decrypt', action='store_true')
    parser.add_argument(
        '-m', metavar='macpasswd', help='macpassword', required=True)
    parser.add_argument('-k', metavar='passwd', help='password', required=True)
    parser.add_argument('data', nargs='?')
    parser.add_argument('image')
    args = vars(parser.parse_args())

    if args['data']:
        if args['data'].endswith('png') or args['data'].endswith('jpg'):
            import base64
            data_type = 'image'
            with open(args['data'], "rb") as imageFile:
                data = base64.b64encode(imageFile.read())
        elif args['data'].endswith('txt'):
            data_type = 'txt'
            data = read_text(args['data'])
        else:
            print "necesita un mensaje secreto como archivo .txt o .png"
            sys.exit(0)

    if args['image']:
        image = read_image(args['image'])
    else:
        print "necesita imagen para insertar datos"
        sys.exit(0)

    if args['hide']:
        encrypt(data_type)

    if args['open']:
        decrypt()
