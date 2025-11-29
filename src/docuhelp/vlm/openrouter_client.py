"""
OpenRouter API client for VLM inference.
Uses Gemini 2.5 Flash for video summarization via base64 frames.
"""
import os
import logging
import time
from typing import List, Dict, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenRouterVLM:
    """Client for OpenRouter VLM inference using Gemini 2.5 Flash."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key (uses OPENROUTER_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable.")

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )

        # Using Gemini Flash 2.0 - free tier with vision capabilities
        # Alternative options: "meta-llama/llama-3.2-11b-vision-instruct:free", "google/gemini-2.0-flash-thinking-exp:free"
        self.model = "google/gemini-2.0-flash-exp:free"
        logger.info(f"OpenRouter VLM client initialized with model: {self.model}")

    def analyze_video_frames(
        self,
        frames: List[Dict[str, any]],
        prompt: Optional[str] = None,
        procedure: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Analyze video frames using Gemini VLM.

        Args:
            frames: List of frame dictionaries with base64_image and timestamp
            prompt: Custom prompt (uses default if None)
            procedure: Surgical procedure name for context

        Returns:
            Dictionary containing:
            {
                "summary": "VLM response text",
                "latency": 2.5,  # seconds
                "frames_analyzed": 120,
                "model": "google/gemini-2.5-flash"
            }
        """
        try:
            logger.info(f"Analyzing {len(frames)} frames with OpenRouter VLM")

            # Build prompt
            if prompt is None:
                prompt = self._build_default_prompt(procedure)

            # Build message content with frames
            message_content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]

            # Add frames as base64 images
            for frame in frames:
                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{frame['base64_image']}"
                    }
                })

            # Call OpenRouter API with retry logic for rate limits
            start_time = time.time()

            max_retries = 5
            base_delay = 2  # seconds

            for attempt in range(max_retries):
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "user",
                                "content": message_content
                            }
                        ]
                    )
                    break  # Success, exit retry loop

                except Exception as e:
                    error_str = str(e)

                    # Check if it's a 429 rate limit error
                    if "429" in error_str or "rate" in error_str.lower():
                        if attempt < max_retries - 1:
                            # Calculate exponential backoff delay
                            delay = base_delay * (2 ** attempt)
                            logger.warning(f"Rate limit hit (attempt {attempt + 1}/{max_retries}). Retrying in {delay}s...")
                            time.sleep(delay)
                            continue
                        else:
                            logger.error(f"Max retries ({max_retries}) reached for rate limit error")
                            raise
                    else:
                        # Not a rate limit error, raise immediately
                        raise

            end_time = time.time()
            latency = end_time - start_time

            # Extract response
            response_text = completion.choices[0].message.content

            logger.info(f"VLM inference completed in {latency:.2f}s")

            return {
                "summary": response_text,
                "latency": round(latency, 2),
                "frames_analyzed": len(frames),
                "model": self.model,
                "procedure": procedure
            }

        except Exception as e:
            logger.error(f"Error in VLM inference: {e}")
            raise

    def _build_default_prompt(self, procedure: Optional[str] = None) -> str:
        """
        Build default prompt for surgical documentation.

        Args:
            procedure: Surgical procedure name

        Returns:
            Prompt string optimized for clinical and legal documentation requirements
        """
        base_prompt = """You are an AI surgical documentation assistant. Your task is to generate a comprehensive, clinically accurate, and legally compliant surgical report from this video.

CRITICAL INSTRUCTIONS:
- Generate ONLY the structured report below
- Do NOT include any conversational text, greetings, or acknowledgments
- Do NOT write "Okay, I'm ready" or similar phrases
- Start directly with the report sections
- Focus ONLY on frames showing actual surgical content (tissue, instruments, medical procedures)
- IGNORE title screens, text overlays, instructions, copyright notices, or blank screens
- Document ALL significant clinical events, techniques, and observations
- Maintain objectivity and clinical accuracy
- Use appropriate medical terminology

REQUIRED DOCUMENTATION STRUCTURE:

**PROCEDURE OVERVIEW**
- Brief summary of the overall procedure performed
- Key anatomical structures involved
- Overall duration and completion status

**SURGICAL PHASES**
CRITICAL REQUIREMENT: You MUST identify and document MULTIPLE distinct surgical phases.
- Minimum 3 phases (always)
- For videos longer than 4 minutes: at least 5 phases
- Break down the procedure into separate temporal phases based on the video frames

EXACT FORMAT TO FOLLOW (copy this structure):

1. **Timestamp Range**: 0:00-0:45
2. [Describe what happens in this phase - surgical actions, instruments, structures]
3. **Key Timestamp**: 0:23

1. **Timestamp Range**: 0:45-1:30
2. [Describe what happens in this phase - surgical actions, instruments, structures]
3. **Key Timestamp**: 1:08

1. **Timestamp Range**: 1:30-2:15
2. [Describe what happens in this phase - surgical actions, instruments, structures]
3. **Key Timestamp**: 1:53

[Continue for ALL phases...]

MANDATORY RULES:
1. Use ACTUAL timestamps from the frames (not made up times)
2. Format MUST be "M:SS-M:SS" (e.g., "0:00-0:45", "1:20-2:15")
3. Each phase = approximately 45-90 seconds
4. Phases must be sequential and non-overlapping
5. NO timestamps in the description text
6. NO labels like "Description:" or "Phase Description:"
7. NEVER use "Full video" as a timestamp range

**CLINICAL OBSERVATIONS**
- Tissue condition and anatomical findings
- Hemostasis and bleeding control measures
- Any complications or unexpected findings
- Quality of visualization and surgical field

**ACCOUNTABILITY MARKERS**
- Critical decision points documented
- Technique modifications or adjustments made
- Safety checks performed (if visible)
- Completeness of each surgical step

**TECHNICAL QUALITY**
- Adequacy of exposure and visualization
- Precision of surgical technique
- Proper instrument handling

DO NOT include:
- Speculative medical advice or diagnoses
- Commentary on surgeon competence
- Closing remarks or subjective opinions
- Non-clinical observations

Format as a structured, professional surgical report suitable for medical records."""

        if procedure:
            base_prompt = f"""**PROCEDURE TYPE**: {procedure}

{base_prompt}

**PROCEDURE-SPECIFIC REQUIREMENTS**:
Document all standard steps for {procedure} including:
- Standard anatomical approach and exposure
- Key procedural milestones
- Expected variations or technique modifications
- Critical safety steps specific to {procedure}"""

        return base_prompt

    def analyze_with_custom_prompt(
        self,
        frames: List[Dict[str, any]],
        custom_prompt: str
    ) -> Dict[str, any]:
        """
        Analyze frames with a fully custom prompt.

        Args:
            frames: List of frame dictionaries
            custom_prompt: Custom prompt text

        Returns:
            Analysis results dictionary
        """
        return self.analyze_video_frames(frames, prompt=custom_prompt)

    def refine_phase_description(
        self,
        frame_base64: str,
        current_description: str,
        user_feedback: str,
        procedure: str
    ) -> str:
        """
        Refine a phase description based on user feedback.

        Args:
            frame_base64: Base64 encoded image of the key frame
            current_description: Current AI-generated description
            user_feedback: User's correction/feedback
            procedure: Surgical procedure name

        Returns:
            Refined description text
        """
        try:
            logger.info(f"Refining phase description with user feedback: {user_feedback[:100]}")

            # Build refinement prompt
            refinement_prompt = f"""You are refining a surgical phase description based on expert feedback.

**CONTEXT**:
- Procedure: {procedure}
- Current AI Description: "{current_description}"
- Expert Feedback: "{user_feedback}"

**YOUR TASK**:
Generate a new, improved description that:
1. Incorporates the expert's feedback and corrections
2. Maintains clinical accuracy and professional terminology
3. Describes what is actually visible in this surgical frame
4. Is concise (1-2 sentences, no more than 150 words)
5. Focuses on surgical actions, instruments, anatomical structures, and techniques

**IMPORTANT**:
- Do NOT include timestamps
- Do NOT include labels like "Description:", "Refined:", etc.
- Output ONLY the refined description text
- Use appropriate medical terminology
- Be objective and clinically accurate

**REFINED DESCRIPTION**:"""

            # Build message content with frame
            message_content = [
                {
                    "type": "text",
                    "text": refinement_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{frame_base64}"
                    }
                }
            ]

            # Call OpenRouter API
            start_time = time.time()
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": message_content
                    }
                ]
            )
            end_time = time.time()

            # Extract refined description
            refined_text = completion.choices[0].message.content.strip()

            # Clean up any remaining artifacts
            refined_text = refined_text.replace("**REFINED DESCRIPTION**:", "").strip()
            refined_text = refined_text.replace("Refined Description:", "").strip()
            refined_text = refined_text.replace("Description:", "").strip()

            logger.info(f"Phase refinement completed in {end_time - start_time:.2f}s")
            logger.info(f"Refined description: {refined_text[:200]}")

            return refined_text

        except Exception as e:
            logger.error(f"Error refining phase description: {e}")
            # Fallback: combine current description with user feedback
            return f"{current_description} {user_feedback}"


def create_vlm_client(api_key: Optional[str] = None) -> OpenRouterVLM:
    """
    Factory function to create OpenRouter VLM client.

    Args:
        api_key: Optional API key

    Returns:
        OpenRouterVLM instance
    """
    return OpenRouterVLM(api_key=api_key)
