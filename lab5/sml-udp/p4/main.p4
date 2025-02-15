#include <core.p4>
#include <v1model.p4>

#include "headers.p4"
#include "config.p4"
#include "arp.p4"
#include "aggregate.p4"

parser TheParser(packet_in packet,
                 out headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
  state start {
    transition parse_ethernet;
  }
  state parse_ethernet {
    packet.extract(hdr.eth);
    transition select(hdr.eth.etherType){
      0x0806: parse_arp;
      0x0800: parse_ipv4;
      default: accept;
    }
  }
  state parse_arp {
    packet.extract(hdr.arp);
    transition select(hdr.arp.ptype){
      0x0800: parse_arp_ipv4;
      default: accept;
    }
  }
  state parse_arp_ipv4 {
    packet.extract(hdr.arp_ipv4);
    transition accept;
  }

  state parse_ipv4 {
    packet.extract(hdr.ipv4);
    transition select(hdr.ipv4.protocol) {
      0x11: parse_udp;
      default: accept;
    }
  }
  state parse_udp {
    packet.extract(hdr.udp);
    /* if destination is 38787 means it is from switch ml */
    transition select(hdr.udp.dstPort) {
      sml_udp_port: parse_sml;
      default: accept;
    }
  }
  state parse_sml {
    packet.extract(hdr.sml);
    transition parse_vector;
  }
  state parse_vector {
    packet.extract(hdr.vector);
    transition accept;
  }
}

control TheIngress(inout headers hdr,
                   inout metadata meta,
                   inout standard_metadata_t standard_metadata) {
  /* worker arrive or not */
  register<bit<8>>(1) worker_arrive_reg;

  action worker_arrive() {
    /* record the work have count */
    bit<8> worker_arrive_tmp;
    bit<8> mask = (bit<8>)0xff << hdr.sml.num_workers;
    worker_arrive_reg.read(worker_arrive_tmp, 0);
    worker_arrive_tmp = worker_arrive_tmp | ((bit<8>)1 << hdr.sml.rank);
    if (worker_arrive_tmp | mask == 0xff) {
      meta.all_worker_arrive = true;
      /* if all worker arrive, clean register to zero */
      worker_arrive_tmp = 0x00;
    } else {
      meta.all_worker_arrive = false;
    }
    worker_arrive_reg.write(0, worker_arrive_tmp);
  }
  action sml_md_set() {
    meta.elem_idx = 0;
    worker_arrive();
  }
  table sml_ctrl {
    actions = {
      sml_md_set;
    }
    default_action = sml_md_set();
  }

  ARP() arp;
  Aggregate() elem00_ctrl;
  Aggregate() elem01_ctrl;
  Aggregate() elem02_ctrl;
  Aggregate() elem03_ctrl;
  Aggregate() elem04_ctrl;
  Aggregate() elem05_ctrl;
  Aggregate() elem06_ctrl;
  Aggregate() elem07_ctrl;
  Aggregate() elem08_ctrl;
  Aggregate() elem09_ctrl;
  Aggregate() elem10_ctrl;
  Aggregate() elem11_ctrl;
  Aggregate() elem12_ctrl;
  Aggregate() elem13_ctrl;
  Aggregate() elem14_ctrl;
  Aggregate() elem15_ctrl;
  Aggregate() elem16_ctrl;
  Aggregate() elem17_ctrl;
  Aggregate() elem18_ctrl;
  Aggregate() elem19_ctrl;
  Aggregate() elem20_ctrl;
  Aggregate() elem21_ctrl;
  Aggregate() elem22_ctrl;
  Aggregate() elem23_ctrl;
  Aggregate() elem24_ctrl;
  Aggregate() elem25_ctrl;
  Aggregate() elem26_ctrl;
  Aggregate() elem27_ctrl;
  Aggregate() elem28_ctrl;
  Aggregate() elem29_ctrl;
  Aggregate() elem30_ctrl;
  Aggregate() elem31_ctrl;
  apply {
    if(hdr.arp.isValid()){
      arp.apply(hdr, standard_metadata);
    }
    if (hdr.sml.isValid()) {
      @atomic{
        sml_ctrl.apply();
      }
      elem00_ctrl.apply(hdr.vector.elem00, hdr.vector.elem00, meta, standard_metadata);
      elem01_ctrl.apply(hdr.vector.elem01, hdr.vector.elem01, meta, standard_metadata);
      elem02_ctrl.apply(hdr.vector.elem02, hdr.vector.elem02, meta, standard_metadata);
      elem03_ctrl.apply(hdr.vector.elem03, hdr.vector.elem03, meta, standard_metadata);
      elem04_ctrl.apply(hdr.vector.elem04, hdr.vector.elem04, meta, standard_metadata);
      elem05_ctrl.apply(hdr.vector.elem05, hdr.vector.elem05, meta, standard_metadata);
      elem06_ctrl.apply(hdr.vector.elem06, hdr.vector.elem06, meta, standard_metadata);
      elem07_ctrl.apply(hdr.vector.elem07, hdr.vector.elem07, meta, standard_metadata);
      elem08_ctrl.apply(hdr.vector.elem08, hdr.vector.elem08, meta, standard_metadata);
      elem09_ctrl.apply(hdr.vector.elem09, hdr.vector.elem09, meta, standard_metadata);
      elem10_ctrl.apply(hdr.vector.elem10, hdr.vector.elem10, meta, standard_metadata);
      elem11_ctrl.apply(hdr.vector.elem11, hdr.vector.elem11, meta, standard_metadata);
      elem12_ctrl.apply(hdr.vector.elem12, hdr.vector.elem12, meta, standard_metadata);
      elem13_ctrl.apply(hdr.vector.elem13, hdr.vector.elem13, meta, standard_metadata);
      elem14_ctrl.apply(hdr.vector.elem14, hdr.vector.elem14, meta, standard_metadata);
      elem15_ctrl.apply(hdr.vector.elem15, hdr.vector.elem15, meta, standard_metadata);
      elem16_ctrl.apply(hdr.vector.elem16, hdr.vector.elem16, meta, standard_metadata);
      elem17_ctrl.apply(hdr.vector.elem17, hdr.vector.elem17, meta, standard_metadata);
      elem18_ctrl.apply(hdr.vector.elem18, hdr.vector.elem18, meta, standard_metadata);
      elem19_ctrl.apply(hdr.vector.elem19, hdr.vector.elem19, meta, standard_metadata);
      elem20_ctrl.apply(hdr.vector.elem20, hdr.vector.elem20, meta, standard_metadata);
      elem21_ctrl.apply(hdr.vector.elem21, hdr.vector.elem21, meta, standard_metadata);
      elem22_ctrl.apply(hdr.vector.elem22, hdr.vector.elem22, meta, standard_metadata);
      elem23_ctrl.apply(hdr.vector.elem23, hdr.vector.elem23, meta, standard_metadata);
      elem24_ctrl.apply(hdr.vector.elem24, hdr.vector.elem24, meta, standard_metadata);
      elem25_ctrl.apply(hdr.vector.elem25, hdr.vector.elem25, meta, standard_metadata);
      elem26_ctrl.apply(hdr.vector.elem26, hdr.vector.elem26, meta, standard_metadata);
      elem27_ctrl.apply(hdr.vector.elem27, hdr.vector.elem27, meta, standard_metadata);
      elem28_ctrl.apply(hdr.vector.elem28, hdr.vector.elem28, meta, standard_metadata);
      elem29_ctrl.apply(hdr.vector.elem29, hdr.vector.elem29, meta, standard_metadata);
      elem30_ctrl.apply(hdr.vector.elem30, hdr.vector.elem30, meta, standard_metadata);
      elem31_ctrl.apply(hdr.vector.elem31, hdr.vector.elem31, meta, standard_metadata);
    }
  }
}

