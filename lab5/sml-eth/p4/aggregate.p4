
#ifndef _AGGREGATE_H
#define _AGGREGATE_H

#include "headers.p4"
#include "types.p4"


control Aggregate(inout headers hdr, 
                  // in bit<32> index, 
                  in elem_t elem_in, 
                  inout standard_metadata_t standard_metadata/*, out elem_t elem_out*/){

  register<bit<32>>(2) reg;
  action aggr(bit<32> elem_idx) {
    bit<32> elem_tmp = 0;
    if(elem_idx==0){
      // reg.read(elem_tmp, elem_idx); /* condition not support */
      /* should change to elem_in */
      elem_tmp = elem_tmp + hdr.vector.elem00 + 16;
      // reg.write(elem_tmp, elem_idx); /* condition not support */
      /* should check if all worker done the write */
      hdr.vector.elem00 = elem_tmp;
      // hdr.vector.elem00 = 16;
    }else if(elem_idx==1){
      // reg.read(elem_tmp, elem_idx); /* condition not support */
      elem_tmp = elem_tmp + hdr.vector.elem01 + 32;
      // reg.write(elem_tmp, elem_idx); /* condition not support */
      /* should check if all worker done the write */
      hdr.vector.elem01 = elem_tmp;
      // hdr.vector.elem01 = 32;
    }
    /* plus 1 before go to next stage */
    hdr.sml.curr_elem_idx = hdr.sml.curr_elem_idx + 1;
    standard_metadata.mcast_grp = 1;
  }
  table sum {
    key = {
      hdr.sml.curr_elem_idx: exact;
    }
    actions = {
      aggr;
      NoAction;
    }
    // size = 20;
    const entries = {
      /* do aggregate on reg[idx] based on key(curr_elem_idx) */
      (0): aggr(0);
      (1): aggr(1);
    }
    default_action = NoAction();
  }
  apply {
    sum.apply();
  }
}


#endif