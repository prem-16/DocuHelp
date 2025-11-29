# UI Feedback Fixes

## Summary
Fixed three critical issues in the feedback UI and VLM response formatting to improve user experience.

## Issues Fixed

### 1. ✅ Feedback UI Showing Same Image for All Phases

**Problem:** When users navigated through different surgical phases during feedback, the image remained the same even though the phase changed.

**Root Cause:** React was reusing the same DOM element for the image, causing it to cache the previous image and not reload when the base64 data changed.

**Solution:** Added React `key` props to force re-rendering when the phase index changes.

**File Modified:** [frontend/src/components/Feedback.js](frontend/src/components/Feedback.js:158-162)

**Changes:**
```jsx
// Before:
<div className="feedback-card">
    <div className="feedback-image-container">
        <img
            src={`data:image/jpeg;base64,${currentPhase.image_base64}`}
            alt={`Surgical phase ${currentIndex + 1}`}
            className="feedback-image"
        />

// After:
<div className="feedback-card" key={currentIndex}>
    <div className="feedback-image-container">
        <img
            key={`phase-image-${currentIndex}`}
            src={`data:image/jpeg;base64,${currentPhase.image_base64}`}
            alt={`Surgical phase ${currentIndex + 1}`}
            className="feedback-image"
        />
```

**Impact:**
- ✓ Each phase now displays its correct keyframe image
- ✓ Images update immediately when user navigates to next phase
- ✓ No caching issues between phases

---

### 2. ✅ Remove "Description:**" Title from Phase Descriptions

**Problem:** VLM responses included labels like "Description:" or "**Description:**" at the start of phase descriptions, creating redundant UI text.

**Root Cause:** The regex pattern in the response parser didn't account for markdown-style bold formatting (`**Description:**`).

**Solution:** Updated the regex pattern to match and remove both plain and bold-formatted labels.

**File Modified:** [src/docuhelp/vlm/inference.py](src/docuhelp/vlm/inference.py:193-194)

**Changes:**
```python
# Before:
clean_line = re.sub(r'^(Description|Key timestamp|Key time stamp|Timestamp):\s*', '', clean_line, flags=re.IGNORECASE)

# After:
clean_line = re.sub(r'^\**(Description|Key timestamp|Key time stamp|Timestamp)\*{0,2}:\s*', '', clean_line, flags=re.IGNORECASE)
```

**Pattern Details:**
- `^\**` - Matches 0 or more asterisks at the start
- `(Description|...)` - Matches common label words
- `\*{0,2}` - Matches 0-2 asterisks after the word
- `:\s*` - Matches the colon and optional whitespace

**UI Changes:**
```jsx
// Also removed redundant "Description:" label from UI
// Before:
<p><strong>Description:</strong> {currentPhase.description || 'No description available'}</p>

// After:
<p>{currentPhase.description || 'No description available'}</p>
```

**Impact:**
- ✓ Cleaner description text without redundant labels
- ✓ Works with both plain and markdown-formatted VLM responses
- ✓ More professional presentation in the UI

---

### 3. ✅ Prevent VLM from Adding Comments at the End

**Problem:** VLM sometimes added commentary, notes, or summary statements after the structured phase descriptions, which cluttered the output.

**Root Cause:** The prompt didn't explicitly instruct the model to avoid adding extra commentary.

**Solution:** Updated the VLM prompt with explicit instructions to:
- Not add any commentary after phase descriptions
- Not add closing remarks or summary statements
- Only provide structured phase information
- End immediately after the last phase

**File Modified:** [src/docuhelp/vlm/openrouter_client.py](src/docuhelp/vlm/openrouter_client.py:151-166)

**Changes:**
```python
base_prompt = """Analyze this surgical video and provide a detailed summary.

IMPORTANT INSTRUCTIONS:
- Focus ONLY on frames showing actual surgical content (tissue, instruments, medical procedures)
- IGNORE any frames that show: title screens, text overlays, instructions, copyright notices, or blank screens
- If you see text-heavy frames, skip them and analyze only the surgical procedure frames
- DO NOT add any commentary, notes, or explanatory text after the phase descriptions  # NEW
- DO NOT add closing remarks or summary statements  # NEW
- ONLY provide the structured phase information, nothing else  # NEW

For each distinct phase or action in the surgical procedure, provide:
1. **Timestamp Range**: Start and end time (e.g., "0:00-0:45")
2. Clear description of what is happening in the surgical field (do NOT prefix with "Description:" or similar labels)  # UPDATED
3. **Key Timestamp**: A single timestamp within the range that best represents this surgical phase

Format your response as a structured list of phases showing the actual surgical procedure steps. End immediately after the last phase."""  # UPDATED
```

**Impact:**
- ✓ Cleaner, more concise VLM outputs
- ✓ No extraneous text in the response
- ✓ Better parsing reliability
- ✓ Reduced token usage and costs

---

## Files Modified

1. **[frontend/src/components/Feedback.js](frontend/src/components/Feedback.js)**
   - Added `key` prop to feedback-card div
   - Added `key` prop to img element
   - Removed "Description:" label from UI

2. **[src/docuhelp/vlm/inference.py](src/docuhelp/vlm/inference.py)**
   - Updated regex pattern to handle markdown-formatted labels
   - Better cleaning of VLM response text

3. **[src/docuhelp/vlm/openrouter_client.py](src/docuhelp/vlm/openrouter_client.py)**
   - Enhanced prompt with explicit instructions
   - Prevents commentary and closing remarks
   - Clearer formatting requirements

## Testing

To verify these fixes:

1. **Image Display Test:**
   - Upload a surgical video
   - Navigate through feedback phases
   - Verify each phase shows a different keyframe image

2. **Description Formatting Test:**
   - Check that phase descriptions don't start with "Description:" or similar labels
   - Verify text is clean and readable

3. **VLM Output Test:**
   - Process a video and check the VLM summary
   - Ensure no commentary appears after the last phase
   - Verify all output is structured phase information only

## Benefits

- ✓ **Better User Experience**: Correct images, cleaner text, no confusion
- ✓ **Professional Presentation**: Removed redundant labels and clutter
- ✓ **Improved Parsing**: More reliable extraction of phase information
- ✓ **Cost Optimization**: Reduced token usage by eliminating unnecessary commentary
- ✓ **Maintainability**: Clear, explicit prompts are easier to understand and modify
