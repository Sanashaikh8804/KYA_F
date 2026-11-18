.PHONY: test demo latency eval

test:
	pytest

demo:
	uvicorn mockbank.app:app --reload

latency:
	python eval/latency.py

eval:
	python eval/run_eval.py
