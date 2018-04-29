#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import Image
except:
    from PIL import Image

import itertools


def as_32_bit_string(n):
    """parametro de retorno n (debe ser un int o char) empaquetado en una cadena de 32 bits"""
    byte_string = ''
    for c in range(24, -8, -8):
        byte_string += chr(n >> c & 0xff)
    return byte_string


def as_bits(data):
    """
    devuelve un generador que proporciona una representación de bits
    de los datos de entrada
    """
    return (ord(char) >> shift & 1
            for char, shift in itertools.product(data, range(7, -1, -1)))


def n_tupled(data, n, fillvalue):
    """
    devuelve un iterador que empaqueta datos en tuplas de longitud n
    rellenado con el valor de relleno
    """
    return itertools.izip_longest(*[iter(data)] * n, fillvalue=fillvalue)


def hide_msg(image, data):
    """"
    ocultar la carga en los bits menos significativos de la imagen
    devolver la imagen manipulada o nula
    """

    def set_least_sig_bit(cc, bit):
        """
        establecer el bit menos significativo de un componente de color
        """
        return cc & ~1 | bit

    def hide_bits(pixel, bits):
        """
        esconder el bit en un componente de color
        devolver el pixel tupled con lsb manipulado
        """
        return tuple(itertools.starmap(set_least_sig_bit, zip(pixel, bits)))

    hdr = as_32_bit_string(len(data))
    payload = '%s%s' % (hdr, data)
    n_pxls = image.size[0]*image.size[1]
    n_bnds = len(image.getbands())

    if len(payload)*8 <= n_pxls*n_bnds:
        img_data = image.getdata()
        payload_bits = n_tupled(as_bits(payload), n_bnds, 0)
        new_img_data = itertools.starmap(
            hide_bits, itertools.izip(img_data, payload_bits))
        image.putdata(list(new_img_data))
        return image


def extract_msg(image):

    def get_least_sig_bits(image):
        """obtener los bits menos significativos de la imagen"""
        pxls = image.getdata()
        return (cc & 1 for pxl in pxls for cc in pxl)

    bits = get_least_sig_bits(image)

    def left_shift(n):
        n_bits = itertools.islice(bits, n)
        return reduce(lambda x, y: x << 1 | y, n_bits, 0)

    def next_ch():
        return chr(left_shift(8))

    def defer(func):
        return func()

    n_pxls = image.size[0] * image.size[1]
    n_bnds = len(image.getbands())

    data_length = left_shift(32)
    if n_pxls * n_bnds > 32 + data_length * 8:
        return ''.join(itertools.imap(
            defer, itertools.repeat(next_ch, data_length)))


if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) != 3:
        print "use: python steganohide.py text.txt bild.bmp"
        sys.exit()
    else:
        text = sys.argv[1]
        img = sys.argv[2]

    if not os.path.exists(text):
        raise IOError('El archivo no existe: %s' % text)
    if not os.path.exists(img):
        raise IOError('El archivo no existe: %s' % img)

    print 'Use texto deste: \n%s\n' % sys.argv[1]
    print 'Usar imagen desde: \n%s\n' % sys.argv[2]

    image = Image.open(img)
    data = open(text).read()

    secret = hide_msg(image, data)

    name, ext = os.path.splitext(img)
    secret.save('%s_%s' % (name, ext))
    os.rename('%s_%s' % (name, ext), '%s' % img)
    i = Image.open('%s' % img)
    secret = extract_msg(i)

    print 'El mensaje oculto es: \n%s\n' % secret
    i.show()
