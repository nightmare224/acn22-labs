#include <core.p4>
#include <v1model.p4>
#include "headers.p4"
#include "types.p4"
#include "aggregate.p4"




parser TheParser(packet_in packet,
                 out headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
  /* TODO: Implement me */
  state start {
    transition parse_ethernet;
  }
  state parse_ethernet {
    packet.extract(hdr.eth);
    transition select(hdr.eth.etherType) {
      0x8787: parse_sml;
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

    // packet.extract(hdr.vector.next);
    // transition select(hdr.vector.last.bos) {
    //   0: parse_vector;
    //   1: accept;
    // }
  }
}

control TheIngress(inout headers hdr,
                   inout metadata meta,
                   inout standard_metadata_t standard_metadata) {
                    

  // register<bit<32>>(1) reg;
  // action sml_aggr() {
  //   // bit<32> elem_tmp
  //   standard_metadata.mcast_grp = 1;
  // }
  // table sml_table {
  //   key = {
  //     hdr.eth.etherType: exact;

  //   }
  //   actions = {
  //     sml_aggr;
  //   }
  //   size = 1024;
  //   default_action = sml_aggr();
  // }
  action drop() {
      mark_to_drop(standard_metadata);
  }
  table sml_ctrl {
    key = {
      hdr.eth.etherType: exact;
    }
    actions = {
      NoAction;
      drop();
    }
    const entries = {
      (0x8787): NoAction();
    }
    default_action = drop();
  }

  Aggregate() elem00_ctrl;
  Aggregate() elem01_ctrl;
  Aggregate() elem02_ctrl;
  apply {
    // sml_table.apply();
    // elem01_ctrl.apply(hdr, 1, hdr.vector.elem01, standard_metadata);
    /* hdr, index, elem_in, std_meta */
    if(hdr.eth.etherType == 0x8787){
      elem00_ctrl.apply(hdr.sml.curr_elem_idx, hdr.vector.elem00, hdr.vector.elem00, standard_metadata);
      elem01_ctrl.apply(hdr.sml.curr_elem_idx, hdr.vector.elem01, hdr.vector.elem01, standard_metadata);
      elem02_ctrl.apply(hdr.sml.curr_elem_idx, hdr.vector.elem02, hdr.vector.elem02, standard_metadata);
    }

  }
}

control TheEgress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
  apply {
    /* TODO: Implement me (if needed) */
  }
}

control TheChecksumVerification(inout headers hdr, inout metadata meta) {
  apply {
    /* TODO: Implement me (if needed) */
  }
}

control TheChecksumComputation(inout headers  hdr, inout metadata meta) {
  apply {
    /* TODO: Implement me (if needed) */
  }
}

control TheDeparser(packet_out packet, in headers hdr) {
  apply {
    packet.emit(hdr.eth);
    packet.emit(hdr.sml);
    packet.emit(hdr.vector);
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