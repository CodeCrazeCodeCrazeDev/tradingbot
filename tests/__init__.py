"""Test suite for AlphaAlgo 2.0.

Intentionally bare: importing test modules at package-init pulls heavy
optional dependencies (torch, RL stacks) into *every* pytest collection.
Pytest discovers test files directly; eager imports here are redundant.
"""
