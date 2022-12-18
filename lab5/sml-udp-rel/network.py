from lib import config # do not import anything before this
from p4app import P4Mininet
from mininet.topo import Topo
from mininet.cli import CLI
import os
from config import NUM_WORKERS
from ipaddress import IPv4Address

NUM_WORKERS = 2 # TODO: Make sure your program can handle larger values

class SMLTopo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)
        # TODO: Implement me. Feel free to modify the constructor signature
        # NOTE: Make sure worker names are consistent with RunWorkers() below
    def build(self):
        switch = self.addSwitch("s1")
        for i in range(NUM_WORKERS):
            host = self.addHost(
                f"w{i}",
                mac=f"08:00:00:00:0{i+1}:11",
                ip=f"10.0.{i+1}.1/24",
                defaultRoute=f"via 10.0.{i+1}.0",
            )
            link = self.addLink(switch, host)

def RunWorkers(net):
    """
    Starts the workers and waits for their completion.
    Redirects output to logs/<worker_name>.log (see lib/worker.py, Log())
    This function assumes worker i is named 'w<i>'. Feel free to modify it
    if your naming scheme is different
    """
    worker = lambda rank: "w%i" % rank
    log_file = lambda rank: os.path.join(os.environ['APP_LOGS'], "%s.log" % worker(rank))
    for i in range(NUM_WORKERS):
        net.get(worker(i)).sendCmd('python worker.py %d > %s' % (i, log_file(i)))
    for i in range(NUM_WORKERS):
        net.get(worker(i)).waitOutput()

def mac2int(mac_addr):
    return int(mac_addr.replace(":", ""), 16)

def ip2int(ip_addr):
    return int(IPv4Address(ip_addr))

def RunControlPlane(net):
    """
    One-time control plane configuration
    """

    port_to_host = {}
    port_to_ip = {}
    for link in net.links:
        switch = link.intf1
        host = link.intf2
        port_no = switch.node.ports[switch]
        port_to_host[port_no] = host.node
        rsp = host.node.cmd('route -n')
        gw = rsp.split("\n")[2].split(' ')[0]
        port_to_ip[port_no] = gw
        # switch.setIP(f"{gw}/24")
        # switch.updateIP()

    switch = net.switches[0]
    ports = []
    for intf, port_no in switch.ports.items():
        if intf.name.startswith(switch.name):
            ports.append(port_no)
            # print(key.mac, key.ip)
            # add arp reply table
            switch.insertTableEntry(
                table_name="TheIngress.arp.tbl_arp",
                match_fields={"standard_metadata.ingress_port": port_no},
                action_name="TheIngress.arp.arp_reply",
                action_params={"sw_mac_addr": mac2int(intf.mac)},
            )
            # udp send table
            switch.insertTableEntry(
                table_name="TheEgress.tbl_sml_udp",
                match_fields={"standard_metadata.egress_port": port_no},
                action_name="TheEgress.sml_udp_send",
                action_params={
                    "ip_sw": ip2int(port_to_ip[port_no]),
                    "ip_hst": ip2int(port_to_host[port_no].IP()),
                    "mac_sw": mac2int(intf.MAC()),
                    "mac_hst": mac2int(port_to_host[port_no].MAC()),
                },
            )
    switch.addMulticastGroup(mgid=1, ports=ports)

topo = SMLTopo() # TODO: Create an SMLTopo instance
net = P4Mininet(program="p4/main.p4", topo=topo)
net.run_control_plane = lambda: RunControlPlane(net)
net.run_workers = lambda: RunWorkers(net)
net.start()
net.run_control_plane()
CLI(net)
net.stop()