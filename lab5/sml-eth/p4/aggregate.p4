
#ifndef _AGGREGATE_H
#define _AGGREGATE_H

#include "headers.p4"
#include "types.p4"


control Aggregate(in elem_t elem_in,
                  out elem_t elem_out, 
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

  register<bit<32>>(32) elem_sum_reg;
  //TODO: may be move the current_elem_in to inout, so it access by next stage
  action broadcast() {
    standard_metadata.mcast_grp = 1;
  }
  action aggr(bit<32> elem_idx) {
    bit<32> elem_tmp = 0;

    /* read the data from register */
    elem_sum_reg.read(elem_tmp, elem_idx);
    /* aggregate current value and register value */
    elem_tmp = elem_tmp + elem_in;
    /* write new value to header (Should only be write if all worker do it, should remove this part ) */
    elem_out = elem_tmp;

    if (meta.all_worker_arrive) {
      /* clean register to zero if it is last arrived worker */
      elem_tmp = 0;
      broadcast();
    }
    /* write new value to register */
    elem_sum_reg.write(elem_idx, elem_tmp);

    /* plus 1 before go to next stage */
    meta.curr_elem_idx = meta.curr_elem_idx + 1;
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
      (3): aggr(3);
      (4): aggr(4);
      (5): aggr(5);
      (6): aggr(6);
      (7): aggr(7);
      (8): aggr(8);
      (9): aggr(9);
      (10): aggr(10);
      (11): aggr(11);
      (12): aggr(12);
      (13): aggr(13);
      (14): aggr(14);
      (15): aggr(15);
      (16): aggr(16);
      (17): aggr(17);
      (18): aggr(18);
      (19): aggr(19);
      (20): aggr(20);
      (21): aggr(21);
      (22): aggr(22);
      (23): aggr(23);
      (24): aggr(24);
      (25): aggr(25);
      (26): aggr(26);
      (27): aggr(27);
      (28): aggr(28);
      (29): aggr(29);
      (30): aggr(30);
      (31): aggr(31);
    }
    default_action = NoAction;
  }
  apply {
    sum.apply();
  }
}


#endif