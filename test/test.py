# SPDX-FileCopyrightText: © 2026 Krishna Saini, Shylashree N, RV College of Engineering
# SPDX-License-Identifier: Apache-2.0

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer


def expected_grant(req: int, mask: int) -> int:
    """Golden reference: lowest-index unmasked active bit wins (channel 0 highest)."""
    masked = (req & mask) & 0xFF
    if masked == 0:
        return 0
    return masked & -masked


def expected_encoder(req: int, mask: int):
    """Golden reference for 8-to-3 encoder outputs (winner_id, valid, multi_req)."""
    masked = (req & mask) & 0xFF
    if masked == 0:
        return 0, 0, 0
    grant = masked & -masked
    winner_id = (grant.bit_length() - 1)
    valid = 1
    multi_req = 1 if (masked & (masked - 1)) != 0 else 0
    return winner_id, valid, multi_req


async def apply_and_check_single_cycle(dut, req: int, mask: int) -> None:
    """Apply (req, mask), advance exactly 1 clock cycle, and verify outputs."""
    dut.ui_in.value = req & 0xFF
    dut.uio_in.value = mask & 0xFF
    await ClockCycles(dut.clk, 1)
    await Timer(1, unit="ns")

    exp_g = expected_grant(req, mask)
    got_g = int(dut.uo_out.value)
    assert got_g == exp_g, (
        f"Single-cycle mismatch for req=0b{req:08b}, mask=0b{mask:08b}: "
        f"expected uo_out=0b{exp_g:08b}, got 0b{got_g:08b}"
    )
    assert int(dut.uio_oe.value) == 0, f"uio_oe must be 0x00, got 0x{int(dut.uio_oe.value):02X}"
    assert int(dut.uio_out.value) == 0, f"uio_out must be 0x00, got 0x{int(dut.uio_out.value):02X}"

    # Verify internal encoder outputs in RTL simulation (skip in flat gate-level netlist)
    if hasattr(dut.user_project, "u_encoder"):
        exp_id, exp_val, exp_multi = expected_encoder(req, mask)
        enc = dut.user_project.u_encoder
        assert int(enc.winner_id.value) == exp_id, (
            f"winner_id mismatch: expected {exp_id}, got {int(enc.winner_id.value)}"
        )
        assert int(enc.valid.value) == exp_val, (
            f"valid mismatch: expected {exp_val}, got {int(enc.valid.value)}"
        )
        assert int(enc.multi_req.value) == exp_multi, (
            f"multi_req mismatch: expected {exp_multi}, got {int(enc.multi_req.value)}"
        )


@cocotb.test()
async def test_priority_arbiter_single_cycle(dut):
    dut._log.info("Start single-cycle 8-bit parallel-prefix priority arbiter verification")

    # 10 us period (100 KHz) matching Tiny Tapeout testbench convention
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # 1. Reset & zero-request state (drive active requests while in reset to verify reset dominates)
    dut.ena.value = 1
    dut.ui_in.value = 0xFF
    dut.uio_in.value = 0xFF
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    await Timer(1, unit="ns")
    assert int(dut.uo_out.value) == 0, f"Reset failed: uo_out=0x{int(dut.uo_out.value):02X}"

    # Release reset with zero requests
    dut.ui_in.value = 0x00
    dut.uio_in.value = 0xFF
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    await Timer(1, unit="ns")
    assert int(dut.uo_out.value) == 0, "Zero-request state must output 0x00"

    # Zero-request check across representative masks
    for mask in (0x00, 0x01, 0x55, 0xAA, 0xF0, 0x0F, 0xFF):
        await apply_and_check_single_cycle(dut, 0x00, mask)

    # 2. Unmasked walking-1s (every channel 0..7 individually)
    dut._log.info("Testing unmasked walking-1s across channels 0..7")
    for ch in range(8):
        await apply_and_check_single_cycle(dut, 1 << ch, 0xFF)

    # Simultaneous multi-channel priority resolution
    dut._log.info("Testing simultaneous multi-channel priority resolution")
    for req in (0xFF, 0xA8, 0xC0, 0xFE, 0xF0, 0x80, 0x55, 0xAA, 0x81):
        await apply_and_check_single_cycle(dut, req, 0xFF)

    # 3. Masked high-priority requests -> immediate 1-cycle transfer to highest unmasked requester
    dut._log.info("Testing dynamic masking with high-priority requests blocked")
    # Channels 0,1,2,5,7 request; mask out 0..2 -> channel 5 wins in 1 cycle
    await apply_and_check_single_cycle(dut, 0b1010_0111, 0b1111_1000)
    # Also mask channel 5 -> channel 7 wins in 1 cycle
    await apply_and_check_single_cycle(dut, 0b1010_0111, 0b1101_1000)
    # Re-enable channel 1 -> channel 1 immediately wins in 1 cycle
    await apply_and_check_single_cycle(dut, 0b1010_0111, 0b1101_1010)

    # 4. Full masking lockout
    dut._log.info("Testing full masking lockout")
    await apply_and_check_single_cycle(dut, 0xFF, 0x00)
    await apply_and_check_single_cycle(dut, 0xA5, 0x00)

    # 5. Exhaustive corner & randomized 1-cycle sweep (768+ vectors)
    dut._log.info("Running 768-vector single-cycle randomized + corner sweep")
    rng = random.Random(20261126)

    # All 256 requests with full enable mask (256 vectors)
    for req in range(256):
        await apply_and_check_single_cycle(dut, req, 0xFF)

    # 512 deterministic random (req, enable_mask) pairs
    for _ in range(512):
        req = rng.randint(0, 255)
        mask = rng.randint(0, 255)
        await apply_and_check_single_cycle(dut, req, mask)

    dut._log.info("All single-cycle priority arbiter tests passed (799+ vectors).")
