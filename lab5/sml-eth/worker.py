from scapy.all import get_if_hwaddr
from scapy.all import Packet
# from scapy.fields import BitField
from scapy.fields import ByteField
# from scapy.fields import FieldListField
from scapy.layers.l2 import Ether
# from scapy.layers.l2 import DestMACField
# from scapy.layers.l2 import SourceMACField
from scapy.packet import Raw
from scapy.sendrecv import srp
from struct import pack
from struct import iter_unpack
from lib.gen import GenInts
from lib.gen import GenMultipleOfInRange
from lib.test import CreateTestData
from lib.test import RunIntTest
from lib.worker import GetRankOrExit
from lib.worker import Log
from config import NUM_WORKERS

NUM_ITER = 1  # TODO: Make sure your program can handle larger values
# how much data in each packet
CHUNK_SIZE = 32
MAC_ADDR = get_if_hwaddr("eth0")
ETH_TYPE = 0x8787


class SwitchML(Packet):
    name = "SwitchMLPacket"
    fields_desc = [
        # DestMACField("dst"),
        # SourceMACField("src"),
        # XShortEnumField("type", ETH_TYPE),
        ByteField("rank", 0),
        ByteField("num_workers", 1)
        # FieldListField("vector", CHUNK_SIZE, BitField("element", 0, 32))
    ]
    # design header format, use scapy
    # implement this packet


def AllReduce(iface, rank, data, result):
    """
    Perform in-network all-reduce over ethernet

    :param str  iface: the ethernet interface used for all-reduce
    :param int   rank: the worker's rank
    :param [int] data: the input vector for this worker
    :param [int]  res: the output vector

    This function is blocking, i.e. only returns with a result or error
    """
    for i in range(len(data) // CHUNK_SIZE):
    # for i in range(2):
        payload = bytearray()
        for num in data[CHUNK_SIZE*i:CHUNK_SIZE*(i+1)]:
        # for num in [1, 1, 1]:
            payload.extend(pack("!I", num))

        pkt_snd = (
            Ether(src=MAC_ADDR, type=ETH_TYPE) /
            SwitchML(rank=rank, num_workers=NUM_WORKERS) /
            Raw(payload)
        )
        # print(packet_send[SwitchML].display())
        pkt_rcv, _ = srp(x=pkt_snd, iface=iface)
        byte_data = SwitchML(pkt_rcv.res[0][1].payload).payload.load
        for j, num in enumerate(iter_unpack("!I", byte_data)):
            result[i * CHUNK_SIZE + j] = num[0]


def main():
    iface = "eth0"
    # id
    rank = GetRankOrExit()
    Log("Started...")
    # image this is model training loop
    for i in range(NUM_ITER):
        # You may want to 'fix' num_elem for debugging
        num_elem = GenMultipleOfInRange(2, 2048, 2 * CHUNK_SIZE)
        # the data generate in local
        data_out = GenInts(num_elem)
        # Log(data_out)
        Log(num_elem)
        # the result of data would receive after call the reduce
        data_in = GenInts(num_elem, 0)
        # test on data can ignore now
        CreateTestData(f"eth-iter-{i}", rank, data_out)
        # do all reduce and then get the result (data_out)
        AllReduce(iface, rank, data_out, data_in)
        print(f"iter {i}: {data_in}")
        RunIntTest(f"eth-iter-{i}", rank, data_in, True)
    Log("Done")


if __name__ == "__main__":
    main()
