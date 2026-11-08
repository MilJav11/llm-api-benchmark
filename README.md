[![LLM Benchmark CI](https://github.com/MilJav11/llm-api-benchmark/actions/workflows/main.yml/badge.svg)](https://github.com/MilJav11/llm-api-benchmark/actions/workflows/main.yml)

# LLM Local API Benchmark 🚀

Professional automated QA framework for benchmarking local LLMs (Llama 3.2, Phi-3, Qwen 2.5) using **Ollama** and **Pytest**.

## 📊 Overview

This project goes beyond simple ping tests. It measures **inference latency**, **instruction-following accuracy**, **security guardrails**, and **RAG context adherence** on local hardware. By separating test data (JSON) from test logic (Pytest), it provides a scalable, 4-layered testing architecture.

### Baseline Benchmark Results (Sample Run)

_Note: LLMs are non-deterministic by nature. These results represent a baseline snapshot; individual CI runs may vary due to model flakiness._

| Model             | Avg. Time | Status    | QA Note                                          |
| :---------------- | :-------- | :-------- | :----------------------------------------------- |
| **Llama 3.2:1b**  | ~11s      | ✅ Passed | Very stable, excellent safety guardrails.        |
| **Phi-3:mini**    | ~19s      | ✅ Passed | High quality, good safety refusals.              |
| **Qwen 2.5:0.5b** | **~4s**   | ❌ Failed | Fast, but highly vulnerable to prompt injection. |

Results were produced locally with the models listed above; CI uses a smaller model set (`llama3.2:1b` and `qwen2.5:0.5b`).

## 🛠️ Setup

1. **Install Ollama:** Follow the instructions at [ollama.com](https://ollama.com) (or run `curl -fsSL https://ollama.com/install.sh | sh`).
2. **Pull the models used by the tests:**
   ```bash
   ollama pull llama3.2:1b
   ollama pull phi3:mini
   ollama pull qwen2.5:0.5b
   ```
3. **Create a Python virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## ▶️ Running the Benchmark

1. **Start Ollama:** run `ollama serve` (or just start the Ollama app).
2. **Run the tests:** `pytest -v`

Tests are skipped automatically when Ollama is not running or no target models are installed.

## 📁 Automated Reporting

The CI/CD pipeline generates automated reports in two formats for easy analysis:

- 🌐 **[HTML Report (Interactive)](./docs/sample-benchmark-report.html)** - Detailed view with duration, LLM judge reasoning, security breaches, and hallucination logs.
- 📄 **[PDF Report (Static)](./docs/sample-benchmark-report.pdf)** - Print-ready version of the test results.

## 🛠️ Tech Stack & Dependencies

- **Python 3.12** & **Pytest** - Core testing logic and assertions.
- **Ollama** - Local LLM inference engine.
- **pytest-html** - Automated HTML report generation.
- **GitHub Actions** - CI/CD pipeline for automated testing runs.

## 🧠 Testing Architecture (4 Layers)

The framework is divided into 4 independent modules, testing different aspects of AI behavior:

1. **⚡ Performance & Exact Match (`test_local_benchmark.py`)**
   Measures basic inference speed and checks if the model can strictly follow constraints (e.g., "answer with one word only").
2. **⚖️ Advanced Evaluation (`test_llm_judge.py`)**
   Implements the **LLM-as-a-Judge** pattern. A designated evaluator model (Llama 3.2) is dynamically prompted to act as a strict QA engineer to semantically evaluate complex reasoning outputs.
3. **🛡️ AI Red Teaming (`test_security.py`)**
   Automated security testing against **Prompt Injection** and **Unsafe Content**. It acts as a "Red Team," intentionally sending malicious prompts to verify if the models' safety guardrails kick in.
4. **📚 RAG Hallucination Prevention (`test_rag_hallucinations.py`)**
   Simulates a Retrieval-Augmented Generation (RAG) environment. The models are evaluated on their ability to adhere strictly to provided context, penalizing them if they introduce outside knowledge or hallucinate facts.

## 🔍 QA Insights & Learnings

- **Strict Constraints:** Small parameter models (like Qwen 2.5:0.5b) struggle with strict "one-word" constraints, highlighting the fragility of standard "exact-match" assertions in AI testing.
- **Security Vulnerabilities:** Small models generally lack sufficient attention mechanisms to resist prompt injection attacks ("ignore previous instructions").
- **LLM Non-Determinism (Flakiness):** During repeated CI/CD runs, identical prompts sometimes yielded different results due to the probabilistic nature of LLMs (e.g., hallucinating forbidden concepts randomly). This proves the necessity of robust, multi-layered automated testing and semantic evaluation over rigid text matching.

## 🚀 Scalability: Adding New Models

This framework is highly scalable. To add a new model (e.g., Mistral), simply follow these 3 steps:

1. **Pull the model locally:** Run `ollama pull mistral` in your terminal.
2. **Update the test scripts:** Add the new model to the `MODELS_TO_TEST` list inside the `.py` files (e.g., `MODELS_TO_TEST = ["llama3.2:1b", "phi3:mini", "qwen2.5:0.5b", "mistral"]`).
3. **Expand test data (Optional):** Add new complex scenarios to the corresponding `.json` files to challenge the new model.
