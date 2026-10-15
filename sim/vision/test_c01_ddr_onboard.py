"""End-to-end surrogate for the shipped c01_ddr_onboard main. No board, no camera, no PL.

The entry module is imported once with every hardware dependency replaced by a stateful fake, so
the shipped control flow (identity checks, PNG round-trip, UNSAFE-STOP hold, restore) really runs.
"""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import types
import unittest
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FAKE = ROOT / 'sim/build/vision/python/onboard-fake'
ENTRY = ROOT / 'sim/scripts/c01_ddr_onboard.py'
BOARD = FAKE / 'c01-board'
BOARD_FILES = {'c01_capture.py', 'c01_status_onboard.py', 'c01_park_capture.py',
               'ddr-result.json', 'custom-ddr.png'}
HOST_SOURCES = {'c01_capture.py', 'c01_park_capture.py'}
DRIVER_SHA256 = '1f11aefdc11805387b0c345583828fd733e5e38b0b0e043b0510808f648e8430'
sys.path.insert(0, str(ROOT / 'src/pynq_host'))
sys.path.insert(0, str(ROOT / 'sim/vision'))
from test_c01_capture import Rig
from c01_capture import QUARANTINE, CR, RUN, SingleFrameCapture

STATE = {'rig': None, 'events': [], 'cv2': 'ok', 'novideo': (), 'shots': 0, 'stored': {},
         'pl_bitfile': '/home/xilinx/vision_m2/vision.bit'}


class KeepAlive(Exception):
    """Raised by the fake clock once the UNSAFE-STOP hold loop has been observed."""


class FakeTime:
    def __init__(self, stop_after=None):
        self.sleeps, self.stop_after = [], stop_after
    def sleep(self, seconds):
        self.sleeps.append(seconds)
        if seconds == 1 and self.stop_after and self.sleeps.count(1) >= self.stop_after:
            raise KeepAlive()


class FakePath:
    """Maps board absolute paths and entry outputs onto sim/build/vision/python/onboard-fake."""
    def __init__(self, *parts): self._p = Path(*parts)
    def _map(self):
        s = self._p.as_posix()
        if s == '/proc/sys/kernel/random/boot_id': return FAKE / 'boot_id'
        if s == '/home/xilinx/vision_m2': return FAKE / 'vision_m2'
        if s.startswith('/home/xilinx/vision_m2/'): return FAKE / 'vision_m2' / s.split('/', 4)[-1]
        if self._p.parent == ENTRY.parent and self._p.name in BOARD_FILES: return BOARD / self._p.name
        return self._p
    def read_text(self, *args, **kwargs):
        if self._map() == FAKE / 'boot_id' and STATE['boot_flip']:
            STATE['boot_reads'] += 1
            return 'boot-1' if STATE['boot_reads'] == 1 else 'boot-2'
        return self._map().read_text(*args, **kwargs)
    def __getattr__(self, name):
        attr = getattr(self._map(), name)
        if not callable(attr):
            return FakePath(attr) if isinstance(attr, Path) else attr
        def delegated(*args, **kw):
            result = attr(*args, **kw)
            return FakePath(result) if isinstance(result, Path) else result
        return delegated
    def __truediv__(self, other): return FakePath(self._p / other)
    def __str__(self): return str(self._map())
    def __eq__(self, other): return self._map() == Path(str(other))
    def __hash__(self): return hash(self._map())


