import socket
import struct
import binascii

SERVER_IP = "192.168.2.10"
SERVER_PORT = 4000

CONNECT_REQUEST = bytes([
    0xBA, 0x00, 0x00,
    0x00, 0x00,
    0x00, 0x00, 0x00, 0x00
])


def crc32_custom(data: bytes) -> int:
    """按协议文档计算 CRC32"""
    return binascii.crc32(data) & 0xFFFFFFFF


def parse_header(packet: bytes):
    """解析点云包头"""
    header_format = ">8s4s2sH H H B 5s"
    header_size = struct.calcsize(header_format)

    header = struct.unpack(header_format, packet[:header_size])
    vendor, project, version, proto_ver, subframe_cnt, pkt_cnt, pkt_len, flag, reserved = header

    return {
               "vendor": vendor.decode("ascii").strip(),
               "project": project.decode("ascii").strip(),
               "version": version.decode("ascii"),
               "proto_ver": proto_ver,
               "subframe_cnt": subframe_cnt,
               "pkt_cnt": pkt_cnt,
               "pkt_len": pkt_len,
               "flag": flag,
           }, header_size


def parse_timestamp(ts_bytes: bytes):
    """解析消息体时间戳（8字节，小端）"""
    ts_val, = struct.unpack("<Q", ts_bytes)
    day = (ts_val >> 45) & 0x1FFFF
    hour = (ts_val >> 40) & 0x1F
    minute = (ts_val >> 34) & 0x3F
    second = (ts_val >> 28) & 0x3F
    ms = (ts_val >> 18) & 0x3FF
    us = (ts_val >> 8) & 0x3FF
    ns = ts_val & 0xFF
    return {
        "day": day, "hour": hour, "minute": minute,
        "second": second, "ms": ms, "us": us, "ns": ns
    }


def recv_and_parse():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"连接 {SERVER_IP}:{SERVER_PORT} ...")
        s.connect((SERVER_IP, SERVER_PORT))

        print("发送连接请求...")
        s.sendall(CONNECT_REQUEST)

        resp = s.recv(16)
        print(f"收到响应: {resp.hex()}")

        while True:
            header_data = s.recv(32)
            header, header_size = parse_header(header_data)

            pkt_len = header["pkt_len"]
            body_crc_data = s.recv(pkt_len - header_size)

            body = body_crc_data[:-4]
            recv_crc, = struct.unpack(">I", body_crc_data[-4:])

            calc_crc = crc32_custom(body)

            print(f"子帧 {header['subframe_cnt']} 包长 {pkt_len}, CRC {'OK' if recv_crc == calc_crc else 'ERR'}")

            timestamp_info = parse_timestamp(body[:8])
            print("时间戳:", timestamp_info)


if __name__ == "__main__":
    recv_and_parse()
