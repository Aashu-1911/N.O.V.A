import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from capabilities.base import ParsedCommand, BaseCapability
from capabilities.response import CapabilityResponse
from capabilities.registry import get_registered_capabilities

logger = logging.getLogger("NOVA_CapabilityRouter")

class CapabilityRouter:
    """N.O.V.A.'s central routing engine responsible for matching commands to capabilities."""

    def route(self, parsed: ParsedCommand, context: Dict[str, Any]) -> BaseCapability:
        """Finds the best capability to handle the command, or raises routing errors."""
        candidates = []
        for cap in get_registered_capabilities():
            conf = cap.confidence(parsed, context)
            if conf > 0.0:
                candidates.append((cap, conf))

        if not candidates:
            raise ValueError("No capable capability matches the command.")

        candidates.sort(key=lambda x: (x[1], x[0].priority()), reverse=True)
        best_cap, best_conf = candidates[0]

        if len(candidates) > 1:
            next_cap, next_conf = candidates[1]
            if next_conf == best_conf and next_cap.priority() == best_cap.priority():
                raise ValueError(f"Tied matching capabilities: {best_cap.name} and {next_cap.name}")

        return best_cap

    def route_and_dispatch(
        self,
        parsed_cmd: ParsedCommand,
        context: Dict[str, Any]
    ) -> CapabilityResponse:
        """Orchestrates the routing, health check, execution, verification, and logging of a request."""
        t0 = time.time()
        
        # 1. Calculate matching confidences
        candidates_raw = []
        for cap in get_registered_capabilities():
            conf = cap.confidence(parsed_cmd, context)
            if conf > 0.0:
                candidates_raw.append((cap, conf))
                
        candidates_log = [(c[0].name, c[1]) for c in candidates_raw]
        
        # Case A: No matching capabilities
        if not candidates_raw:
            duration = (time.time() - t0) * 1000
            res = CapabilityResponse(
                status="error",
                reply="I'm sorry, I don't know how to handle that request.",
                handled_by="CapabilityRouter",
                execution_time=duration,
                errors=["No capable module matched the parsed command."]
            )
            self._log_pipeline(parsed_cmd.raw_command, parsed_cmd, parsed_cmd, candidates_log, "None", "N/A", "N/A", "N/A", {}, res)
            return res
            
        # Sort candidates
        candidates_raw.sort(key=lambda x: (x[1], x[0].priority()), reverse=True)
        best_cap, best_conf = candidates_raw[0]
        
        # Case B: Tied capabilities matching the command
        if len(candidates_raw) > 1:
            next_cap, next_conf = candidates_raw[1]
            if next_conf == best_conf and next_cap.priority() == best_cap.priority():
                duration = (time.time() - t0) * 1000
                res = CapabilityResponse(
                    status="success",
                    reply=f"Multiple subsystems ({best_cap.name} and {next_cap.name}) could handle your request. Could you clarify what you would like to do?",
                    handled_by="CapabilityRouter",
                    execution_time=duration,
                    errors=["Tied capabilities matching the command."]
                )
                self._log_pipeline(parsed_cmd.raw_command, parsed_cmd, parsed_cmd, candidates_log, "None (Tie)", "N/A", "N/A", "N/A", {}, res)
                return res

        # Case C: Selected capability is not healthy
        if not best_cap.health():
            duration = (time.time() - t0) * 1000
            res = CapabilityResponse(
                status="error",
                reply=f"The subsystem responsible for this action ({best_cap.name}) is currently unavailable.",
                handled_by=best_cap.name,
                execution_time=duration,
                errors=["Capability health check failed."]
            )
            self._log_pipeline(parsed_cmd.raw_command, parsed_cmd, parsed_cmd, candidates_log, best_cap.name, "N/A", "N/A", "N/A", {}, res)
            return res

        # 2. Dispatch execution
        try:
            response = best_cap.execute(parsed_cmd, context)
            duration = (time.time() - t0) * 1000
            response.execution_time = duration
            response.handled_by = best_cap.name
            
            # Format verification text
            ver_text = "N/A"
            if response.verification_result is not None:
                ver_text = "Verified Successful" if response.verification_result else "Verification Failed"

            self._log_pipeline(
                original_cmd=parsed_cmd.raw_command,
                parsed_cmd=parsed_cmd,
                resolved_cmd=parsed_cmd,
                candidates=candidates_log,
                selected=best_cap.name,
                interpreter_output=response.payload.get("interpretation", "Success"),
                execution_log=response.payload.get("execution_summary", "Completed"),
                verification_log=ver_text,
                context_updates=response.context_updates,
                final_response=response
            )
            return response
            
        except Exception as e:
            duration = (time.time() - t0) * 1000
            res = CapabilityResponse(
                status="error",
                reply=f"Failed to execute command: {str(e)}",
                handled_by=best_cap.name,
                execution_time=duration,
                errors=[str(e)]
            )
            self._log_pipeline(parsed_cmd.raw_command, parsed_cmd, parsed_cmd, candidates_log, best_cap.name, "Error", "Failed", "N/A", {}, res)
            return res

    def _log_pipeline(
        self,
        original_cmd: str,
        parsed_cmd: ParsedCommand,
        resolved_cmd: ParsedCommand,
        candidates: List[Tuple[str, float]],
        selected: str,
        interpreter_output: Any,
        execution_log: Any,
        verification_log: Any,
        context_updates: Dict[str, Any],
        final_response: CapabilityResponse
    ) -> None:
        log_str = (
            "\n==================================================\n"
            "N.O.V.A. Execution Pipeline Log\n"
            f"1. Command:             {original_cmd}\n"
            f"2. Parsed Command:      verb={parsed_cmd.verb}, object={parsed_cmd.object}, scope={parsed_cmd.scope}\n"
            f"3. Resolved Context:    verb={resolved_cmd.verb}, object={resolved_cmd.object}, entities={resolved_cmd.entities}\n"
            f"4. Candidate Caps:      {candidates}\n"
            f"5. Selected Cap:        {selected}\n"
            f"6. Interpreter Output:  {interpreter_output}\n"
            f"7. Execution:           {execution_log}\n"
            f"8. Verification:        {verification_log}\n"
            f"9. Context Updates:     {context_updates}\n"
            f"10. Final Response:     {final_response.reply} (Status: {final_response.status})\n"
            "==================================================\n"
        )
        logger.info(log_str)
        print(log_str, flush=True)
