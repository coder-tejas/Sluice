FROM ghcr.io/ggml-org/llama.cpp:server

RUN mkdir -p /models && apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && curl -L --fail -o /models/qwen2.5-0.5b-instruct-q4_k_m.gguf \
    https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf \
 && rm -rf /var/lib/apt/lists/*

CMD ["-m", "/models/qwen2.5-0.5b-instruct-q4_k_m.gguf", \
     "--host", "0.0.0.0", "--port", "8080", \
     "--alias", "qwen2.5-0.5b-instruct", \
     "--ctx-size", "4096", "--threads", "4"]