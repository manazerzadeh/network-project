from typing import *


DEBUG = True

def int_to_bytes(number: int, byte_size: int):
    byte = [0 for i in range(byte_size)]
    num_copy = number
    for i in range(byte_size - 1, -1, -1):
        byte[i] = num_copy % 256
        num_copy //= 256

    return bytes(byte)


def ip_to_bytes(ip: str):
    str_list = ip.split('.')
    b_list = [0 for i in range(8)]
    for i in range(4):
        b_list[2 * i], b_list[2 * i + 1] = int_to_bytes(int(str_list[i]), 2)

    return bytes(b_list)


def bytes_to_ip(ip_bytes: bytes):
    ip = [0 for i in range(4)]
    for i in range(4):
        ip[i] = int.from_bytes(ip_bytes[2 * i:2 * i + 2], byteorder='big', signed=False)

    return str(ip[0]) + '.' + str(ip[1]) + '.' + str(ip[2]) + '.' + str(ip[3])


if __name__ == '__main__':
    print(int_to_bytes(65000, 4))