control TheEgress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
  action sml_udp_send(ipv4_addr_t ip_sw, ipv4_addr_t ip_hst, mac_addr_t mac_sw, mac_addr_t mac_hst) {
    hdr.ipv4.srcAddr = ip_sw;
    hdr.ipv4.dstAddr = ip_hst;
    hdr.eth.srcAddr = mac_sw;
    hdr.eth.dstAddr = mac_hst;
  }
  table tbl_sml_udp {
    actions = {
      sml_udp_send();
      NoAction();
    }
    key = {
      standard_metadata.egress_port: exact;
    }
    size = 8;
    default_action = NoAction();
  }
  apply {
    if(hdr.udp.isValid() && hdr.sml.isValid()){
      tbl_sml_udp.apply();
    }
  }
}

control TheChecksumVerification(inout headers hdr, inout metadata meta) {
  apply {
    /* no need is this level, would need in level 3*/
  }
}

control TheChecksumComputation(inout headers  hdr, inout metadata meta) {
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
    update_checksum(
      hdr.sml.isValid(),
      { 
        hdr.ipv4.srcAddr,
        hdr.ipv4.dstAddr,
        (bit<8>)0x00,
        hdr.ipv4.protocol,
        hdr.udp.length,
        hdr.udp.srcPort,
        hdr.udp.dstPort,
        hdr.udp.length,
        hdr.sml,
        hdr.vector
      },
      hdr.udp.checksum,
      HashAlgorithm.csum16
    );
  }
}

control TheDeparser(packet_out packet, in headers hdr) {
  apply {
    packet.emit(hdr);
  }
}

V1Switch(
  TheParser(),
  TheChecksumVerification(),
  TheIngress(),
  TheEgress(),
  TheChecksumComputation(),
  TheDeparser()
) main;