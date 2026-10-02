# make host-test   : sanity-check data + harness on your PC (scalar fallback, no RVV)
# make spike       : build RVV binaries, run on Spike -> results/vlen$(VLEN)/, then analyze
# make sweep       : make spike for every VLEN in $(VLENS) (same binaries, RVV is VLEN-agnostic)
# Override toolchain if needed: make spike CC="clang --target=riscv64-unknown-elf ..."
RISCV   ?= /opt/riscv
export PATH := $(RISCV)/bin:$(PATH)
ifeq ($(origin CC),default)
CC := riscv64-unknown-elf-gcc
endif
ARCH    ?= rv64gcv_zicntr
VLEN    ?= 512
VLENS   ?= 128 256 512
SPIKE   ?= spike
SPIKE_ISA ?= $(ARCH)_zvl$(VLEN)b
PK      ?= pk
N       ?= 128
SEED    ?= 1
SPARS   ?= 0.0 0.1 0.2 0.3 0.4 0.5 0.8 0.9 0.95 0.99
PATTERNS?= uniform banded block
CFLAGS  ?= -I. -O2 -march=$(ARCH) -mabi=lp64d
OUT     ?= results/vlen$(VLEN)

DATA := $(foreach p,$(PATTERNS),$(foreach s,$(SPARS),data/$(p)_s$(s).h))
BINS := $(patsubst data/%.h,bin/%,$(DATA))

.SECONDARY: $(DATA)

# N and SEED are baked into the headers: regenerate them whenever either changes.
PARAMS := N=$(N) SEED=$(SEED)
data/.params: FORCE
	@mkdir -p data
	@echo "$(PARAMS)" | cmp -s - $@ || echo "$(PARAMS)" > $@

data/%.h: data/.params scripts/gen_matrix.py
	python3 scripts/gen_matrix.py --n $(N) --seed $(SEED) \
	  --pattern $(firstword $(subst _s, ,$*)) --sparsity $(lastword $(subst _s, ,$*)) --out $@

bin/%: data/%.h src/main.c src/kernels.c src/kernels.h
	@mkdir -p bin
	$(CC) $(CFLAGS) -DDATA_HEADER='"$<"' src/main.c src/kernels.c -o $@ -lm

spike: $(BINS)
	@mkdir -p $(OUT); : > $(OUT)/spike_results.txt
	@for b in $(BINS); do echo "== $$b"; $(SPIKE) --isa=$(SPIKE_ISA) $(PK) $$b | tee -a $(OUT)/spike_results.txt; done
	python3 scripts/analyze.py $(OUT)/spike_results.txt --metric instret --outdir $(OUT)

sweep:
	@for v in $(VLENS); do $(MAKE) --no-print-directory spike VLEN=$$v || exit 1; done

host-test:
	@mkdir -p bin data
	python3 scripts/gen_matrix.py --n 64 --sparsity 0.9 --out data/host.h
	gcc -I. -O2 -DDATA_HEADER='"data/host.h"' src/main.c src/kernels.c -o bin/host -lm
	./bin/host

clean:
	rm -rf bin data
FORCE:
.PHONY: spike sweep host-test clean FORCE
