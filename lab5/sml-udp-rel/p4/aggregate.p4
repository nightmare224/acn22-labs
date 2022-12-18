
#ifndef _AGGREGATE_H
#define _AGGREGATE_H

#include "headers.p4"
#include "types.p4"


control Aggregate(in elem_t elem_in,
                  out elem_t elem_out,
                  in bit<8> chunk_id,
                  in bit<8> rank,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

  register<bit<32>>(64) elem_sum_reg;
  //TODO: may be move the current_elem_in to inout, so it access by next stage
  
  action broadcast() {
    standard_metadata.mcast_grp = 1;
  }
  action unicast() {
    standard_metadata.egress_spec = standard_metadata.ingress_port;
  }
  action aggr() {
    bit<32> elem_tmp = 0;
    bit<32> elem_base_idx = chunk_size & chunk_id;

    if(meta.opcode == 1){
      unicast();
    }else if(meta.opcode == 0){
      /* read the data from register */
      elem_sum_reg.read(elem_tmp, meta.elem_idx + elem_base_idx);
      /* aggregate current value and register value */
      elem_tmp = elem_tmp + elem_in;
      /* update new value to header (not nessesary if it is not last worker) */
      elem_out = elem_tmp;
      if (meta.worker_arrival[chunk_id].all_worker_arrive) {
        /* clean register to zero if it is last arrived worker */
        elem_tmp = 0;
        /* and then broadcast the modified packet to all worker */
        broadcast();
      }
      /* write new value to register */
      elem_sum_reg.write(meta.elem_idx + elem_base_idx, elem_tmp);
    }
    /* plus 1 before go to next stage */
    meta.elem_idx = meta.elem_idx + 1;
  }
  table tbl_aggr {
    actions = {
      aggr();
    }
    default_action = aggr();
  }

  apply {
    @atomic {
      tbl_aggr.apply();
    }
  }
}


#endif