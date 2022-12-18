from ipaddress import IPv4Address
from scapy.all import Packet
from scapy.config import conf
from scapy.fields import ByteField
from scapy.packet import Raw
from socket import AF_INET
from socket import SOCK_DGRAM
from socket import socket
from struct import iter_unpack
from struct import pack
from lib.comm import receive
from lib.comm import send
from lib.comm import unreliable_receive
from lib.comm import unreliable_send
from lib.gen import GenInts
from lib.gen import GenMultipleOfInRange
from lib.test import CreateTestData
from lib.test import RunIntTest
from lib.worker import GetRankOrExit
from lib.worker import ip
from lib.worker import Log
from config import NUM_WORKERS
from socket import timeout

NUM_ITER = 1
CHUNK_SIZE = 32

SRC_IP_ADDR = ip()
DST_IP_ADDR = ""
for route in conf.route.routes:
    if SRC_IP_ADDR in route:
        DST_IP_ADDR = str(IPv4Address(route[0]))
        break

SRC_PORT = 38787
DST_PORT = 38787

IP_HEADER_LEN = 20
UDP_HEADER_LEN = 8
SWITCH_ML_HEADER_LEN = 2
UDP_TOTAL_LEN = UDP_HEADER_LEN + SWITCH_ML_HEADER_LEN + CHUNK_SIZE * 4
IP_TOTAL_LEN = IP_HEADER_LEN + UDP_TOTAL_LEN


class SwitchML(Packet):
    name = "SwitchMLPacket"
    fields_desc = [
        ByteField("rank", 0),
        ByteField("num_workers", 1),
        ByteField("chunk_id", 0)  # even or odd
    ]


def AllReduce(soc, rank, data, result):
    """
    Perform reliable in-network all-reduce over UDP

    :param str    soc: the socket used for all-reduce
    :param int   rank: the worker's rank
    :param [int] data: the input vector for this worker
    :param [int]  res: the output vector

    This function is blocking, i.e. only returns with a result or error
    """

    # NOTE: Do not send/recv directly to/from the socket.
    #       Instead, please use the functions send() and receive() from lib/comm.py
    #       We will use modified versions of these functions to test your program
    #
    #       You may use the functions unreliable_send() and unreliable_receive()
    #       to test how your solution handles dropped/delayed packets
    for i in range(len(data) // CHUNK_SIZE):
    # for i in range(2):
        payload = bytearray()
        for num in data[CHUNK_SIZE*i:CHUNK_SIZE*(i+1)]:
        # for num in [1] * CHUNK_SIZE:
            payload.extend(pack("!I", num))
        pkt_snd = bytes(
            SwitchML(rank=rank, num_workers=NUM_WORKERS, chunk_id=i&0x1) /
            Raw(payload)
        )
        while 1:
            soc.settimeout(1.0)
            unreliable_send(soc, pkt_snd, (DST_IP_ADDR, DST_PORT), 0)
            # send(soc, pkt_snd, (DST_IP_ADDR, DST_PORT))
            try:
                # pkt_recv, _ = unreliable_receive(soc, len(pkt_snd), 0)
                pkt_recv, _ = receive(soc, len(pkt_snd))
                if SwitchML(pkt_snd).chunk_id == SwitchML(pkt_recv).chunk_id:
                    break
            except timeout:
                print(f"TIMEOUT {i}")
                pass
        # byte_data = SwitchML(UDP(IP(Ether(pkt_recv).payload).payload).payload).payload.load
        byte_data = SwitchML(pkt_recv).payload.load
        for j, num in enumerate(iter_unpack("!I", byte_data)):
            result[i * CHUNK_SIZE + j] = num[0]


def main():
    rank = GetRankOrExit()

    s = socket(family=AF_INET, type=SOCK_DGRAM)
    s.bind((SRC_IP_ADDR, SRC_PORT))
    # NOTE: This socket will be used for all AllReduce calls.
    #       Feel free to go with a different design (e.g. multiple sockets)
    #       if you want to, but make sure the loop below still works

    Log("Started...")
    for i in range(NUM_ITER):
        # You may want to 'fix' num_elem for debugging
        num_elem = GenMultipleOfInRange(2, 2048, 2 * CHUNK_SIZE)
        data_out = GenInts(num_elem)
        data_in = GenInts(num_elem, 0)
        CreateTestData(f"udp-rel-iter-{i}", rank, data_out)
        AllReduce(s, rank, data_out, data_in)
        RunIntTest(f"udp-rel-iter-{i}", rank, data_in, True)
    Log("Done")
    s.close()


if __name__ == "__main__":
    main()
