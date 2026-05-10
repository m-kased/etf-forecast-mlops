.PHONY: help setup train test lint format clean

help:
	@echo "Available targets:"
	@echo "  setup  - create local folders for the project"
	@echo "  train  - placeholder for model training command"
	@echo "  test   - placeholder for running tests"
	@echo "  lint   - placeholder for lint checks"
	@echo "  format - placeholder for code formatting"
	@echo "  clean  - remove generated local artifacts"

setup:
	mkdir -p data models notebooks scripts tests terraform .github/workflows reports
	@echo "Created standard project folders"

train:
	@echo "TODO: add training command"

test:
	@echo "TODO: add test command"

lint:
	@echo "TODO: add lint command"

format:
	@echo "TODO: add format command"

clean:
	rm -rf models/* reports/*
	@echo "Cleaned models/ and reports/ contents"
