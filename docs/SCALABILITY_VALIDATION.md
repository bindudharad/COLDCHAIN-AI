# Big Data Scalability & Throughput Validation Report

**Project:** COLDCHAIN-AI  
**Component:** Telemetry Ingestion, Vectorized Preprocessing, & Batch Pipeline  
**Date:** 2026-10-09  
**Status:** BENCHMARKED & EMPIRICALLY PROFILED  

---

## 1. Experimental Methodology & Environment

> [!WARNING]
> **BIG DATA SCOPE & DISTRIBUTED SYSTEMS DISCLOSURE:**  
> This benchmark validates **single-node in-memory vectorized streaming throughput** on edge/server hardware.  
> It demonstrates high-efficiency pandas/NumPy vectorization and PyTorch batching up to $1,000,000\text{ records}$.  
> **It does NOT represent a distributed cluster environment** (no Apache Spark, PySpark, Ray, or distributed Kafka brokers were deployed).

### Test Environment:
- **Operating System:** Windows 11 AMD64
- **Runtime:** Python 3.10.11
- **Deep Learning Engine:** PyTorch 2.14.1 (CPU Execution)
- **Memory Profiler:** Python `tracemalloc`
- **Data Generator:** Chronologically synthesized multi-channel cold-chain sensor stream (`scripts/run_scalability_benchmark.py`)

---

## 2. Empirical Benchmark Results

Evaluated across four discrete orders of magnitude from $10,000$ to $1,000,000$ records:

| Scale (Records) | Memory Footprint | Ingestion Time | Ingestion Throughput | Preprocessing Time | Preprocessing Throughput | Peak RAM | Batch Inference | NSGA-II Runtime | Total Runtime |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **10,000 (10K)** | $1.1\text{ MB}$ | $0.251\text{ s}$ | $39,801\text{ rows/s}$ | $0.097\text{ s}$ | $102,684\text{ rows/s}$ | $2.8\text{ MB}$ | $43.6\text{ ms}$ | $155.9\text{ ms}$ | **$0.567\text{ s}$** |
| **100,000 (100K)** | $11.5\text{ MB}$ | $2.794\text{ s}$ | $35,787\text{ rows/s}$ | $0.210\text{ s}$ | $476,585\text{ rows/s}$ | $25.2\text{ MB}$ | $20.9\text{ ms}$ | $144.2\text{ ms}$ | **$3.325\text{ s}$** |
| **500,000 (500K)** | $57.7\text{ MB}$ | $14.081\text{ s}$ | $35,509\text{ rows/s}$ | $0.911\text{ s}$ | $548,777\text{ rows/s}$ | $125.9\text{ MB}$ | $47.2\text{ ms}$ | $184.2\text{ ms}$ | **$15.966\text{ s}$** |
| **1,000,000 (1M)** | $115.4\text{ MB}$ | $27.963\text{ s}$ | $35,761\text{ rows/s}$ | $1.600\text{ s}$ | $624,846\text{ rows/s}$ | $251.8\text{ MB}$ | $70.6\text{ ms}$ | $95.0\text{ ms}$ | **$31.381\text{ s}$** |

---

## 3. Analysis & Key Takeaways

1. **Sub-Linear Preprocessing Scalability:**  
   Because feature engineering (`core_preprocessing.prepare`) relies on contiguous NumPy/pandas vectorization, preprocessing throughput increases with larger batches, achieving over **$624,000\text{ rows per second}$** at $1\text{M records}$.
2. **Predictable Linear Memory Scaling:**  
   Peak heap allocation scales strictly linearly with input scale: from $2.8\text{ MB}$ at $10\text{K}$ to $251.8\text{ MB}$ at $1\text{M}$. The entire one-million-row pipeline comfortably executes on low-spec edge hardware with $< 512\text{ MB}$ RAM.
3. **Real-Time Control Loop Feasibility:**  
   Neural forecast latency ($20.9\text{--}70.6\text{ ms}$) and constrained NSGA-II optimization ($95.0\text{--}184.2\text{ ms}$) run in under $250\text{ ms}$ combined. This is well within standard 1-minute to 15-minute industrial cold-chain telemetry refresh cycles.
4. **Reproducibility:**  
   Benchmark is completely reproducible via `python scripts/run_scalability_benchmark.py`. Results stored at `reports/scalability_benchmark_report.json`.
