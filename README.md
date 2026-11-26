![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# 8-Bit Parallel-Prefix Priority Arbiter with Dynamic Masking & Grant Encoder

- [Read the full project documentation](docs/info.md)

## Overview

This Tiny Tapeout SKY130 project implements a **Single-Cycle 8-Bit Parallel-Prefix Priority Arbiter with Dynamic Enable Masking and an 8-to-3 Grant Encoder**, targeting a **`1x1` SKY130 tile** (`~167 × 108 µm`) on the **`TTSKY26e`** shuttle.

### Key Features
- **Deterministic 1-Cycle Latency:** Every request/mask combination resolves to a registered, glitch-free one-hot grant on `uo_out[7:0]` in exactly **1 clock cycle** (`posedge clk`, active-low `rst_n`).
- **3-Stage Kogge-Stone Parallel-Prefix OR Tree:** Eliminates $O(N)$ ripple priority chains in `src/parallel_prefix_arbiter.v` (Channel `0` = highest priority, Channel `7` = lowest).
- **Dynamic Channel Masking:** `uio_in[7:0]` provides an active-high per-channel `enable_mask[7:0]` with all bidirectional output enables (`uio_oe`) tied to `8'h00`.
- **8-to-3 Binary Grant Encoder:** `src/grant_encoder_8to3.v` computes the 3-bit `winner_id`, `valid`, and contention flag `multi_req`.

## Repository Structure
- `src/project.v` — Top-level Tiny Tapeout wrapper (`tt_um_priority_arbiter_8bit`)
- `src/parallel_prefix_arbiter.v` — 8-bit masked parallel-prefix arbiter
- `src/grant_encoder_8to3.v` — Combinational 8-to-3 grant encoder
- `test/test.py`, `test/tb.v`, `test/Makefile` — Single-cycle `cocotb` verification suite
- `info.yaml` — Tiny Tapeout project metadata and pinout
- `docs/info.md` — Datasheet and testing guide


## Running Simulation Locally

```sh
cd test
make -B
```

## Acknowledgments

We sincerely acknowledge the **Center of Excellence (CoE) in Integrated Circuits and Systems (ICAS)** and the **Department of Electronics and Communication Engineering (ECE), RV College of Engineering (RVCE)** for providing the resources and guidance for this Tiny Tapeout submission.
