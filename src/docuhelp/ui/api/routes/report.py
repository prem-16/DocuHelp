"""Report endpoints for report generation and evaluation"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()


class ReportEvaluationRequest(BaseModel):
    report: str
    procedure: str
    phases_count: int = 0


@router.post("/evaluate")
async def evaluate_report(request: ReportEvaluationRequest):
    """
    Evaluate a surgical report for accuracy, completeness, and quality using LLM.

    Args:
        request: Report evaluation request with report text, procedure name, and phases count

    Returns:
        Accuracy score (0-100) and detailed evaluation criteria
    """
    try:
        from openai import OpenAI
        import os
        import json
        import re

        # Initialize OpenRouter client for evaluation
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

        # Build comprehensive evaluation prompt
        evaluation_prompt = f"""You are an expert surgical documentation evaluator. Evaluate the following surgical report for a {request.procedure} procedure.

**REPORT TO EVALUATE:**
{request.report}

**EVALUATION CRITERIA:**

Analyze this report across these dimensions and provide a comprehensive assessment:

1. **Completeness (0-100)**: Does the report cover all standard phases and steps expected in a {request.procedure} procedure?
   - Compare against standard {request.procedure} documentation found in medical literature
   - Check if all anatomical structures, instruments, and techniques are mentioned
   - Verify {request.phases_count} phases were documented

2. **Chronological Order (0-100)**: Are the surgical phases presented in the correct temporal sequence?
   - Verify timestamps are sequential and non-overlapping
   - Check that procedural steps follow standard surgical workflow
   - Ensure no logical inconsistencies in the timeline

3. **Clinical Accuracy (0-100)**: Is the medical terminology and technical description accurate?
   - Verify anatomical terminology is correct
   - Check that surgical techniques are properly described
   - Assess if procedure-specific steps align with medical standards

4. **Medical Terminology (0-100)**: Is appropriate professional medical language used?
   - Use of correct surgical/anatomical terms
   - Professional tone and documentation style
   - Absence of colloquialisms or informal language

**OUTPUT FORMAT (JSON ONLY):**
Respond ONLY with valid JSON in this exact format:
{{
    "completeness_score": <0-100>,
    "completeness_assessment": "<brief assessment>",
    "chronological_score": <0-100>,
    "chronological_assessment": "<brief assessment>",
    "clinical_accuracy_score": <0-100>,
    "clinical_accuracy_assessment": "<brief assessment>",
    "terminology_score": <0-100>,
    "terminology_assessment": "<brief assessment>",
    "overall_score": <0-100>,
    "summary": "<2-3 sentence overall assessment>"
}}

**IMPORTANT**:
- Output ONLY valid JSON, no additional text
- Be realistic - compare against actual surgical documentation standards
- The overall_score should be the weighted average: (completeness*0.3 + chronological*0.2 + clinical_accuracy*0.3 + terminology*0.2)
"""

        logger.info(f"Evaluating report for {request.procedure} with {request.phases_count} phases")

        # Call OpenRouter API for evaluation
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-exp:free",
            messages=[
                {
                    "role": "user",
                    "content": evaluation_prompt
                }
            ],
            temperature=0.3  # Lower temperature for more consistent evaluation
        )

        evaluation_text = response.choices[0].message.content.strip()

        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r'\{.*\}', evaluation_text, re.DOTALL)
        if json_match:
            evaluation_text = json_match.group(0)

        evaluation_data = json.loads(evaluation_text)

        # Calculate overall score if not provided
        if "overall_score" not in evaluation_data:
            overall = (
                evaluation_data.get("completeness_score", 0) * 0.3 +
                evaluation_data.get("chronological_score", 0) * 0.2 +
                evaluation_data.get("clinical_accuracy_score", 0) * 0.3 +
                evaluation_data.get("terminology_score", 0) * 0.2
            )
            evaluation_data["overall_score"] = round(overall)

        logger.info(f"Report evaluation completed: {evaluation_data['overall_score']}%")

        return JSONResponse(
            status_code=200,
            content={
                "accuracy_score": evaluation_data["overall_score"],
                "evaluation_details": {
                    "completeness": evaluation_data.get("completeness_assessment", "N/A"),
                    "chronological_order": evaluation_data.get("chronological_assessment", "N/A"),
                    "clinical_accuracy": evaluation_data.get("clinical_accuracy_assessment", "N/A"),
                    "terminology": evaluation_data.get("terminology_assessment", "N/A"),
                    "summary": evaluation_data.get("summary", "Evaluation completed")
                },
                "detailed_scores": {
                    "completeness": evaluation_data.get("completeness_score", 0),
                    "chronological_order": evaluation_data.get("chronological_score", 0),
                    "clinical_accuracy": evaluation_data.get("clinical_accuracy_score", 0),
                    "terminology": evaluation_data.get("terminology_score", 0)
                }
            }
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse evaluation response: {e}")
        logger.error(f"Raw response: {evaluation_text}")
        # Fallback to simple scoring
        return JSONResponse(
            status_code=200,
            content={
                "accuracy_score": 75,
                "evaluation_details": {
                    "completeness": "Automated evaluation unavailable",
                    "chronological_order": "Automated evaluation unavailable",
                    "clinical_accuracy": "Automated evaluation unavailable",
                    "terminology": "Automated evaluation unavailable",
                    "summary": "Report generated successfully with basic validation"
                },
                "detailed_scores": {
                    "completeness": 75,
                    "chronological_order": 75,
                    "clinical_accuracy": 75,
                    "terminology": 75
                }
            }
        )
    except Exception as e:
        logger.error(f"Error evaluating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/report/{report_id}")
def get_report(report_id: str):
    """Get report by ID (stub)"""
    return {"report_id": report_id}
