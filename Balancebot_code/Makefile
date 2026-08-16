# ============================================================
# BalanceBot Makefile
#
# All targets run from Balancebot_code/ — the PlatformIO project root.
#
# Firmware targets require:
#   - PlatformIO:  pip install platformio
#   - Arduino Nano 33 IoT connected via USB
#
# Python targets require:
#   - pip install -r requirements  (or: pip install pyserial pandas matplotlib numpy)
#   - Bot connected via USB serial
#
# Usage:
#   make flash           Upload balance firmware (active development)
#   make monitor         Open serial monitor
#   make acquire         Record serial data (balance mode)
#   make lint            Run ruff on the Python pipeline
# ============================================================

PYTHON  := python3
PIO     := pio
PORT    ?= /dev/ttyACM0

# ../berechnungen und ../werkzeuge gehoeren zum privaten Entwicklungsrepo
# und fehlen im oeffentlichen Spiegel (werkzeuge/spiegel_abgleichen.py).
# wildcard liefert dort eine leere Zeichenkette; das lint-Ziel laesst den
# jeweiligen Aufruf dann weg, statt mit "No such file or directory"
# abzubrechen.
BERECHNUNGEN := $(wildcard ../berechnungen)
WERKZEUGE    := $(wildcard ../werkzeuge)

# ============================================================
# Help (default target)
# ============================================================

.PHONY: help
help:
	@echo ""
	@echo "  BalanceBot — available targets"
	@echo ""
	@echo "  Firmware"
	@echo "    flash            Upload balance firmware (modular, active)"
	@echo "    flash-v1         Upload balance_v1 firmware (reference)"
	@echo "    flash-carrier    Upload carrier_timing test sketch"
	@echo "    flash-imu        Upload imu_latency test sketch"
	@echo "    flash-deadzone   Upload deadzone_id test sketch"
	@echo "    build            Compile balance firmware (no upload)"
	@echo "    build-all        Compile all environments"
	@echo "    monitor          Open serial monitor (115200 baud)"
	@echo ""
	@echo "  Data pipeline"
	@echo "    acquire          Record serial data — balance mode"
	@echo "    acquire-deadzone Record serial data — deadzone_id mode"
	@echo "    acquire-imu      Record serial data — imu_latency mode"
	@echo "    acquire-carrier  Record serial data — carrier_timing mode"
	@echo ""
	@echo "  Code quality"
	@echo "    lint             Run ruff on active Python scripts"
	@echo ""
	@echo "  PORT=/dev/ttyACM0 (override: make flash PORT=/dev/ttyUSB0)"
	@echo ""

# ============================================================
# Firmware — flash
# ============================================================

.PHONY: flash
flash:
	$(PIO) run -e balance -t upload

.PHONY: flash-v1
flash-v1:
	$(PIO) run -e balance_v1 -t upload

.PHONY: flash-carrier
flash-carrier:
	$(PIO) run -e carrier_timing -t upload

.PHONY: flash-imu
flash-imu:
	$(PIO) run -e imu_latency -t upload

.PHONY: flash-deadzone
flash-deadzone:
	$(PIO) run -e deadzone_id -t upload

# ============================================================
# Firmware — compile only
# ============================================================

.PHONY: build
build:
	$(PIO) run -e balance

.PHONY: build-all
build-all:
	$(PIO) run -e balance -e balance_v1 -e carrier_timing -e imu_latency -e deadzone_id

# ============================================================
# Serial monitor
# ============================================================

.PHONY: monitor
monitor:
	$(PIO) device monitor --baud 115200

# ============================================================
# Data pipeline — acquire
# ============================================================

.PHONY: acquire
acquire:
	$(PYTHON) python/acquire.py --port $(PORT)

.PHONY: acquire-deadzone
acquire-deadzone:
	$(PYTHON) python/acquire.py --mode deadzone --port $(PORT)

.PHONY: acquire-imu
acquire-imu:
	$(PYTHON) python/acquire.py --mode imu --port $(PORT)

.PHONY: acquire-carrier
acquire-carrier:
	$(PYTHON) python/acquire.py --mode carrier --port $(PORT)

# ============================================================
# Code quality
# ============================================================

.PHONY: lint
lint:
	ruff check python/acquire.py python/process.py python/analyze.py python/config.py
ifneq ($(BERECHNUNGEN),)
	ruff check ../berechnungen/
endif
ifneq ($(WERKZEUGE),)
	ruff check ../werkzeuge/
endif
