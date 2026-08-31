import json
import logging
import re
import httpx
from typing import Dict, Any
from app.core.config import settings
from app.core.cache import investigation_cache
from app.services.llm.prompt_templates import SRE_SYSTEM_PROMPT, generate_investigation_user_prompt

logger = logging.getLogger(__name__)

def _fallback_response(reason: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
    failing_count = evidence.get("summary", {}).get("failing_pods_count", 0)
    warning_count = evidence.get("summary", {}).get("warning_events_count", 0)
    
    return {
        "ai_available": False,
        "root_cause": f"AI reasoning engine unavailable ({reason}). Captured raw cluster evidence: {failing_count} failing pods, {warning_count} warning events.",
        "suggested_fix": "Review the raw container logs, pod conditions, and Kubernetes event streams in the Diagnostic Evidence tab below.",
        "suggested_command": "kubectl get pods,events -n " + str(evidence.get("summary", {}).get("namespace", "default")),
        "confidence_score": 0,
        "evidence_used": [f"Raw telemetry payload for namespace '{evidence.get('summary', {}).get('namespace', 'default')}'"],
        "preventive_recommendation": "Configure GROQ_API_KEY environment variable or verify API quota.",
        "raw_evidence": evidence
    }

async def analyze_evidence_with_groq(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sends aggregated evidence payload to Groq's chat completions API and parses structured SRE reasoning.
    Includes 5-minute caching, defensive JSON parsing, model fallback, and graceful degradation.
    """
    # 1. Check TTL cache
    cached_result = investigation_cache.get(evidence)
    if cached_result:
        logger.info("Returning cached SRE investigation reasoning.")
        return cached_result

    # 2. Check API key
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.strip() == "":
        logger.warning("GROQ_API_KEY not configured. Falling back to raw telemetry output.")
        result = _fallback_response("GROQ_API_KEY missing", evidence)
        return result

    namespace = evidence.get("summary", {}).get("namespace", "default")
    user_prompt = generate_investigation_user_prompt(namespace, json.dumps(evidence, indent=2))

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Helper function to call Groq API endpoint
    async def _call_groq_model(model_name: str) -> Dict[str, Any]:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SRE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=settings.GROQ_TIMEOUT_SECONDS) as client:
            resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data

    response_json = None
    used_model = settings.GROQ_MODEL

    # Try Primary Model
    try:
        groq_data = await _call_groq_model(settings.GROQ_MODEL)
        content_str = groq_data["choices"][0]["message"]["content"]
        response_json = json.loads(content_str)
    except Exception as primary_err:
        logger.warning(f"Groq primary model '{settings.GROQ_MODEL}' failed: {primary_err}. Trying fallback model '{settings.GROQ_FALLBACK_MODEL}'...")
        try:
            used_model = settings.GROQ_FALLBACK_MODEL
            groq_data = await _call_groq_model(settings.GROQ_FALLBACK_MODEL)
            content_str = groq_data["choices"][0]["message"]["content"]
            response_json = json.loads(content_str)
        except Exception as fallback_err:
            logger.error(f"Both primary and fallback Groq LLM calls failed: {fallback_err}")
            return _fallback_response(f"Groq API Error: {str(fallback_err)}", evidence)

    # Validate output structure defensively
    try:
        validated_result = {
            "ai_available": True,
            "model_used": used_model,
            "root_cause": str(response_json.get("root_cause", "Root cause undetermined.")),
            "suggested_fix": str(response_json.get("suggested_fix", "No fix provided.")),
            "suggested_command": response_json.get("suggested_command"),
            "confidence_score": int(response_json.get("confidence_score", 50)),
            "evidence_used": list(response_json.get("evidence_used", [])),
            "preventive_recommendation": str(response_json.get("preventive_recommendation", "")),
            "raw_evidence": evidence
        }

        # Cache valid response
        investigation_cache.set(evidence, validated_result)
        return validated_result

    except Exception as parse_err:
        logger.error(f"Failed to parse LLM JSON output structure: {parse_err}")
        return _fallback_response("JSON Parse Failure", evidence)
