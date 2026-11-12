"""Static triage of an unknown/suspicious file. READ-ONLY — never executes.

Usage: python scripts/binary_recon.py <path> [--strings] [--min-str 6]
Outputs: hashes, format, entropy map, PE structure, imports, suspicious
markers (URLs, IPs, embedded payloads, persistence/exfil patterns).
"""
import argparse
import hashlib
import math
import re
import struct
import sys
from pathlib import Path

SUSPICIOUS = [
    (rb"(?i)powershell", "powershell ref"),
    (rb"(?i)-enc\b|-encodedcommand", "encoded PS command"),
    (rb"(?i)virtualalloc", "VirtualAlloc (shellcode staging)"),
    (rb"(?i)createremotethread", "remote thread injection"),
    (rb"(?i)runonce|currentversion\\\\run", "registry persistence"),
    (rb"(?i)cmd\.exe\s*/c", "cmd shell exec"),
    (rb"(?i)http://|https://", "embedded URL"),
    (rb"(?i)\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "embedded IP"),
    (rb"(?i)-----BEGIN [A-Z ]*PRIVATE KEY", "embedded private key"),
    (rb"(?i)\.onion", "tor/onion ref"),
    (rb"(?i)cryptowallet|wallet\.dat|bc1[a-z0-9]{20,}", "crypto wallet ref"),
]

MAGICS = [
    (b"MZ", "PE/DOS executable"), (b"\x7fELF", "ELF binary"),
    (b"PK\x03\x04", "ZIP/archive"), (b"\xfe\xed\xfa", "Mach-O"),
    (b"\xcf\xfa\xed\xfe", "Mach-O"), (b"\xca\xfe\xba\xbe", "Mach-O fat"),
    (b"%PDF", "PDF"), (b"\xd0\xcf\x11\xe0", "OLE (doc/xls/vba)"),
    (b"#!", "script w/ shebang"), (b"Rar!", "RAR"), (b"\x1f\x8b", "gzip"),
]


def entropy(b: bytes) -> float:
    if not b:
        return 0.0
    freq = [0] * 256
    for x in b:
        freq[x] += 1
    n = len(b)
    return -sum((c / n) * math.log2(c / n) for c in freq if c)


def ascii_strings(data: bytes, n: int):
    for m in re.finditer(rb"[\x20-\x7e]{%d,}" % n, data):
        yield m.group().decode("ascii", "replace")
    for m in re.finditer(rb"(?:[\x20-\x7e]\x00){%d,}" % n, data):
        yield m.group().decode("utf-16-le", "replace").replace("\x00", "")


def pe_info(data: bytes):
    out = {"sections": [], "imports": [], "flags": []}
    if data[:2] != b"MZ":
        return out
    try:
        e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
        if data[e_lfanew:e_lfanew + 4] != b"PE\x00\x00":
            return out
        nsec = struct.unpack_from("<H", data, e_lfanew + 6)[0]
        optsize = struct.unpack_from("<H", data, e_lfanew + 20)[0]
        opt = e_lfanew + 24
        magic = struct.unpack_from("<H", data, opt)[0]
        out["arch"] = "x64" if magic == 0x20B else "x86" if magic == 0x10B else f"magic {magic:#x}"
        sec_base = opt + optsize
        for i in range(nsec):
            o = sec_base + i * 40
            if o + 40 > len(data):
                break
            name = data[o:o + 8].rstrip(b"\x00").decode("ascii", "replace")
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, o + 8)
            chars = struct.unpack_from("<I", data, o + 36)[0]
            ent = entropy(data[rawptr:rawptr + rawsize])
            flags = "".join(c for c, bit in
                            (("R", 0x40000000), ("W", 0x80000000), ("X", 0x20000000))
                            if chars & bit)
            out["sections"].append({"name": name, "vsize": vsize, "raw": rawsize,
                                    "entropy": round(ent, 2), "flags": flags})
    except Exception as e:
        out["flags"].append(f"PE parse error: {e}")
    try:
        import pefile  # type: ignore
        pe = pefile.PE(data=data)
        for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []) or []:
            dll = entry.dll.decode("ascii", "replace")
            funcs = [i.name.decode("ascii", "replace") if i.name else f"ord{i.ordinal}"
                     for i in entry.imports]
            out["imports"].append((dll, funcs))
    except ImportError:
        out["flags"].append("pefile not installed — imports skipped (pip install pefile)")
    except Exception:
        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--strings", action="store_true", help="dump full strings")
    ap.add_argument("--min-str", type=int, default=6)
    a = ap.parse_args()
    p = Path(a.path)
    data = p.read_bytes()
    print(f"file: {p.name}  ({len(data)} bytes)")
    print(f"sha256: {hashlib.sha256(data).hexdigest()}")
    print(f"md5:    {hashlib.md5(data).hexdigest()}")
    fmt = next((name for m, name in MAGICS if data.startswith(m)), "unknown")
    print(f"format: {fmt}")
    print(f"entropy: {entropy(data):.2f} /8.0  "
          f"({'packed/encrypted-looking' if entropy(data) > 7.2 else 'normal'})")

    embedded = [m.start() for m in re.finditer(rb"MZ", data)][1:]
    if fmt == "PE/DOS executable" and embedded:
        print(f"[!] {len(embedded)} embedded MZ magic(s) at {embedded[:6]} — possible payload")

    info = pe_info(data) if fmt == "PE/DOS executable" else {}
    if info.get("sections"):
        print("\nsections:")
        for s in info["sections"]:
            warn = "  <-- high entropy" if s["entropy"] > 7.0 else ""
            rwx = "  <-- RWX" if set(s["flags"]) == {"R", "W", "X"} else ""
            print(f"  {s['name']:<9} vsize={s['vsize']:>8} raw={s['raw']:>8} "
                  f"ent={s['entropy']:<5} {s['flags']}{warn}{rwx}")
    if info.get("imports"):
        print("\nimports:")
        for dll, funcs in info["imports"]:
            print(f"  {dll}: {', '.join(funcs[:12])}{' ...' if len(funcs) > 12 else ''}")
    for f in info.get("flags", []):
        print(f"[note] {f}")

    print("\nsuspicious markers:")
    hits = 0
    for pat, label in SUSPICIOUS:
        found = re.findall(pat, data)
        if found:
            hits += 1
            uniq = sorted(set(x.decode('ascii', 'replace') if isinstance(x, bytes) else str(x) for x in found))[:8]
            print(f"  [!] {label} x{len(found)}: {uniq}")
    if not hits:
        print("  none")

    if a.strings:
        print("\nstrings:")
        for s in ascii_strings(data, a.min_str):
            print(" ", s)
    else:
        ints = [s for s in ascii_strings(data, a.min_str)
                if re.search(r"(?i)url|http|key|token|pass|mutex|reg|\.exe|\.dll|api", s)]
        if ints:
            print("\ninteresting strings (filtered):")
            for s in ints[:40]:
                print(" ", s)


if __name__ == "__main__":
    sys.exit(main())
