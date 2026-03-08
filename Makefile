.PHONY: smoke benchmark summary ci

smoke:
	PYTHONPATH=src python3 scripts/smoke_check.py

benchmark:
	PYTHONPATH=src python3 scripts/run_benchmark.py

summary:
	python3 scripts/summarize_benchmark.py

ci:
	./scripts/ci_check.sh
