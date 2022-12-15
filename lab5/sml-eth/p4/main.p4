#include <core.p4>
#include <v1model.p4>
#include "headers.p4"
#include "types.p4"
#include "aggregate.p4"
#include "config.p4"



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
      sml_eth_type: parse_sml;
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
                    
  /* worker arrive or not */
  register<bit<8>>(1) worker_arrive_reg;

  action worker_arrive() {
    /* record the work have count */
    bit<8> worker_arrive_tmp;
    bit<8> mask = (bit<8>)0xff << hdr.sml.num_workers;
    worker_arrive_reg.read(worker_arrive_tmp, 0);
    worker_arrive_tmp = worker_arrive_tmp | ((bit<8>)1 << hdr.sml.rank);
    if(worker_arrive_tmp | mask == 0xff){
      meta.all_worker_arrive = true;
      /* if all worker arrive, clean register to zero */
      worker_arrive_tmp = 0x00;
    }else{
      meta.all_worker_arrive = false;
    }
    worker_arrive_reg.write(0, worker_arrive_tmp);
  }
  action sml_md_set() {
    meta.curr_elem_idx = 0;
    worker_arrive();
  }
  action drop() {
    mark_to_drop(standard_metadata);
  }
  table sml_ctrl {
    key = {
      hdr.eth.etherType: exact;
    }
    actions = {
      sml_md_set;
      NoAction;
      drop;
    }
    const entries = {
      (sml_eth_type): sml_md_set();
    }
    default_action = NoAction();
  }

  Aggregate() elem00_ctrl;
  Aggregate() elem01_ctrl;
  Aggregate() elem02_ctrl;
  apply {
    sml_ctrl.apply();
    // elem01_ctrl.apply(hdr, 1, hdr.vector.elem01, standard_metadata);
    /* hdr, index, elem_in, std_meta */
    if(hdr.eth.etherType == sml_eth_type){
      elem00_ctrl.apply(hdr.vector.elem00, hdr.vector.elem00, meta, standard_metadata);
      elem01_ctrl.apply(hdr.vector.elem01, hdr.vector.elem01, meta, standard_metadata);
      elem02_ctrl.apply(hdr.vector.elem02, hdr.vector.elem02, meta, standard_metadata);
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