def install_fakes():
    status = types.ModuleType('c01_status_onboard')
    status.verify = lambda path, sha: STATE['events'].append(('verify', str(path), sha))
    def load_candidate(bit, Overlay):
        STATE['events'].append(('candidate_load', str(bit)))
        return Overlay(str(bit))
    status.load_candidate = load_candidate
    def restore_original(load, smoke):
        STATE['events'].append(('restore',))
        if STATE['restore_fail']: raise RuntimeError('restore failed: injected')
        load(); smoke()
    status.restore_original = restore_original
    pynq = types.ModuleType('pynq')
    pynq.MMIO = lambda base, size: STATE['rig'] if base == 0x43000000 else STATE['rig'].status
    pynq.Overlay = lambda bit: {'bit': str(bit)}
    pynq.allocate = lambda **kw: STATE['rig'].allocate(**kw)
    pynq.PL = types.SimpleNamespace(timestamp=12345, bitfile_name=STATE['pl_bitfile'])
    m2 = types.ModuleType('m2_onboard')
    def cmd_smoke():
        STATE['shots'] += 1
        STATE['events'].append(('smoke', STATE['shots']))
        if STATE['shots'] in STATE['novideo']: raise SystemExit(3)
    m2.cmd_smoke, m2.cmd_load = cmd_smoke, lambda: STATE['events'].append(('original_load',))
    cv2 = types.ModuleType('cv2'); cv2.IMREAD_COLOR = 1
    def imwrite(path, image):
        if STATE['cv2'] == 'write_fail': return False
        STATE['stored'][str(path)] = image
        Path(str(path)).write_bytes(bytes([137, 80, 78, 71]) + np.asarray(image).tobytes()[:32])
        return True
    cv2.imwrite = imwrite
    cv2.imread = lambda path, flag: None if STATE['cv2'] == 'round_trip' else STATE['stored'].get(str(path))
    park = types.ModuleType('c01_park_capture'); park.PARK_RUN = 0; park.HALT_STICKY = 0
    park.ParkFrameCapture = SingleFrameCapture
    fcntl = types.ModuleType('fcntl'); fcntl.LOCK_EX = fcntl.LOCK_NB = 2
    fcntl.flock = lambda *a: None
    sys.modules.update({'c01_status_onboard': status, 'pynq': pynq, 'm2_onboard': m2,
                        'cv2': cv2, 'fcntl': fcntl, 'c01_park_capture': park})


install_fakes()
spec = importlib.util.spec_from_file_location('c01_ddr_onboard_under_test', ENTRY)
ENTRY_MODULE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ENTRY_MODULE)


