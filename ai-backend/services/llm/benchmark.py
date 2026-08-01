import time
import psutil
import subprocess
import logging
from typing import Dict, Any, Optional, Iterator, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkMetrics:
    model_name: str
    prompt: str
    first_token_latency: float
    total_latency: float
    tokens_per_sec: float
    completion_time: float
    prompt_time: float
    ram_used_mb_start: float
    ram_used_mb_end: float
    gpu_util_start: Optional[float] = None
    gpu_util_end: Optional[float] = None
    gpu_mem_used_mb_start: Optional[float] = None
    gpu_mem_used_mb_end: Optional[float] = None
    is_valid_json: bool = False
    error: Optional[str] = None

def get_system_metrics() -> Dict[str, Any]:
    """Gather current RAM usage of the process and system-wide GPU metrics if available."""
    metrics = {"ram_used_mb": 0.0, "gpu_util": None, "gpu_mem_used_mb": None}
    try:
        metrics["ram_used_mb"] = psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:
        pass
    try:
        # Try calling nvidia-smi to fetch GPU stats
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2.0
        )
        if result.returncode == 0 and result.stdout:
            parts = result.stdout.strip().split(",")
            if len(parts) >= 2:
                metrics["gpu_util"] = float(parts[0].strip())
                metrics["gpu_mem_used_mb"] = float(parts[1].strip())
    except Exception:
        pass
    return metrics

def run_benchmarked_stream(provider, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> Tuple[str, BenchmarkMetrics]:
    """Execute a stream request through the provider, timing tokens and measuring resource utilization."""
    start_metrics = get_system_metrics()
    start_time = time.time()
    
    first_token_time = None
    chunks = []
    error_str = None
    
    try:
        stream_iter = provider.stream(prompt, system_prompt=system_prompt, **kwargs)
        for chunk in stream_iter:
            if first_token_time is None:
                first_token_time = time.time()
            chunks.append(chunk)
    except Exception as e:
        error_str = str(e)
        logger.error(f"[Benchmark] Execution error on model {provider.model_name}: {e}")
        
    end_time = time.time()
    end_metrics = get_system_metrics()
    
    total_text = "".join(chunks)
    
    # Estimate tokens: 1 token ~ 4 characters
    char_count = len(total_text)
    estimated_tokens = max(1.0, char_count / 4.0)
    
    total_latency = end_time - start_time
    
    if first_token_time is not None:
        prompt_time = first_token_time - start_time
        completion_time = end_time - first_token_time
    else:
        prompt_time = total_latency
        completion_time = 0.0
        
    tokens_per_sec = estimated_tokens / max(0.01, completion_time if completion_time > 0 else total_latency)
    
    is_json = False
    if total_text.strip().startswith("{") and total_text.strip().endswith("}"):
        try:
            import json
            json.loads(total_text)
            is_json = True
        except Exception:
            pass
            
    metrics = BenchmarkMetrics(
        model_name=provider.model_name,
        prompt=prompt,
        first_token_latency=prompt_time,
        total_latency=total_latency,
        tokens_per_sec=tokens_per_sec if not error_str else 0.0,
        completion_time=completion_time,
        prompt_time=prompt_time,
        ram_used_mb_start=start_metrics["ram_used_mb"],
        ram_used_mb_end=end_metrics["ram_used_mb"],
        gpu_util_start=start_metrics["gpu_util"],
        gpu_util_end=end_metrics["gpu_util"],
        gpu_mem_used_mb_start=start_metrics["gpu_mem_used_mb"],
        gpu_mem_used_mb_end=end_metrics["gpu_mem_used_mb"],
        is_valid_json=is_json,
        error=error_str
    )
    
    return total_text, metrics
