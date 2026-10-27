#!/usr/bin/env python3
"""Load the deployed vision overlay and wait once for video to settle."""
import sys


def main():
    sys.path.insert(0, "/home/xilinx/vision_m2")
    import m2_onboard
    from vision_regs import VisionRegs

    m2_onboard.cmd_load()
    vision = VisionRegs(base=m2_onboard.AXI_REGS_BASE)
    vision.apply_preset("GRAY")
    sequence = vision.commit(wait=False)
    # A single outstanding commit remains valid while HDMI locks after boot.
    vision.wait_applied(sequence, timeout=30.0, poll=0.02)
    print(f"VISION_BOOT_PASS applied_config_id={sequence}", flush=True)


if __name__ == "__main__":
    main()