class Tests(unittest.TestCase):
    def setUp(self):
        STATE.update(events=[], cv2='ok', novideo=(), shots=0, stored={}, boot_flip=False,
                     restore_fail=False, boot_reads=0,
                     pl_bitfile='/home/xilinx/vision_m2/vision.bit')
        ENTRY_MODULE.Path = FakePath
        ENTRY_MODULE.time = FakeTime()
        FAKE.mkdir(parents=True, exist_ok=True)
        (FAKE / 'vision_m2').mkdir(exist_ok=True)
        BOARD.mkdir(parents=True, exist_ok=True)
        for name in BOARD_FILES:
            source = ROOT / ('src/pynq_host' if name in HOST_SOURCES else 'sim/scripts') / name
            if source.exists(): shutil.copyfile(source, BOARD / name)
        (FAKE / 'boot_id').write_text('boot-1')
        (BOARD / 'ddr-result.json').unlink(missing_ok=True)
        os.environ['C01_BIT'] = str(ROOT / 'sim/build/c01-hdmi-1791713720540454/'
                                         'capture-1791713720540454.bit')
        os.environ.pop('C01_CAPTURE_MODE', None)
    def run_entry(self, rig, keepalive=None, **kw):
        STATE.update(rig=rig, **kw)
        ENTRY_MODULE.time = FakeTime(keepalive)
        sys.modules['pynq'].PL.bitfile_name = STATE['pl_bitfile']
        out = io.StringIO(); caught = None
        try:
            with contextlib.redirect_stdout(out):
                ENTRY_MODULE.main()
        except BaseException as exc:
            caught = exc
        return STATE['events'], out.getvalue(), json.loads((BOARD / 'ddr-result.json').read_text()), caught
    def test_success_path_publishes_and_restores(self):
        events, out, result, caught = self.run_entry(Rig())
        self.assertIsNone(caught)
        self.assertTrue(result['ok'] and result['restored'])
        self.assertEqual(result['boot_after'], result['boot_before'])
        self.assertIn('png_sha256', result)
        self.assertEqual(result['shape'], [720, 1280, 3])
        self.assertEqual(result['driver_sha256'], DRIVER_SHA256)
        import hashlib as _hashlib
        self.assertEqual(result['helper_sha256'],
                         _hashlib.sha256((BOARD / 'c01_status_onboard.py').read_bytes()).hexdigest())
        self.assertEqual(result['runner_sha256'], _hashlib.sha256(ENTRY.read_bytes()).hexdigest())
        self.assertEqual(events[0][0], 'verify')
        self.assertLess(events.index(('restore',)), len(events))
        self.assertIn('PASS: custom DDR complete independent frame', out)
        self.assertIn('PASS: custom DDR cleanup and original vision restoration', out)
    def test_png_write_failure_refuses_publication(self):
        _, out, result, caught = self.run_entry(Rig(), cv2='write_fail')
        self.assertIsInstance(caught, RuntimeError)
        self.assertFalse(result['ok']); self.assertTrue(result['restored'])
        self.assertIn('PNG write failed', result['main_error'])
        self.assertNotIn('unsafe_stop', result)
    def test_png_round_trip_mismatch_refuses_publication(self):
        _, out, result, caught = self.run_entry(Rig(), cv2='round_trip')
        self.assertIsInstance(caught, RuntimeError)
        self.assertFalse(result['ok']); self.assertTrue(result['restored'])
        self.assertIn('PNG round-trip mismatch', result['main_error'])


    def test_novideo_first_attempt_retries_then_captures(self):
        events, out, result, caught = self.run_entry(Rig(), novideo=(1,))
        self.assertIsNone(caught); self.assertTrue(result['ok'])
        self.assertIn('bounded settle retry', out)
        smokes = [e for e in events if e[0] == 'smoke']
        self.assertEqual(smokes[:2], [('smoke', 1), ('smoke', 2)])
        self.assertEqual(smokes[-1], ('smoke', 3))  # third is the restore-time smoke
        self.assertLess(events.index(('restore',)), len(events))
    def test_novideo_twice_fails_before_any_dma(self):
        rig = Rig()
        events, out, result, caught = self.run_entry(rig, novideo=(1, 2))
        self.assertIsInstance(caught, SystemExit)
        self.assertFalse(result['ok']); self.assertIn('SystemExit(3)', result['main_error'])
        self.assertEqual(rig.buffers, []); self.assertNotIn(('write', CR, RUN), rig.events)
        self.assertIn(('restore',), events)
    def test_active_candidate_dma_is_not_restored_over(self):
        rig = Rig(); rig.reg[CR] = 1
        events, out, result, caught = self.run_entry(rig)
        self.assertIsInstance(caught, RuntimeError)
        self.assertIn('do not restore over owner', result['main_error'])
        self.assertNotIn(('restore',), events); self.assertEqual(rig.buffers, [])
    def test_restore_failure_is_reported_and_raised(self):
        events, out, result, caught = self.run_entry(Rig(), restore_fail=True)
        self.assertIsInstance(caught, RuntimeError)
        self.assertTrue(result['ok']); self.assertIn('restore failed', result['restore_error'])
    def test_boot_change_after_capture_is_rejected(self):
        events, out, result, caught = self.run_entry(Rig(), boot_flip=True)
        self.assertIsInstance(caught, RuntimeError)
        self.assertEqual(str(caught), 'board rebooted during capture')
        self.assertEqual(result['boot_after'], 'boot-2')
    def test_unsafe_stop_holds_buffers_and_never_exits(self):
        rig = Rig('unsafe')
        events, out, result, caught = self.run_entry(rig, keepalive=1)
        self.assertIsInstance(caught, KeepAlive)
        self.assertTrue(result['unsafe_stop'])
        self.assertIn('UNSAFE-STOP', out)
        self.assertNotIn(('restore',), events)
        self.assertEqual([b.frees for b in rig.buffers], [0]*4)
        self.assertGreaterEqual(ENTRY_MODULE.time.sleeps.count(1), 1)
        holder = QUARANTINE[-1]
        holder.token = ('boot-1', STATE['pl_bitfile'], '12345')
        rig.mode = 'ok'; holder.close()
        self.assertEqual([b.frees for b in rig.buffers], [1]*4)
        QUARANTINE.remove(holder)


    def test_invalid_capture_mode_refuses_before_hardware(self):
        os.environ['C01_CAPTURE_MODE'] = 'bogus'
        try:
            with self.assertRaises(ValueError):
                ENTRY_MODULE.main()
        finally:
            os.environ.pop('C01_CAPTURE_MODE', None)
    def test_park_mode_selects_park_driver(self):
        os.environ['C01_CAPTURE_MODE'] = 'park'
        try:
            events, out, result, caught = self.run_entry(Rig())
        finally:
            os.environ.pop('C01_CAPTURE_MODE', None)
        self.assertIsNone(caught)
        self.assertEqual(result['capture_mode'], 'park')
        self.assertIn('park_driver_sha256', result)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): sys.exit(1)
    print('PASS: c01_ddr_onboard main: PNG/recovery, NOVIDEO retry, mode guard and UNSAFE-STOP hold')
