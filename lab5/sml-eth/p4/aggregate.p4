
#ifndef _AGGREGATE_H
#define _AGGREGATE_H

#include "headers.p4"
#include "types.p4"


control Aggregate(in elem_t elem_in,
                  out elem_t elem_out, 
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata){

  register<bit<32>>(32) reg;
  //TODO: may be move the current_elem_in to inout, so it access by next stage
  action aggr(bit<32> elem_idx) {
    bit<32> elem_tmp = 0;

    
    /* read the data from register */
    reg.read(elem_tmp, elem_idx);
    /* aggregate current value and register value */
    elem_tmp = elem_tmp + elem_in;
    /* write new value to register */
    reg.write(elem_idx, elem_tmp);
    /* write new value to header (Should only be write if all worker do it, should remove this part ) */
    elem_out = elem_tmp;


    /* plus 1 before go to next stage */
    meta.curr_elem_idx = meta.curr_elem_idx + 1;
    standard_metadata.mcast_grp = 1;
  }
  table sum {
    key = {
      meta.curr_elem_idx: exact;
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
      (2): aggr(2);
    }
    default_action = NoAction();
  }
  apply {
    sum.apply();
  }
}


#endif