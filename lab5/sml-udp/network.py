from lib import config  # do not import anything before this
from p4app import P4Mininet
from os import environ
from pathlib import PurePath
from mininet.cli import CLI
from mininet.topo import Topo
from config import NUM_WORKERS


class SMLTopo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)
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
    def worker(rank):
        return f"w{rank}"

    def log_file(rank):
        return PurePath(environ['APP_LOGS']).joinpath(f"{worker(rank)}.log")

    for i in range(NUM_WORKERS):
        net.get(worker(i)).sendCmd(f"python worker.py {i} > {log_file(i)}")
    for i in range(NUM_WORKERS):
        net.get(worker(i)).waitOutput()


def RunControlPlane(net):
    """
    One-time control plane configuration
    """
    # TODO: Implement me (if needed)
    switch = net.switches[0]
    ports = [value
             for key, value in switch.ports.items()
             if key.name.startswith(switch.name)]
    switch.addMulticastGroup(mgid=1, ports=ports)

topo = SMLTopo()  # TODO: Create an SMLTopo instance
net = P4Mininet(program="p4/main.p4", topo=topo)
net.run_control_plane = lambda: RunControlPlane(net)
net.run_workers = lambda: RunWorkers(net)
net.start()
net.run_control_plane()
CLI(net)
net.stop()
