/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>


/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

header ethernet_t {
    bit<48> dstAddr;    //mac
    bit<48> srcAddr;
    bit<16> etherType;
}

header ipv4_t {
    bit<4> version;
    bit<4> ihl;
    bit<8> typeOfService;
    bit<16> totalLength;
    bit<16> identification;
    bit<3> flags;
    bit<13> fragmentOffset;
    bit<8> ttl; //time to live
    bit<8> protocol;
    bit<16> hdrChecksum; // header checksum
    bit<32> srcAddr;
    bit<32> dstAddr;    //ipv4
}

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> totalLength;
    bit<16> checksum;
}

struct metadata {
    /* empty */
}

struct headers {
    ethernet_t  ethernet;
    ipv4_t  ipv4;
    udp_t   udp;        
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }
    // ethernet header would be first
    state parse_ethernet {
        // choose to parse which field of header
        packet.extract(hdr.ethernet);
        transition parse_ipv4;
    }
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            17: parse_udp;
            default: accept;
        }
    }
    state parse_udp {
        packet.extract(hdr.udp);
        transition accept;
    }
}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {   
    apply {
    }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    
    action ipv4_forward(bit<48> dstAddr, bit<9> port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
    action multicast() {
        standard_metadata.mcast_grp = 1;
    }
    action drop() {
        mark_to_drop(standard_metadata);
    }
    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            multicast;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }
    apply {
        ipv4_lpm.apply();
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    action update_dest(bit<48> dstMacAddr, bit<32> dstIpAddr) {
        hdr.ethernet.dstAddr = dstMacAddr;
        hdr.ipv4.dstAddr = dstIpAddr;
        hdr.udp.checksum = 0;
        // hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
    }
    table multicast_table {
        //the key is useless, just want to always make checksum 0
        key = {
            standard_metadata.egress_rid: exact;
            standard_metadata.egress_port: exact;
        }
        actions = {
            update_dest;
            NoAction;
        }
        size = 1024;
        default_action = NoAction;
    }
    apply {
        if(hdr.udp.isValid()){
            multicast_table.apply();
        }
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
    apply {
        update_checksum(
            hdr.ipv4.isValid(),
            { 
                hdr.ipv4.version,
                hdr.ipv4.ihl,
                hdr.ipv4.typeOfService,
                hdr.ipv4.totalLength,
                hdr.ipv4.identification,
                hdr.ipv4.flags,
                hdr.ipv4.fragmentOffset,
                hdr.ipv4.ttl,
                hdr.ipv4.protocol,
                hdr.ipv4.srcAddr,
                hdr.ipv4.dstAddr
            },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16
        );
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
