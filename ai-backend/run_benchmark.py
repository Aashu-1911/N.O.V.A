import sys
import os
import time
import json
from typing import List, Dict, Any

# Ensure correct path resolution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.llm.service import LLMService
from services.llm.benchmark import run_benchmarked_stream, get_system_metrics

# Sample prompts reflecting N.O.V.A.'s workload
BENCHMARK_PROMPTS = [
    {"prompt": "Open Notepad", "expected_type": "intent"},
    {"prompt": "Search GitHub for React", "expected_type": "intent"},
    {"prompt": "Open VS Code and maximize it", "expected_type": "intent"},
    {"prompt": "Explain recursion", "expected_type": "text"},
    {"prompt": "Plan my day", "expected_type": "text"},
    {"prompt": "Message Harsh to come early tomorrow", "expected_type": "intent"},
    {"prompt": "Add task to study docker", "expected_type": "intent"},
    {"prompt": "Minimize Calculator", "expected_type": "intent"},
    {"prompt": "Restore Telegram", "expected_type": "intent"},
    {"prompt": "Search Google for weather in Seattle", "expected_type": "intent"}
]

def run_benchmark():
    print("=" * 60)
    print(" N.O.V.A. LLM Benchmark Runner")
    print("=" * 60)

    service = LLMService()
    
    # We will test both models: Default (Hermes) and Fallback (Qwen)
    providers = [
        ("Hermes 3", service.default_provider),
        ("Qwen 3", service.fallback_provider)
    ]
    
    all_results = {}
    
    for name, provider in providers:
        print(f"\nRunning benchmark for provider: {name} ({provider.model_name})...")
        # Ensure model is warmed up
        provider.initialize()
        
        results = []
        for i, item in enumerate(BENCHMARK_PROMPTS):
            p_text = item["prompt"]
            p_type = item["expected_type"]
            print(f"  [{i+1}/{len(BENCHMARK_PROMPTS)}] Prompt: {p_text!r}")
            
            # If it's an intent, request JSON
            kwargs = {}
            if p_type == "intent":
                kwargs["format"] = "json"
                
            response, metrics = run_benchmarked_stream(provider, p_text, **kwargs)
            results.append(metrics)
            
        all_results[name] = results

    # Generate Markdown Report
    report_lines = []
    report_lines.append("# N.O.V.A. LLM Provider Benchmark Report\n")
    report_lines.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for name in all_results:
        metrics_list = all_results[name]
        
        # Aggregate statistics
        total_prompts = len(metrics_list)
        successful_runs = sum(1 for m in metrics_list if m.error is None)
        valid_jsons = sum(1 for m in metrics_list if m.is_valid_json)
        avg_first_token = sum(m.first_token_latency for m in metrics_list) / total_prompts
        avg_total_latency = sum(m.total_latency for m in metrics_list) / total_prompts
        avg_throughput = sum(m.tokens_per_sec for m in metrics_list) / total_prompts
        max_ram = max(m.ram_used_mb_end - m.ram_used_mb_start for m in metrics_list)
        
        report_lines.append(f"## Provider: {name}")
        report_lines.append(f"- **Success Rate**: {successful_runs}/{total_prompts} ({successful_runs/total_prompts * 100:.1f}%)")
        report_lines.append(f"- **JSON Validity**: {valid_jsons} valid objects generated")
        report_lines.append(f"- **Average Time to First Token**: {avg_first_token:.3f}s")
        report_lines.append(f"- **Average Total Latency**: {avg_total_latency:.3f}s")
        report_lines.append(f"- **Average Throughput**: {avg_throughput:.1f} tokens/sec")
        report_lines.append(f"- **Peak RAM Increase**: {max_ram:.2f} MB\n")
        
        # Detailed Table
        report_lines.append("| Prompt | Success | JSON | Time to First Token | Total Latency | Throughput | RAM Δ |")
        report_lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for m in metrics_list:
            status = "✅" if m.error is None else "❌"
            json_status = "✅" if m.is_valid_json else "N/A"
            ram_delta = m.ram_used_mb_end - m.ram_used_mb_start
            report_lines.append(
                f"| {m.prompt} | {status} | {json_status} | {m.first_token_latency:.3f}s | {m.total_latency:.3f}s | {m.tokens_per_sec:.1f} t/s | {ram_delta:+.1f} MB |"
            )
        report_lines.append("\n")

    report_content = "\n".join(report_lines)
    
    # Save Report
    report_path = "benchmark_results.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print("\n" + "=" * 60)
    print(f"Benchmark finished. Results written to: {report_path}")
    print("=" * 60)
    print(report_content)

if __name__ == "__main__":
    run_benchmark()
