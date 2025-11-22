MODEL="Qwen/Qwen2-VL-7B-Instruct"

echo "🔥 Starting A100 Optimized Server for Documents..."
echo "   - Precision: bfloat16 (Native Ampere)"
echo "   - Context: 32k tokens"
echo "   - Multi-Image: Enabled (Up to 10 pages per request)"

# --limit-mm-per-prompt image=10: CRITICAL! 
# By default vLLM might only allow 1 image. Your code sends multiple pages.
# --gpu-memory-utilization 0.95: Squeeze every bit of 40GB VRAM for context.

vllm serve $MODEL \
    --trust-remote-code \
    --dtype bfloat16 \
    --gpu-memory-utilization 0.95 \
    --max-model-len 32768 \
    --limit-mm-per-prompt '{"image": 10}' \
    --port 8000