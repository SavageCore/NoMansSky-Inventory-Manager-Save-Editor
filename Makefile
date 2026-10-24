PYTHON ?= python3

.PHONY: help linux appimage deb rpm flatpak tarball all test clean \
        rpm-build rpm-install deb-install

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

# Build the two Linux executables (PyInstaller)
linux: ## Build dist/NMS-Sorter and dist/NMS-Sorter-console plus the tarball
	$(PYTHON) packaging/build_linux.py

tarball: linux ## Alias for the release tarball (produced by `linux`)

# Per-format packages (each depends on the linux binary)
appimage: linux ## Build the AppImage (requires appimagetool)
	$(PYTHON) packaging/build_appimage.py

deb: linux ## Build the .deb package
	$(PYTHON) packaging/build_deb.py

deb-install: deb ## Install the .deb package
	@deb=$$(ls dist/nms-sorter_*_amd64.deb | head -1); \
	if [ -z "$$deb" ]; then echo "no deb found"; exit 1; fi; \
	if [ "$$(id -u)" -eq 0 ]; then dpkg -i "$$deb"; \
	else sudo dpkg -i "$$deb"; fi

rpm: linux rpm-build rpm-install ## Build and install the .rpm package

rpm-build: linux ## Build the .rpm package
	$(PYTHON) packaging/build_rpm.py

rpm-install: ## Install the built .rpm package
	@rpm=$$(ls dist/nms-sorter-*.rpm | head -1); \
	if [ -z "$$rpm" ]; then echo "no rpm found"; exit 1; fi; \
	if [ "$$(id -u)" -eq 0 ]; then dnf install -y "$$rpm"; \
	else sudo dnf install -y "$$rpm"; fi

flatpak: ## Build the Flatpak bundle (builds from source)
	$(PYTHON) packaging/build_flatpak.py

# Convenience
all: linux appimage deb rpm ## Build everything (flatpak excluded; run `make flatpak` separately)

test: ## Run the test suite
	$(PYTHON) -m pytest tests -q --ignore=tests/test_fuzz.py

clean: ## Remove build artifacts
	rm -rf build dist .pytest_cache
