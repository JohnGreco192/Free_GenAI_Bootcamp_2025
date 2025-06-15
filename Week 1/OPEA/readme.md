# OPEA Megaservice with TGI (Text Generation Inference)

This project sets up an OPEA (Open Platform for Enterprise AI) Megaservice to serve a Large Language Model (LLM) using Hugging Face's Text Generation Inference (TGI) backend. The setup is designed to run efficiently on GPU-enabled environments, specifically demonstrated on Lightning AI Studios with NVIDIA L4 GPUs.

---

## Project Overview

This project consists of three main components that work together in a pipeline:

### TGI Server (`tgi.py`)
This script launches the core LLM inference engine using **Hugging Face's TGI**. It loads the specified LLM onto your GPU and exposes an API endpoint for text generation.

### LLM Microservice (`llm_microservice_app.py`)
This is an **OPEA-compliant microservice** that acts as a client to the TGI server. It receives requests from the Megaservice, formats them for TGI, sends them to the TGI server, and then returns the TGI's response back to the Megaservice.

### OPEA Megaservice (`appLLMonly.py`)
This is the **orchestrator service** that exposes the public API endpoint (`/v1/chat/completions`). It receives user requests and forwards them to the LLM Microservice.

---

## Current State and Setup

You've successfully set up and troubleshooted the communication pipeline. All services are now communicating correctly, and the TGI server is running, ready to receive requests.

### Hardware Constraint Notes
This setup is running on a **Lightning AI Studio with an NVIDIA L4 GPU**. This is crucial, as TGI heavily relies on GPU acceleration for efficient LLM inference. An L4 GPU (with 24GB VRAM) is significantly more powerful than a T4 and is well-suited for running LLMs, including larger models like Llama 3 8B Instruct. **Attempting to run TGI with `--gpus all` on a CPU-only instance will result in an error.**

### Prerequisites
* A Lightning AI Studio with an **NVIDIA L4 GPU** allocated.
* Docker installed and running within the Lightning AI Studio environment (this is usually pre-configured).
* Required Python libraries (primarily `comps`, `fastapi`, `uvicorn`, `requests`, `pydantic`). These are typically managed by your `miniconda3/envs/cloudspace` environment.

### Project Structure