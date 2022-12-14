from lib.gen import GenInts, GenMultipleOfInRange
from lib.test import CreateTestData, RunIntTest
from lib.worker import *
from scapy.all import Packet
from scapy.layers.inet import Ether
from scapy.packet import Raw
# from scapy.layers.l2 import DestMACField, SourceMACField
from scapy.fields import ByteField, BitField, FieldListField
from scapy.sendrecv import srp

NUM_ITER   = 1     # TODO: Make sure your program can handle larger values
# how much data in each packet
CHUNK_SIZE = 2  # TODO: Define me
ETH_TYPE = 0x8787

class SwitchML(Packet):
    name = "SwitchMLPacket"
    fields_desc = [
        # DestMACField("dst"),
        # SourceMACField("src"),
        # XShortEnumField("type", ETH_TYPE),
        ByteField("rank", 0),
        ByteField("chunk_size", 1),
        BitField("curr_elem_idx", 0, 32),
        # FieldListField("vector", CHUNK_SIZE, BitField("element", 0, 32))
        # TODO: Implement me
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

    # perform allreduce on data and run result on result vector
    # TODO: Implement me
    # send the data-out to iface (eth0)
    # packet should contain rank (id) and data-out
    # store the value in data-in
    # for i in range(int(len(data)/CHUNK_SIZE)):
    
    for i in range(1):
        payload = bytearray()
        for num in data[CHUNK_SIZE*i:CHUNK_SIZE*(i+1)]:
            payload.extend(num.to_bytes(length=4, byteorder="big"))
        packet_send = Ether(type=ETH_TYPE) / SwitchML(rank=rank, chunk_size=CHUNK_SIZE, curr_elem_idx=0) / Raw(payload)#SwitchML(rank=rank, vector=data[CHUNK_SIZE*i:CHUNK_SIZE*(i+1)])
        # print(packet_send[SwitchML].display())
        # print(packet_send[SwitchML].payload)
        # print(packet_send[SwitchML].fields)
        # print(packet_send.payload)
        packet_recv = srp(x = packet_send, iface = iface)
        # Log(packet.show())

def main():
    iface = 'eth0'
    # id
    rank = GetRankOrExit()
    Log("Started...")
    # image this is model training loop
    for i in range(NUM_ITER):
        num_elem = GenMultipleOfInRange(2, 2048, 2 * CHUNK_SIZE) # You may want to 'fix' num_elem for debugging
        # the data generate in local
        data_out = GenInts(num_elem)
        # Log(data_out)
        Log(num_elem)
        # the result of data would receive after call the reduce
        data_in = GenInts(num_elem, 0)
        # test on data can ignore now
        CreateTestData("eth-iter-%d" % i, rank, data_out)
        # do all reduce and then get the result (data_out)
        AllReduce(iface, rank, data_out, data_in)
        RunIntTest("eth-iter-%d" % i, rank, data_in, True)
    Log("Done")

if __name__ == '__main__':
    main()