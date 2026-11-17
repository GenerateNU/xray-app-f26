"""
Claude wrote this to figure out how the data is set up and what the cmds does.

radeye.py - Serial driver for Thermo Scientific RadEye instruments (G20 and family)

Protocol details below were recovered from Thermo's RadEye.EXE (V1.6.0, VB6),
by disassembling its communication routines. They have NOT yet been tested
against a live instrument, so treat the first session as a verification run.

PHYSICAL LAYER  (confirmed: MSComm "Settings" property in RadEye.EXE)
    9600 baud, 7 data bits, EVEN parity, 2 stop bits, no flow control.
    The IR cable (USB 42540/26 or RS232 42540/29) is a plain serial port;
    with USB it shows up as a virtual COM port (FTDI or Prolific driver).

TRANSACTION  (confirmed from the transfer routine)
    1. Flush input, send '@' to wake the instrument's IR interface.
    2. Instrument answers with a prompt that tells you the current link mode:
         '>'  (0x3E)  -> ASCII line mode
         BEL  (0x07)  -> framed mode
    3. Send the command in the format for that mode, read the reply.
    RadEye.EXE retries a failed transaction up to 3 times.

ASCII LINE MODE
    request:  <cmd> CR LF
    reply:    text terminated by LF;  '#?' means "command not understood".

FRAMED MODE  (what RadEye.EXE normally uses; it switches with '*C1')
    request:  STX <cmd> <CC> ETX
    reply:    STX <payload> <CC> ETX     data reply
              ACK (0x06)                  write accepted
              NAK (0x15)                  rejected
              STX '?41' ETX               error / unknown command
    CC = two uppercase hex digits of (0x02 + sum of the ASCII codes of
         <cmd> or <payload>) & 0xFF.  I.e. a mod-256 sum including STX.

    '*C1' selects framed mode, '*C0' selects ASCII mode.

COMMANDS
    Commands are short ASCII strings. By convention '<x>R' reads a parameter
    group and '<x>W ...' writes it. Reply fields are usually hexadecimal
    tokens separated by spaces (RadEye.EXE parses them as "&H" & token).

    Verified on a RadEye G20-10, firmware E3.11 (2026-10-19 probe):
        'V'    identification, e.g. 'RadEye G20-10 E3.11'
        '#R'   serial number (decimal)
        'ZR'   real-time clock, YYMMDDhhmmss
        'DR'   user text field (the hidden 200-char "Text field")
        'lR'   source-test parameters: nuclide, reference value, ref. date,
               half-life, last test timestamp
        'AR5'  dose-rate alarm 1   } units of 0.01 uSv/h, decimal,
        'AR6'  dose-rate alarm 2   } single-precision floats
        'AR7'  dose alarm 1        } units of 0.01 uSv
        'AR8'  dose alarm 2        }   (999999872 = 1e9 = 10 Sv)
    Tentative:
        'TR'   returns a constant 120 - probably the history interval (s),
               NOT the measurement.
        AUTOSEND  With Menu > Settings > Autosend enabled, the instrument
               periodically sends unsolicited frames like
               '10 0  0 0 00 FH41B2  439 ' (STX..CC ETX, then CR LF).
               The first field appears to be dose rate in 0.01 uSv/h.
               Use listen() / --listen. These frames can also arrive in the
               middle of a command and be mistaken for its reply.
        'WR'   'YYMMDD YYMMDD Vx.xx' - possibly calibration date,
               calibration expiry (010101 = none) and bootloader version
    Replies that are just ACK mean "no data for this command on this model".
    Many other replies ('fR', 'kR', 'KR', 'jR', 'mR') are hex bit-fields.
    Use `python radeye.py COM4 --probe` to dump raw replies and compare them
    with what RadEye.EXE shows for the same instrument.

SAFETY
    Write commands (anything with 'W' as its second character, plus clear/
    erase commands) can change alarm thresholds, configuration or wipe history.
    This driver refuses them unless you pass allow_write=True.

Requires: pyserial  (pip install pyserial)
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

try:
    import serial  # pyserial
except ImportError:  # allow import for testing without pyserial
    serial = None

STX, ETX, ACK, BEL, NAK = b"\x02", b"\x03", b"\x06", b"\x07", b"\x15"
CR, LF = b"\r", b"\n"

MODE_ASCII = 0
MODE_FRAMED = 1

# Read-only commands observed in RadEye.EXE. Safe to send for exploration.
READ_COMMANDS = [
    "V", "#R", "BR", "WR", "ZR", "TR", "fR", "uR", "sR", "dR", "DR", "cR",
    "mR", "nR", "lR", "kR", "jR", "hR", "HR", "bR", "KR", "NR", "SR",
    "oR", "pR", "qR", "yR", "zR",
    "AR0", "AR1", "AR2", "AR3", "AR4", "AR5", "AR6", "AR7", "AR8", "AR9",
    "ARB", "ARC", "ARH", "ARK", "ARM", "ARN", "ARP", "ART", "ARs", "ARt",
]

DANGEROUS_PREFIXES = ("clr", "EW", "EC", "CC", "D", "HW", "BT~W", "~W")


class RadEyeError(Exception):
    pass


class RadEyeTimeout(RadEyeError):
    pass


class RadEyeNak(RadEyeError):
    pass


class RadEyeChecksumError(RadEyeError):
    pass


def checksum(text: str) -> str:
    """Two-hex-digit checksum: (0x02 + sum of ASCII codes) mod 256, uppercase."""
    total = 0x02 + sum(text.encode("ascii"))
    return f"{total & 0xFF:02X}"


def build_frame(cmd: str) -> bytes:
    return STX + cmd.encode("ascii") + checksum(cmd).encode("ascii") + ETX


def parse_frame(buf: bytes) -> Optional[str]:
    """
    Parse a framed reply. Returns payload (str), "" for a bare ACK,
    None if the buffer is not yet complete. Raises on NAK/error/bad checksum.
    """
    stx = buf.find(STX)
    if stx < 0:
        if NAK in buf:
            raise RadEyeNak("instrument replied NAK")
        if ACK in buf:
            return ""
        return None
    etx = buf.find(ETX, stx + 1)
    if etx < 0:
        return None
    body = buf[stx + 1:etx].decode("ascii", errors="replace")
    if body == "?41":
        raise RadEyeNak("instrument replied ?41 (command not accepted)")
    if len(body) < 2:
        raise RadEyeChecksumError(f"frame too short: {buf!r}")
    payload, cc = body[:-2], body[-2:]
    if checksum(payload) != cc.upper():
        raise RadEyeChecksumError(
            f"checksum mismatch: got {cc}, expected {checksum(payload)} for {payload!r}")
    return payload


def hex_fields(payload: str) -> List[int]:
    """Split a reply into space-separated hex tokens, as RadEye.EXE does."""
    out = []
    for tok in payload.split():
        try:
            out.append(int(tok, 16))
        except ValueError:
            pass
    return out


def decimal_fields(payload: str) -> List[float]:
    """Split a reply into space-separated decimal numbers."""
    out = []
    for tok in payload.split():
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


UNIT = 0.01  # uSv or uSv/h per count, as seen in AR5..AR8 and TR


@dataclass
class Alarms:
    rate1_uSv_h: float
    rate2_uSv_h: float
    dose1_uSv: float
    dose2_uSv: float


@dataclass
class Measurement:
    raw: str
    fields: List[str]
    dose_rate_uSv_h: Optional[float]  # TENTATIVE: first field x 0.01


class RadEye:
    def __init__(self, port: str, *, prompt_timeout: float = 0.7,
                 reply_timeout: float = 2.0, retries: int = 3,
                 allow_write: bool = False, debug: bool = False, ser=None):
        self.prompt_timeout = prompt_timeout
        self.reply_timeout = reply_timeout
        self.retries = retries
        self.allow_write = allow_write
        self.debug = debug
        self.mode: Optional[int] = None
        if ser is not None:
            self.ser = ser
        else:
            if serial is None:
                raise RadEyeError("pyserial is not installed (pip install pyserial)")
            self.ser = serial.Serial(
                port=port, baudrate=9600, bytesize=serial.SEVENBITS,
                parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_TWO,
                timeout=0.05, xonxoff=False, rtscts=False, dsrdtr=False)

    # ---- context manager -------------------------------------------------
    def close(self):
        try:
            self.ser.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ---- low level -------------------------------------------------------
    def _log(self, direction: str, data: bytes):
        if self.debug:
            print(f"{direction} {data!r}", file=sys.stderr)

    def _write(self, data: bytes):
        self._log("-->", data)
        self.ser.write(data)
        self.ser.flush()

    def _read_until(self, done, timeout: float) -> bytes:
        buf = b""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            chunk = self.ser.read(self.ser.in_waiting or 1)
            if chunk:
                buf += chunk
                if done(buf):
                    self._log("<--", buf)
                    return buf
        self._log("<-- (timeout)", buf)
        raise RadEyeTimeout(f"no complete reply within {timeout}s (got {buf!r})")

    def wake(self) -> int:
        """Send '@' and detect the link mode from the prompt."""
        self.ser.reset_input_buffer()
        self._write(b"@")
        buf = self._read_until(lambda b: b">" in b or BEL in b, self.prompt_timeout)
        self.mode = MODE_ASCII if b">" in buf else MODE_FRAMED
        return self.mode

    def _transfer_once(self, cmd: str) -> str:
        mode = self.wake()
        if mode == MODE_FRAMED:
            self._write(build_frame(cmd))
            result = {}

            def done(b):
                try:
                    p = parse_frame(b)
                except RadEyeError as e:
                    result["err"] = e
                    return True
                if p is not None:
                    result["payload"] = p
                    return True
                return False

            self._read_until(done, self.reply_timeout)
            if "err" in result:
                raise result["err"]
            payload = result["payload"]
        else:
            self._write(cmd.encode("ascii") + CR + LF)
            buf = self._read_until(lambda b: LF in b or b"#?" in b, self.reply_timeout)
            if b"#?" in buf:
                raise RadEyeNak("instrument replied #? (command not understood)")
            payload = buf.decode("ascii", errors="replace").strip("\r\n>")
        # '*C0' / '*C1' switch the link mode for later transactions
        if cmd.startswith("*C") and len(cmd) == 3 and cmd[2] in "01":
            self.mode = int(cmd[2])
        return payload

    # ---- public API ------------------------------------------------------
    def query(self, cmd: str) -> str:
        """Send one command and return the reply payload (with retries)."""
        if not self.allow_write and self._is_write(cmd):
            raise RadEyeError(
                f"refusing write/clear command {cmd!r}; pass allow_write=True if intended")
        last = None
        for attempt in range(self.retries):
            try:
                return self._transfer_once(cmd)
            except (RadEyeTimeout, RadEyeChecksumError) as e:
                last = e
                time.sleep(0.1)
        raise last

    def query_fields(self, cmd: str) -> List[int]:
        return hex_fields(self.query(cmd))

    @staticmethod
    def _is_write(cmd: str) -> bool:
        if cmd.startswith("*C"):
            return False
        if len(cmd) >= 2 and cmd[1] == "W":
            return True
        return any(cmd.startswith(p) for p in DANGEROUS_PREFIXES) and cmd not in READ_COMMANDS

    def use_framed_mode(self):
        """Switch to checksummed framed mode, as RadEye.EXE does."""
        self.query("*C1")

    def version(self) -> str:
        return self.query("V")

    def serial_number(self) -> str:
        return self.query("#R")

    def clock(self) -> datetime:
        raw = self.query("ZR").strip()[-12:]
        return datetime.strptime(raw, "%y%m%d%H%M%S")

    def user_text(self) -> str:
        return self.query("DR").strip()

    def alarms(self) -> Alarms:
        v = [decimal_fields(self.query(c))[0] * UNIT for c in ("AR5", "AR6", "AR7", "AR8")]
        return Alarms(*v)

    def source_test_params(self) -> List[str]:
        return self.query("lR").split()

    def listen(self, timeout: float = 30.0):
        """
        Yield Measurement objects from Autosend frames, without sending anything.
        Requires Autosend enabled on the instrument. Raises RadEyeTimeout if no
        frame arrives within `timeout` seconds.
        """
        buf = b""
        deadline = time.monotonic() + timeout
        while True:
            chunk = self.ser.read(self.ser.in_waiting or 1)
            if chunk:
                buf += chunk
                self._log("<--", chunk)
            while True:
                try:
                    payload = parse_frame(buf)
                except RadEyeError as e:
                    self._log("!! bad frame", buf)
                    buf = buf[buf.find(ETX) + 1:] if ETX in buf else b""
                    continue
                if payload is None:
                    break
                buf = buf[buf.find(ETX, buf.find(STX)) + 1:] if STX in buf else b""
                if payload:
                    deadline = time.monotonic() + timeout
                    yield self._decode_measurement(payload)
            if len(buf) > 4096:
                buf = buf[-512:]
            if time.monotonic() > deadline:
                raise RadEyeTimeout(f"no Autosend frame within {timeout}s - is Autosend enabled?")

    @staticmethod
    def _decode_measurement(raw: str) -> "Measurement":
        """TENTATIVE decoding of an Autosend frame."""
        fields = raw.split()
        rate = None
        if fields:
            try:
                rate = float(fields[0]) * UNIT
            except ValueError:
                pass
        return Measurement(raw=raw, fields=fields, dose_rate_uSv_h=rate)

    def probe(self, commands=READ_COMMANDS):
        """Send each read-only command and yield (cmd, reply or error)."""
        for cmd in commands:
            try:
                yield cmd, self.query(cmd)
            except RadEyeError as e:
                yield cmd, f"<{type(e).__name__}: {e}>"


# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description="Talk to a RadEye over its IR serial link")
    ap.add_argument("port", help="serial port, e.g. COM4 or /dev/ttyUSB0")
    ap.add_argument("--cmd", action="append", help="send a raw command (repeatable)")
    ap.add_argument("--probe", action="store_true", help="dump replies to all read commands")
    ap.add_argument("--listen", action="store_true",
                    help="print Autosend frames (enable Autosend on the instrument first)")
    ap.add_argument("--ascii", action="store_true", help="stay in ASCII mode (skip '*C1')")
    ap.add_argument("--debug", action="store_true", help="print raw bytes on stderr")
    ap.add_argument("--allow-write", action="store_true", help="permit write/clear commands")
    args = ap.parse_args(argv)

    with RadEye(args.port, debug=args.debug, allow_write=args.allow_write) as dev:
        if args.listen and not (args.cmd or args.probe):
            print("Listening for Autosend frames - compare with the display. Ctrl+C to stop.")
            try:
                for m in dev.listen():
                    rate = f"{m.dose_rate_uSv_h:.2f} uSv/h" if m.dose_rate_uSv_h is not None else "?"
                    print(f"{datetime.now():%H:%M:%S}  {rate:>14}   raw={m.raw!r}")
            except KeyboardInterrupt:
                pass
            return
        mode = dev.wake()
        print(f"Instrument awake, link mode: {'framed' if mode else 'ASCII'}")
        if not args.ascii and mode != MODE_FRAMED:
            dev.use_framed_mode()
            print("Switched to framed mode")
        print("Version :", dev.version())
        if args.cmd:
            for c in args.cmd:
                print(f"{c:6} -> {dev.query(c)!r}")
        if args.probe:
            for c, r in dev.probe():
                print(f"{c:6} -> {r!r}")
        if args.listen:
            print("Listening for Autosend frames - compare with the display. Ctrl+C to stop.")
            try:
                for m in dev.listen():
                    rate = f"{m.dose_rate_uSv_h:.2f} uSv/h?" if m.dose_rate_uSv_h is not None else "?"
                    print(f"{datetime.now():%H:%M:%S}  {rate:>14}   raw={m.raw!r}")
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()