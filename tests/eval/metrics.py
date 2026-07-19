import json
import litellm
from pydantic import BaseModel


class _Verdict(BaseModel):
    score: int  # 1-5
    explanation: str


def evaluate(instance):
    reference = instance.get("reference")
    rubric = (
        "Grade the agent's final response on a 1-5 scale (1 poor, 5 excellent) for "
        "accuracy, relevance, and clarity."
    )
    if reference:
        rubric += (
            " The response should agree with the expected answer below; penalize "
            "factual disagreement with it."
        )
    prompt = (
        f"You are an expert QA evaluator for an enterprise AI assistant. {rubric}\n"
        f"User Prompt: {instance.get('prompt', '')}\n"
        f"Final Response: {instance.get('response', '')}\n"
    )
    if reference:
        prompt += f"Expected Answer (ground truth): {reference}\n"
    prompt += f"Full Agent Trace: {instance.get('agent_data', '')}\n"

    system_instruction = (
        "You are an expert QA evaluator. Output a JSON object with exactly two fields:\n"
        "  'score': an integer from 1 to 5\n"
        "  'explanation': a string explaining your score\n"
    )
    response = litellm.completion(
        model="groq/llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    content = response.choices[0].message.content
    try:
        verdict_dict = json.loads(content)
        verdict = _Verdict.model_validate(verdict_dict)
    except Exception:
        return {"score": 0, "explanation": content or "Failed to parse model output"}

    return {"score": max(1, min(5, verdict.score)), "explanation": verdict.explanation}
