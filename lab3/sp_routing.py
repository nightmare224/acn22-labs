# This code is part of the Advanced Computer Networks (2020) course at Vrije 
# Universiteit Amsterdam.

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

#!/usr/bin/env python3

from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib.packet import ether_types

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase

import topo
from dijkstra import Dijkstra

class SPRouter(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SPRouter, self).__init__(*args, **kwargs)
        self.topo_net = topo.Fattree(4)
        self.mac_to_port = mac_to_port.MacToPortTable()
        self.dpid_to_node = {}
        self.dijkstra_fattree = Dijkstra(self.topo_net.switches)

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        # Switches and links in the network
        switches = get_switch(self, None)
        links = get_link(self, None)
        for switch in switches:
            switch_info = switch.to_dict()
            dpid = int(switch_info['dpid'], base=16)
            # just choose the first one
            switch_name = switch_info['ports'][0]['name']
            for topo_switch in self.topo_net.switches:
                if switch_name.startswith(topo_switch.id):
                    self.dpid_to_node[dpid] = topo_switch

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    # Add a flow entry to the flow-table
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # Construct flow_mod message and send it
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    def _is_from_upper_port(self, dpid, in_port):
        return in_port in self._get_upper_ports(dpid)
    
    def _get_upper_ports(self, dpid):
        ports = set()
        links = get_link(self, dpid)
        receiver_type = self.dpid_to_node[dpid].type
        if receiver_type == "es":
            for link in links:
                sender_dpid = link.dst.dpid
                sender_type = self.dpid_to_node[sender_dpid].type
                if sender_type != "h":
                    ports.add(link.src.port_no)
        elif receiver_type == "as":
            for link in links:
                sender_dpid = link.dst.dpid
                sender_type = self.dpid_to_node[sender_dpid].type
                if sender_type == "cs":
                    ports.add(link.src.port_no)
        return ports

    def _get_lower_ports(self, dpid):
        # lower port might connect to host, so cannot use get_link to get
        # because get_link would not show the connection with host
        ports = set()
        switch = get_switch(self, dpid)[0]
        upper_port = self._get_upper_ports(dpid)
        for port in switch.ports:
            if port.port_no not in upper_port:
                ports.add(port.port_no)
        return ports

    def _get_all_ports(self, dpid):
        switch = get_switch(self, dpid)[0]
        ports = {port.port_no for port in switch.ports}
        return ports

    def _get_flood_ports(self, dpid, in_port):
        switch_type = self.dpid_to_node[dpid].type
        print("switch name:", self.dpid_to_node[dpid].id)
        ports = set()
        if switch_type == "cs":
            ports = self._get_lower_ports(dpid)
            ports.remove(in_port)
        elif self._is_from_upper_port(dpid, in_port):
            ports = self._get_lower_ports(dpid)
        else:
            ports = self._get_all_ports(dpid)
            ports.remove(in_port)
            if not self._is_es(dpid):
                next_ports = self._get_next_ports(dpid)
                ports.intersection_update(next_ports)
        return ports
    
    def _is_es(self, dpid):
        return self.dpid_to_node[dpid].type == "es"
    
    def _get_paths(self, dpid):
        start_node = self.dpid_to_node[dpid]
        paths = []
        for node in self.topo_net.edge_switches:
            if node is not start_node:
                paths.append(self.dijkstra_fattree.get_path(start_node, node))
        return paths

    def _get_next_nodes(self, dpid):
        start_node = self.dpid_to_node[dpid]
        paths = self._get_paths(dpid)
        next_nodes = set()
        for path in paths:
            next_nodes.add(path[path.index(start_node) + 1])
        return next_nodes

    def _get_next_ports(self, dpid):
        dpids = tuple(self.dpid_to_node.keys())
        nodes = tuple(self.dpid_to_node.values())
        next_nodes = self._get_next_nodes(dpid)
        next_dpids = set()
        for next_node in next_nodes:
            next_dpids.add(dpids[nodes.index(next_node)])
        next_ports = set()
        links = get_link(self, dpid)
        for link in links:
            if link.dst.dpid in next_dpids:
                next_ports.add(link.src.port_no)
        return next_ports
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)

        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        if arp_pkt:
            # by arp pkt, we can know which port connect to which host
            # 0x0800 means ipv4, 0x0806 means arp package
            if self._is_es(dpid) and not self._is_from_upper_port(dpid, in_port):
                match = parser.OFPMatch(eth_type = ether_types.ETH_TYPE_IP, ipv4_dst = arp_pkt.src_ip)
                actions = [parser.OFPActionOutput(in_port)]
                self.add_flow(datapath, 1, match, actions)

            actions = []
            self.mac_to_port.dpid_add(dpid)
            if not self.mac_to_port.port_get(dpid, haddr_to_bin(arp_pkt.src_mac)):
                match = parser.OFPMatch(eth_type = ether_types.ETH_TYPE_IP, ipv4_dst = arp_pkt.src_ip)
                actions = [parser.OFPActionOutput(in_port)]
                self.add_flow(datapath, 1, match, actions)
                self.mac_to_port.port_add(dpid, in_port, haddr_to_bin(arp_pkt.src_mac))
            out_port = self.mac_to_port.port_get(dpid, haddr_to_bin(arp_pkt.dst_mac))
            if out_port:
                actions.append(parser.OFPActionOutput(out_port))
            else:
                flood_ports = self._get_flood_ports(dpid, in_port)
                for out_port in flood_ports:
                    actions.append(parser.OFPActionOutput(out_port))
            out = parser.OFPPacketOut(
                datapath=datapath,
                in_port=in_port,
                actions=actions,
                buffer_id=datapath.ofproto.OFP_NO_BUFFER,
                data=msg.data
            )
            datapath.send_msg(out)
