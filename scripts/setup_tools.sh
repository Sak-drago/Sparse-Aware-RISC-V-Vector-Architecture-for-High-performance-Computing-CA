#!/usr/bin/env bash
# Build dtc, Spike and pk into $RISCV (default /opt/riscv). No root needed if $RISCV is writable.
# Assumes riscv64-unknown-elf-gcc (with RVV support, GCC >= 14) is already in $RISCV/bin.
# Host packages needed: g++, make, flex, bison, libboost-regex-dev, libboost-system-dev.
set -euo pipefail
RISCV=${RISCV:-/opt/riscv}
WORK=${WORK:-$HOME/rvtools-src}
JOBS=${JOBS:-$(nproc)}
export PATH="$RISCV/bin:$PATH"

# Commits this artifact was validated with.
DTC_REV=7a1e017926004ecff5fce62d62d42ce9f3e00082
SPIKE_REV=609dbe0b9994154833039209fa37151e7c05e9d4
PK_REV=9c61d29846d8521d9487a57739330f9682d5b542

fetch() { # url dir rev
  [ -d "$2" ] || git clone "$1" "$2"
  git -C "$2" checkout -q "$3"
}

mkdir -p "$WORK" && cd "$WORK"

# Spike shells out to dtc at start-up to build its device tree.
fetch https://github.com/dgibson/dtc.git dtc $DTC_REV
make -C dtc -j"$JOBS" NO_PYTHON=1 NO_YAML=1 NO_VALGRIND=1 PREFIX="$RISCV" install

fetch https://github.com/riscv-software-src/riscv-isa-sim.git riscv-isa-sim $SPIKE_REV
mkdir -p riscv-isa-sim/build && (cd riscv-isa-sim/build && ../configure --prefix="$RISCV" && make -j"$JOBS" && make install)

fetch https://github.com/riscv-software-src/riscv-pk.git riscv-pk $PK_REV
mkdir -p riscv-pk/build && (cd riscv-pk/build && ../configure --prefix="$RISCV" --host=riscv64-unknown-elf --with-arch=rv64gc_zifencei && make -j"$JOBS" && make install)

spike --help 2>&1 | head -1
ls -l "$RISCV/riscv64-unknown-elf/bin/pk"
