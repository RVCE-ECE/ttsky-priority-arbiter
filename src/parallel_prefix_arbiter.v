/*
 * Copyright (c) 2026 Krishna Saini, Shylashree N, RV College of Engineering
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// 8-bit fixed-priority arbiter (Channel 0 = highest, Channel 7 = lowest)
// using dynamic enable masking and a 3-stage Kogge-Stone parallel-prefix OR tree.
module parallel_prefix_arbiter (
    input  wire [7:0] req,
    input  wire [7:0] enable_mask,
    output wire [7:0] grant_oh,
    output wire       any_grant,
    output wire [7:0] masked_req
);

  // Apply active-high channel enable mask
  assign masked_req = req & enable_mask;

  // 3-stage parallel-prefix OR tree over masked_req:
  // p3[i] = OR_{j=0}^{i} masked_req[j]
  wire [7:0] p0;
  wire [7:0] p1;
  wire [7:0] p2;
  wire [7:0] p3;

  assign p0 = masked_req;

  // Stage 1: pairwise prefix ORs (stride 1)
  assign p1[0]   = p0[0];
  assign p1[7:1] = p0[7:1] | p0[6:0];

  // Stage 2: stride-2 prefix ORs
  assign p2[1:0] = p1[1:0];
  assign p2[7:2] = p1[7:2] | p1[5:0];

  // Stage 3: stride-4 prefix ORs
  assign p3[3:0] = p2[3:0];
  assign p3[7:4] = p2[7:4] | p2[3:0];

  // Prefix disable vector: high when any higher-priority channel (0..i-1) is active
  wire [7:0] higher_req_active;
  assign higher_req_active = {p3[6:0], 1'b0};

  // One-hot grant: channel i wins iff it is unmasked-active and no higher channel is active
  assign grant_oh  = masked_req & ~higher_req_active;
  assign any_grant = p3[7];

endmodule
