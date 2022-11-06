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


from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
# from ryu.lib.packet import ipv4
# from ryu.lib.packet import arp

class LearningSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(LearningSwitch, self).__init__(*args, **kwargs)

        # Initialize mac address table
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Initial flow entry for matching misses
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

    def is_arp(self, protocols):
        for p in protocols:
            if hasattr(p, 'protocol_name'):
                # print(p.protocol_name)
                if 'arp' == p.protocol_name:
                    return True
        return False

    # Handle the packet_in event
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        
        msg = ev.msg
        # print(msg)
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser


        # init mac_to_port
        self.mac_to_port.setdefault(datapath.id, {})

        # store path in to table
        pkt = packet.Packet(msg.data)

        eth = pkt.get_protocols(ethernet.ethernet)[0]
        mac_src = eth.src
        mac_dst = eth.dst
        dpid = datapath.id
        in_port = msg.match['in_port']
        if not self.is_arp(pkt.protocols):
            # update in mac table if it is not related to arp
            self.mac_to_port[dpid][mac_src] = in_port

        # if not found then broadcast to every port
        if mac_dst not in self.mac_to_port[dpid]:
            out_port = ofproto.OFPP_FLOOD
        else:
            out_port = self.mac_to_port[dpid][mac_dst]
        # print(self.mac_to_port)
        actions = [parser.OFPActionOutput(out_port)]

        # install flow (why need this part??)
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port = in_port, eth_dst = mac_dst)
            # match = parser.OFPMatch(in_port = in_port, eth_dst = mac_dst, eth_src = mac_src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)

        # Construct packet_out message and send it
        out = parser.OFPPacketOut(datapath=datapath,
                                  in_port=in_port, 
                                  actions=actions, 
                                  buffer_id=msg.buffer_id, # datapath.ofproto.OFP_NO_BUFFER
                                  data=msg.data)
        datapath.send_msg(out)
