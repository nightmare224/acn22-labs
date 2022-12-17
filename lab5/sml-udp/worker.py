from binascii import hexlify
from scapy.all import get_if_hwaddr
from scapy.all import Packet
from scapy.config import conf
from scapy.data import ETH_P_ARP
from scapy.data import ETH_P_IP
from scapy.data import ETHER_BROADCAST
from scapy.data import IP_PROTOS
from scapy.fields import ByteField
from scapy.layers.inet import IP
from scapy.layers.inet import UDP
from scapy.layers.l2 import ARP
from scapy.layers.l2 import Ether
from scapy.packet import Raw
from socket import AF_INET
from socket import AF_PACKET
from socket import htons
from socket import inet_ntop
from socket import SOCK_DGRAM
from socket import SOCK_RAW
from socket import socket
from struct import iter_unpack
from struct import pack
from lib.comm import send
from lib.comm import receive
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
BROADCAST_MAC_ADDR = hexlify(ETHER_BROADCAST, ":").decode()

SRC_MAC_ADDR = get_if_hwaddr("eth0")
DST_MAC_ADDR = BROADCAST_MAC_ADDR

SRC_IP_ADDR = ip()
DST_IP_ADDR = ""
for route in conf.route.routes:
    if SRC_IP_ADDR in route:
        DST_IP_ADDR = inet_ntop(AF_INET, pack("!I", route[0]))
        break

SRC_PORT = 38787
DST_PORT = 38788

IP_HEADER_LEN = 20
UDP_HEADER_LEN = 8
SWITCH_ML_HEADER_LEN = 2
UDP_TOTAL_LEN = UDP_HEADER_LEN + SWITCH_ML_HEADER_LEN + CHUNK_SIZE * 4
IP_TOTAL_LEN = IP_HEADER_LEN + UDP_TOTAL_LEN


class SwitchML(Packet):
    name = "SwitchMLPacket"
    fields_desc = [
        ByteField("rank", 0),
        ByteField("num_workers", 1)
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
    global DST_MAC_ADDR
    if DST_MAC_ADDR == BROADCAST_MAC_ADDR:
        pkt_snd = (
            Ether(dst=DST_MAC_ADDR, src=SRC_MAC_ADDR, type=ETH_P_ARP) /
            ARP(hwtype=1, ptype=0x0800, hwlen=6, plen=4, op=1,
                hwsrc=SRC_MAC_ADDR, psrc=SRC_IP_ADDR, pdst=DST_IP_ADDR)
        ).build()
        s = socket(family=AF_PACKET, type=SOCK_RAW, proto=htons(ETH_P_ARP))
        s.bind(("eth0", ETH_P_ARP))
        s.send(pkt_snd)
        DST_MAC_ADDR = ARP(Ether(s.recv(len(pkt_snd))).payload).hwsrc
        s.close()

    for i in range(len(data) // CHUNK_SIZE):
        # for i in range(2):
        payload = bytearray()
        for num in data[CHUNK_SIZE*i:CHUNK_SIZE*(i+1)]:
            # for num in [1, 2, 3]:
            payload.extend(pack("!I", num))
        pkt_snd = (
            Ether(dst=DST_MAC_ADDR, src=SRC_MAC_ADDR, type=ETH_P_IP) /
            IP(ihl=5, len=IP_TOTAL_LEN, id=i, proto=IP_PROTOS.udp, src=SRC_IP_ADDR, dst=DST_IP_ADDR) /
            UDP(sport=SRC_PORT, dport=DST_PORT, len=UDP_TOTAL_LEN) /
            SwitchML(rank=rank, num_workers=NUM_WORKERS) /
            Raw(payload)
        ).build()
        send(soc, pkt_snd, (DST_IP_ADDR, DST_PORT))
        pkt_recv = receive(soc, len(pkt_snd))
        byte_data = SwitchML(
            UDP(IP(Ether(pkt_recv).payload).payload).payload).payload.load
        for j, num in enumerate(iter_unpack("!I", byte_data)):
            result[i * CHUNK_SIZE + j] = num[0]


def main():
    rank = GetRankOrExit()

    s = socket(family=AF_INET, type=SOCK_DGRAM)
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
