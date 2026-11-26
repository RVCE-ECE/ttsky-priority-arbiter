/*
 * Copyright (c) 2026 Krishna Saini, Shylashree N, RV College of Engineering
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_priority_arbiter_8bit (
    input  wire [7:0] ui_in,    // Dedicated inputs: req[7:0] (bit 0 = highest priority)
    output wire [7:0] uo_out,   // Dedicated outputs: 1-cycle registered grant_oh[7:0]
    input  wire [7:0] uio_in,   // IOs: Input path -> enable_mask[7:0] (1 = enabled, 0 = masked)
    output wire [7:0] uio_out,  // IOs: Output path (unused, tied low)
    output wire [7:0] uio_oe,   // IOs: Enable path (0 = input, tied low)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  wire [7:0] grant_oh;
  wire       any_grant;
  wire [7:0] masked_req;
  wire [2:0] winner_id;
  wire       valid;
  wire       multi_req;

  reg  [7:0] uo_out_reg;

  parallel_prefix_arbiter u_arbiter (
      .req        (ui_in),
      .enable_mask(uio_in),
      .grant_oh   (grant_oh),
      .any_grant  (any_grant),
      .masked_req (masked_req)
  );

  grant_encoder_8to3 u_encoder (
      .grant_oh  (grant_oh),
      .any_grant (any_grant),
      .masked_req(masked_req),
      .winner_id (winner_id),
      .valid     (valid),
      .multi_req (multi_req)
  );

  // Single-cycle deterministic output register with active-low async reset
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      uo_out_reg <= 8'h00;
    end else begin
      uo_out_reg <= grant_oh;
    end
  end

  assign uo_out  = uo_out_reg;
  assign uio_out = 8'b00000000;
  assign uio_oe  = 8'b00000000;

  // Suppress unused signal warnings for ena and internal encoder outputs
  wire _unused = &{ena, winner_id, valid, multi_req, 1'b0};

endmodule
