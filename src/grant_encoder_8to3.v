/*
 * Copyright (c) 2026 Krishna Saini, Shylashree N, RV College of Engineering
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

// Purely combinational 8-to-3 binary grant encoder with valid and
// multi-request contention detection.
module grant_encoder_8to3 (
    input  wire [7:0] grant_oh,
    input  wire       any_grant,
    input  wire [7:0] masked_req,
    output wire [2:0] winner_id,
    output wire       valid,
    output wire       multi_req
);

  assign winner_id[0] = grant_oh[1] | grant_oh[3] | grant_oh[5] | grant_oh[7];
  assign winner_id[1] = grant_oh[2] | grant_oh[3] | grant_oh[6] | grant_oh[7];
  assign winner_id[2] = grant_oh[4] | grant_oh[5] | grant_oh[6] | grant_oh[7];

  assign valid     = any_grant;
  assign multi_req = |(masked_req & (masked_req - 8'd1));

  // Channel 0 encodes to 3'b000, so grant_oh[0] is not directly used in winner_id
  wire _unused = &{grant_oh[0], 1'b0};

endmodule
