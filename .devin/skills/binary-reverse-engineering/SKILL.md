---
name: binary-reverse-engineering
description: Static analysis of binaries and obfuscated code — triage, unpack, disassemble, report. Defensive analysis only; untrusted code never runs on the host.
---

# Code / Binary Reverse-Engineering

Static-first triage of unknown or hostile binaries, packed/obfuscated code,
and undocumented protocols. **Defensive analysis only** — describe and
detect, never improve malicious capability.

## Hard rules

- **Never execute the sample on the host.** If dynamic observation is truly
  required, it goes through `SandboxManager` (Job Object limits, scrubbed
  secrets, LOW-integrity FS confinement) — and even then prefer pure static.
- No execution of extracted shellcode, no "just to see what it does."
- Keep vulnerability details private until patched / coordinated disclosure.

## Toolchain (Windows host)

- `scripts/binary_recon.py` — first-pass triage: hashes, format detection
  (PE/ELF/Mach-O/script/zip), entropy per section, strings, imports, packed
  indicators. Pure Python, read-only.
- git-bash `strings`, `objdump`, `file` for fast looks.
- Optional `.venv` installs when needed: `pefile`, `capstone`, `yara-python`.
- Python bytecode: `uncompyle6`/`decompyle3` or manual `dis` for version
  mismatches. .NET: ILSpy/dnSpy exports if present.

## Workflow

1. **Triage**: `python scripts/binary_recon.py <file>` → file type, hashes,
   entropy map, import table, suspicious markers (RWE sections, high-entropy
   blobs, suspicious API sets, embedded payloads/URLs/keys).
2. **Classify**: clean-looking installer? packed? script wrapped in PE?
   document? Exploit document → extract macros/OLE streams, don't open.
3. **Unpack before disassembling** when entropy indicates packing — look for
   known packer signatures (UPX, Themida-style, pyinstaller, etc). UPX is
   trivially unpackable offline; commercial protectors may not be.
4. **Disassemble the interesting region** — entry point, suspicious imports,
   string-referenced code — not the whole binary. Capstone for raw bytes.
5. **Report**: IOCs (hashes, URLs, mutexes, reg keys), capability summary,
   MITRE-ish behavior mapping, confidence. What it *does*, what it *could*
   do, and what's unresolved — separately.

## Out of scope (refuse)

- Improving/patching malware, building the C2, evading detection.
- Credential harvesting, cookie/wallet theft assistance.
- Distributing live samples or weaponized derivations.
