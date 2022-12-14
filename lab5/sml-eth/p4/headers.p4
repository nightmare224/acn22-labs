#ifndef _HEADERS_H
#define _HEADERS_H

#include "types.p4"

header ethernet_h {
  bit<48> dstAddr;
  bit<48> srcAddr;
  bit<16> etherType;
}

header sml_h {
  /* TODO: Define me */
  bit<8> rank;
  bit<8> chuck_size;
  bit<32> curr_elem_idx;
  // bit<128> vector;
}

header elem_h {
  // elem_t[32] elem;
  elem_t elem;
  bit<8> bos;   /* bottom of stack */
  // bit<32> elem00;
  // bit<32> elem01;
}

struct headers {
  ethernet_h eth;
  sml_h sml;
  elem_h[32] vector;
}

struct metadata { 
  // bit<32> curr_elem_in;
}

#endif