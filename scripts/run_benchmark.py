from agentgym.eval.runner import run_benchmark


if __name__ == "__main__":
    path = run_benchmark()
    print(f"BENCHMARK_OK {path}")
