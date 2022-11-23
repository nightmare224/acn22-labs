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
        self.mac_to_port = {}

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        # Switches and links in the network
        switches = get_switch(self, None)
        links = get_link(self, None)
        # print(len(links))
        # would show ip address
        # print(switches[0].dp.address)
        # for s1 in switches[0].ports:
        #     print(s1.dpid, s1.port_no, s1.hw_addr, s1.name)
        # print(links)
        # print(switches[0].dp.xid, switches[0].dp.id, switches[0].dp.address)
        # for switch in switches:
            # print(switch)


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


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)

        # self.mac_to_port.setdefault(datapath.id, {})

        # add switch to host flow
        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            switch_port= in_port
            host_ip = arp_pkt.src_ip
            # by arp pkt, we can know which port connect to which host
            # 0x0800 means ipv4, 0x0806 means arp package
            match = parser.OFPMatch(eth_type = 0x0800, ipv4_dst = host_ip)
            actions = [parser.OFPActionOutput(switch_port)]
            self.add_flow(datapath, 1, match, actions)
            # print(in_port, arp_pkt.src_ip, arp_pkt.dst_ip)


        
        # print(pkt)
        # change to ipv4 would get ip
        # ip = pkt.get_protocols(ipv4.ipv4)
        # print(ip)
        # print("=========")
        # mac_src = eth.src
        # mac_dst = eth.dst
        # in_port = msg.match['in_port']
        # self.mac_to_port[dpid][mac_src] = in_port

        # # init mac_to_port
        # self.mac_to_port.setdefault(datapath.id, {})
