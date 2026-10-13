"""Recover historical experiment inputs; only write exact logged SHA matches."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def save(folder, name, source, expected):
    payload = source.encode('utf-8')
    actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise ValueError(f'{folder}/{name} SHA mismatch: {actual}; bytes={len(payload)}')
    directory = OUT / folder
    directory.mkdir(exist_ok=True)
    target = directory / name
    if target.exists() and target.read_bytes() != payload:
        raise ValueError('do not overwrite different evidence')
    target.write_bytes(payload)
    print('PASS: exact experiment input', folder, name, actual)


def main():
    driver = (ROOT / 'src/pynq_host/c01_capture.py').read_text(encoding='utf-8')
    driver = driver.replace("        self.evidence['identity'] = self.token\n", '')
    begin = driver.index("            self.evidence['buffers'] =")
    end = driver.index('            self.dma.write(CR, 4)\n', begin)
    driver = driver[:begin] + driver[end:]
    begin = driver.index('        failures = []\n')
    end = driver.index("        self.evidence['cleanup']", begin)
    driver = driver[:begin] + '        for b in self.buffers:\n            b.freebuffer()\n        self.closed = True\n' + driver[end:]
    save('config-first', 'c01_capture.py', driver,
         '0d250e3ad6940440934412acf02690fb8d9072dcfeb4c76517069f8d7aae1a7a')
    original = driver.replace('0x101F', '0x1013')
    begin = original.index('            # Stream can be accepted/discarded while halted.')
    end = original.index('            self._check_source()\n', begin)
    original = original[:begin] + original[end:]
    anchor = '            self.dma.write(PARK, self.dma.read(PARK) & ~0x1F00)\n'
    clean = ('            self.dma.write(SR, ERRORS | IRQ | 0x2000)\n'
             '            if self.dma.read(SR) & (ERRORS | IRQ) or self.dma.read(CR) & 1:\n'
             '                raise CaptureError("DMA reset/clear not clean")\n')
    original = original.replace(anchor, clean + anchor)
    save('first', 'c01_capture.py', original,
         '552990318c9fb68b4e74c5c13f5d056a50e6a3a0faf890d9d6d3517ac3b547c1')
    runner = (ROOT / 'sim/scripts/c01_ddr_onboard.py').read_text(encoding='utf-8')
    runner = '\n'.join(line for line in runner.split('\n') if "'runner_sha256':" not in line and "'helper_sha256':" not in line)
    begin = runner.index('        for attempt in (1, 2):\n')
    end = runner.index('        owner = SingleFrameCapture', begin)
    runner = runner[:begin] + '        time.sleep(2)\n        m2_onboard.cmd_smoke()\n' + runner[end:]
    helper = (ROOT / 'sim/scripts/c01_status_onboard.py').read_text(encoding='utf-8')
    for folder in ('first', 'config-first'):
        save(folder, 'c01_ddr_onboard.py', runner,
             'd8c48dfa93a088c1658cdd9009bf6a54f68d762a5afe4772f708baa87903752c')
        save(folder, 'c01_status_onboard.py', helper,
             '894bf7dc01ba9260c48cde7ab0b1aecdd6bfa157f7fa43252170cea1752e1810')


if __name__ == '__main__': main()
