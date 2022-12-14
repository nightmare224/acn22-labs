from lib import config  # do not import anything before this
from p4app import P4Mininet
from mininet.topo import Topo
from mininet.cli import CLI
import os

NUM_WORKERS = 2  # TODO: Make sure your program can handle larger values


class SMLTopo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)
        # add host and add link
        # TODO: Implement me. Feel free to modify the constructor signature
        # NOTE: Make sure worker names are consistent with RunWorkers() below

    def build(self):
        switch = self.addSwitch("s1")
        for i in range(NUM_WORKERS):
            host = self.addHost(f"w{i}")
            self.addLink(switch, host)


def RunWorkers(net):
    """
    Starts the workers and waits for their completion.
    Redirects output to logs/<worker_name>.log (see lib/worker.py, Log())
    This function assumes worker i is named 'w<i>'. Feel free to modify it
    if your naming scheme is different
    """
    worker = lambda rank: "w%i" % rank
    log_file = lambda rank: os.path.join(
        os.environ["APP_LOGS"], "%s.log" % worker(rank)
    )
    for i in range(NUM_WORKERS):
        net.get(worker(i)).sendCmd("python worker.py %d > %s" % (i, log_file(i)))
    for i in range(NUM_WORKERS):
        net.get(worker(i)).waitOutput()


def RunControlPlane(net):
    """
    One-time control plane configuration
    """
    # like insert table entry
    # TODO: Implement me (if needed)
    # print(net.__dir__())
    # print(net.switches[0].ports)
    switch = net.switches[0]
    print(net.switches[0].name)
    ports = []
    # the ports is {<Intf lo>: 0, <Intf s1-eth1>: 1, <Intf s1-eth2>: 2}
    for key in switch.ports:
        if str(key).startswith(switch.name):
            ports.append(switch.ports[key])
    switch.addMulticastGroup(mgid=1, ports=ports)
    # switch.printTableEntries()
    # print(switch.p4info_helper.p4info.tables[0].match_fields[0])
    # print(switch.p4info_helper.p4info.tables[0].ListFields())
    # switch.insertTableEntry(
    #     table_name="TheIngress.sml_table",
    #     match_fields={"hdr.eth.etherType": 0x8787},
    #     action_name="TheIngress.sml_aggr",
    # )


topo = SMLTopo()  # TODO: Create an SMLTopo instance
net = P4Mininet(program="p4/main.p4", topo=topo)
net.run_control_plane = lambda: RunControlPlane(net)
net.run_workers = lambda: RunWorkers(net)
net.start()
net.run_control_plane()
CLI(net)
net.stop()
