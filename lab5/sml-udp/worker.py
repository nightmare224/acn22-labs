from scapy.all import get_if_hwaddr
from scapy.all import Packet
from scapy.config import conf
from scapy.fields import ByteField
from scapy.layers.inet import IP
from scapy.layers.inet import UDP
from scapy.layers.l2 import Ether
from scapy.packet import Raw
from socket import SOCK_DGRAM
from socket import socket
from lib.gen import GenInts
from lib.gen import GenMultipleOfInRange
from lib.test import CreateTestData
from lib.test import RunIntTest
from lib.worker import GetRankOrExit
from lib.worker import ip
from lib.worker import Log
from config import NUM_WORKERS

NUM_ITER = 1     # TODO: Make sure your program can handle larger values
CHUNK_SIZE = 3  # TODO: Define me
SRC_MAC_ADDR = get_if_hwaddr("eth0")
DST_MAC_ADDR = "ff:ff:ff:ff:ff:ff"
SRC_IP_ADDR = ip()
DST_IP_ADDR = ""
for route in conf.route.routes:
    if SRC_IP_ADDR in route:
        DST_IP_ADDR = route[2]
        break
print(conf.route)
SRC_PORT = 38787
DST_PORT = 38788
ETH_TYPE = 0x0800
IP_HEADER_LEN = 20
UDP_HEADER_LEN = 8
SWITCH_ML_HEADER_LEN = 2
UDP_TOTAL_LEN = UDP_HEADER_LEN + SWITCH_ML_HEADER_LEN + CHUNK_SIZE * 4
IP_TOTAL_LEN = IP_HEADER_LEN + UDP_TOTAL_LEN
IP_PROTO = 0x11


class SwitchML(Packet):
    name = "SwitchMLPacket"
    fields_desc = [
        ByteField("rank", 0),
        ByteField("num_workers", 1)
        # TODO: Implement me
    ]


def AllReduce(soc, rank, data, result):
    """
    Perform in-network all-reduce over UDP

    :param str    soc: the socket used for all-reduce
    :param int   rank: the worker's rank
    :param [int] data: the input vector for this worker
    :param [int]  res: the output vector

    This function is blocking, i.e. only returns with a result or error
    """
    # for i in range(len(data) // CHUNK_SIZE):
    for i in range(2):
        payload = bytearray()
        # for num in data[CHUNK_SIZE*i:CHUNK_SIZE*(i+1)]:
        for num in [1, 1, 1]:
            payload.extend(num.to_bytes(length=4, byteorder="big"))
        pkt_snd = (
            Ether(dst=DST_MAC_ADDR, src=SRC_MAC_ADDR, type=ETH_TYPE) /
            IP(ihl=5, len=IP_TOTAL_LEN, id=i, proto=IP_PROTO, src=SRC_IP_ADDR, dst=DST_IP_ADDR) /
            UDP(sport=SRC_PORT, dport=DST_PORT, len=UDP_TOTAL_LEN) /
            SwitchML(rank=rank, num_workers=NUM_WORKERS) /
            Raw(payload)
        ).build()
        # print(Ether(pkt_snd).display())
        soc.sendto(pkt_snd, (DST_IP_ADDR, DST_PORT))
        tmp = soc.recvfrom(1024)
    # NOTE: Do not send/recv directly to/from the socket.
    #       Instead, please use the functions send() and receive() from lib/comm.py
    #       We will use modified versions of these functions to test your program
    pass


def main():
    rank = GetRankOrExit()

    s = socket(type=SOCK_DGRAM)
    # s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    # NOTE: This socket will be used for all AllReduce calls.
    #       Feel free to go with a different design (e.g. multiple sockets)
    #       if you want to, but make sure the loop below still works

    Log("Started...")
    for i in range(NUM_ITER):
        # You may want to 'fix' num_elem for debugging
        num_elem = GenMultipleOfInRange(2, 2048, 2 * CHUNK_SIZE)
        data_out = GenInts(num_elem)
        data_in = GenInts(num_elem, 0)
        CreateTestData(f"udp-iter-{i}", rank, data_out)
        AllReduce(s, rank, data_out, data_in)
        RunIntTest(f"udp-iter-{i}", rank, data_in, True)
    Log("Done")
    s.close()


if __name__ == '__main__':
    main()
