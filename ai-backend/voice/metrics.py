import threading
import time
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

@dataclass
class RequestMetrics:
    req_id: str = "unknown"
    transcript: str = ""
    clean_transcript: str = ""
    validation_score: float = 0.0
    intent: str = "unknown"
    intent_confidence: float = 0.5
    entities: dict = field(default_factory=dict)
    handler: str = "None"
    execution_time: float = 0.0
    reply_length: int = 0
    tts_queue_length: int = 0
    synthesis_time: float = 0.0
    playback_time: float = 0.0
    total_latency: float = 0.0
    
    # Whisper details
    avg_logprob: float = 0.0
    no_speech_prob: float = 0.0
    words_detected: int = 0
    validation_reason: str = ""
    acceptance_reason: str = ""
    
    # Timings
    pipeline_start: float = 0.0
    transcription_start: float = 0.0
    transcription_end: float = 0.0
    execution_start: float = 0.0
    execution_end: float = 0.0
    synthesis_start: float = 0.0
    synthesis_end: float = 0.0
    playback_start: float = 0.0
    playback_end: float = 0.0


class VoiceMetrics:
    def __init__(self):
        self.commands: List[Dict[str, Any]] = []
        self.retry_count = 0
        self.lock = threading.Lock()
        self.command_counter = 0

    def add_command(
        self,
        accepted: bool,
        transcription_time: float,
        synthesis_time: float,
        execution_time: float,
        total_latency: float
    ):
        with self.lock:
            self.commands.append({
                'accepted': accepted,
                'transcription_time': transcription_time,
                'synthesis_time': synthesis_time,
                'execution_time': execution_time,
                'total_latency': total_latency
            })
            if len(self.commands) > 100:
                self.commands.pop(0)
            self.command_counter += 1
            
            # Print summary every 25 commands
            if self.command_counter % 25 == 0:
                self.print_summary()

    def increment_retries(self, count: int = 1):
        with self.lock:
            self.retry_count += count

    def print_summary(self):
        if not self.commands:
            return
        
        last_100 = self.commands
        total = len(last_100)
        accepted = sum(1 for c in last_100 if c['accepted'])
        rejected = total - accepted
        failure_rate = (rejected / total) * 100 if total > 0 else 0.0
        
        avg_trans = sum(c['transcription_time'] for c in last_100 if c['transcription_time'] > 0) / sum(1 for c in last_100 if c['transcription_time'] > 0) if any(c['transcription_time'] > 0 for c in last_100) else 0.0
        avg_synth = sum(c['synthesis_time'] for c in last_100 if c['synthesis_time'] > 0) / sum(1 for c in last_100 if c['synthesis_time'] > 0) if any(c['synthesis_time'] > 0 for c in last_100) else 0.0
        avg_exec = sum(c['execution_time'] for c in last_100 if c['execution_time'] > 0) / sum(1 for c in last_100 if c['execution_time'] > 0) if any(c['execution_time'] > 0 for c in last_100) else 0.0
        avg_latency = sum(c['total_latency'] for c in last_100 if c['total_latency'] > 0) / sum(1 for c in last_100 if c['total_latency'] > 0) if any(c['total_latency'] > 0 for c in last_100) else 0.0
        
        print("\n" + "=" * 50)
        print("          N.O.V.A. VOICE PIPELINE STATISTICS")
        print(f"          Last {total} commands")
        print("=" * 50)
        print(f"Accepted Commands:         {accepted}")
        print(f"Rejected Commands:         {rejected}")
        print(f"Failure Rate:              {failure_rate:.1f}%")
        print(f"Avg Transcription Time:    {avg_trans:.3f} s")
        print(f"Avg Synthesis Time:        {avg_synth:.3f} s")
        print(f"Avg Execution Time:        {avg_exec:.3f} s")
        print(f"Avg Total Latency:         {avg_latency:.3f} s")
        print(f"Total Retry Count:         {self.retry_count}")
        print("=" * 50 + "\n", flush=True)


VOICE_METRICS = VoiceMetrics()
request_context = threading.local()


def log_accepted_request(metrics: RequestMetrics):
    trans_time = metrics.transcription_end - metrics.transcription_start
    VOICE_METRICS.add_command(
        accepted=True,
        transcription_time=trans_time if trans_time > 0 else 0.0,
        synthesis_time=metrics.synthesis_time,
        execution_time=metrics.execution_time,
        total_latency=metrics.total_latency
    )
    
    print(f"[INSTRUMENTATION] ==================================================")
    print(f"[INSTRUMENTATION]               VOICE PIPELINE LOG")
    print(f"[INSTRUMENTATION] ==================================================")
    print(f"[INSTRUMENTATION] Request ID:          {metrics.req_id}")
    print(f"[INSTRUMENTATION] Transcript:          {metrics.transcript!r}")
    print(f"[INSTRUMENTATION] Validation Score:    {metrics.validation_score:.3f}")
    print(f"[INSTRUMENTATION] Intent:              {metrics.intent}")
    print(f"[INSTRUMENTATION] Entities:            {metrics.entities}")
    print(f"[INSTRUMENTATION] Handler:             {metrics.handler}")
    print(f"[INSTRUMENTATION] Execution Time:      {metrics.execution_time:.3f} s")
    print(f"[INSTRUMENTATION] Reply Length:        {metrics.reply_length} chars")
    print(f"[INSTRUMENTATION] TTS Queue Length:    {metrics.tts_queue_length}")
    print(f"[INSTRUMENTATION] Synthesis Time:      {metrics.synthesis_time:.3f} s")
    print(f"[INSTRUMENTATION] Playback Time:       {metrics.playback_time:.3f} s")
    print(f"[INSTRUMENTATION] Total Latency:       {metrics.total_latency:.3f} s")
    print(f"[INSTRUMENTATION] --------------------------------------------------")
    print(f"[INSTRUMENTATION] Whisper logprob:     {metrics.avg_logprob:.6f}")
    print(f"[INSTRUMENTATION] Speech prob:         {metrics.no_speech_prob:.6f} (silence prob)")
    print(f"[INSTRUMENTATION] Words detected:      {metrics.words_detected}")
    print(f"[INSTRUMENTATION] Validation reason:   {metrics.validation_reason}")
    print(f"[INSTRUMENTATION] Acceptance reason:   {metrics.acceptance_reason}")
    print(f"[INSTRUMENTATION] ==================================================", flush=True)

    from config import VOICE_CONFIG
    if VOICE_CONFIG.get("diagnostics", False):
        print("\n==========================")
        print("VOICE DIAGNOSTICS")
        print(f"Transcript:          {metrics.clean_transcript}")
        print(f"Validation score:    {metrics.validation_score:.3f}")
        print(f"Intent confidence:   {metrics.intent_confidence:.3f}")
        print(f"Execution latency:   {metrics.execution_time:.3f} s")
        print(f"Whisper latency:     {trans_time:.3f} s")
        print(f"Piper latency:       {metrics.synthesis_time:.3f} s")
        print(f"Handler latency:     {metrics.execution_time:.3f} s")
        print(f"Total latency:       {metrics.total_latency:.3f} s")
        print("==========================\n", flush=True)
