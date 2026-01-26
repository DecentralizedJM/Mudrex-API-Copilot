# RAG Pipeline Hallucination Analysis Report

**Date:** 2026-01-26  
**Issue:** Bot hallucinates when answering out-of-context questions  
**Priority:** HIGH - Affects user trust and accuracy

---

## Executive Summary

The Mudrex API bot's RAG pipeline has several critical flaws that cause hallucinations when questions fall outside the documented knowledge base. The bot currently falls back to Google Search grounding, which can return generic API information that doesn't match Mudrex's specific implementation, leading to incorrect answers.

---

## Root Causes

### 1. **Google Search Grounding Fallback (CRITICAL)**

**Location:** `src/rag/pipeline.py:102-112`

**Problem:**
When no documents are retrieved above the similarity threshold, the pipeline automatically falls back to `generate_response_with_grounding()`, which uses Google Search. This is problematic because:

- Google Search returns **generic** API documentation (Binance, Coinbase, etc.)
- The model synthesizes answers from this generic info, assuming it applies to Mudrex
- No explicit instruction to say "I don't know" if Mudrex-specific info isn't found
- Users get confident-sounding but **wrong** answers

**Example Flow:**
```
User: "How do I set up webhooks?"
→ Vector search: No docs (Mudrex doesn't have webhooks)
→ Fallback: Google Search → Generic webhook setup guides
→ Model: "Here's how to set up webhooks..." (WRONG - Mudrex doesn't support this)
```

**Current Code:**
```python
if not retrieved_docs:
    # API-related but RAG empty: use Google Search grounding
    logger.info("No RAG docs; using Google Search grounding for API-related query")
    answer = self.gemini_client.generate_response_with_grounding(
        question, [], chat_history, mcp_context
    )
```

### 2. **Weak "I Don't Know" Enforcement**

**Location:** `src/rag/gemini_client.py:28-60` (SYSTEM_INSTRUCTION)

**Problem:**
While the SYSTEM_INSTRUCTION says "Never guess at Mudrex-specific details. It's better to say 'I don't know' than give wrong info," the grounding prompt doesn't reinforce this strongly enough. When Google Search returns results, the model treats them as authoritative.

**Current Instruction:**
- Says "don't make stuff up"
- Says "if you don't have it, say so"
- BUT: When grounding provides web results, model assumes they're valid for Mudrex

**Missing:**
- Explicit instruction: "If Google Search doesn't return Mudrex-specific documentation, say 'I don't have that in my Mudrex docs'"
- Confidence threshold: "Only answer if you're 90%+ sure this applies to Mudrex"

### 3. **Similarity Threshold Too High**

**Location:** `src/config/settings.py:45` and `src/rag/vector_store.py:172`

**Problem:**
- Default threshold: `0.55` (class) vs `0.45` (env) - **inconsistency**
- Threshold of 0.55 may filter out relevant but not perfectly matching docs
- When docs are filtered out → falls back to Google Search → hallucinations

**Example:**
```
User: "What's the rate limit?"
→ Vector search finds doc with similarity 0.52 (below 0.55 threshold)
→ Filtered out → No docs → Google Search → Generic rate limit info → WRONG
```

**Current Code:**
```python
# config/settings.py
SIMILARITY_THRESHOLD: float = 0.55  # Class default

# But in from_env():
SIMILARITY_THRESHOLD=float(os.getenv("SIMILARITY_THRESHOLD", "0.45")),  # Env default
```

### 4. **No Confidence Scoring in Response**

**Location:** `src/rag/pipeline.py:114-135`

**Problem:**
Even when docs ARE retrieved, there's no confidence check. Low-similarity docs (0.55-0.60) might not be relevant, but the model still uses them confidently.

**Missing:**
- Confidence threshold check before generating response
- Warning when top similarity is low (< 0.65)
- Explicit "I'm not 100% sure" when similarity is borderline

### 5. **Grounding Prompt Doesn't Filter for Mudrex-Specific**

**Location:** `src/rag/gemini_client.py:237-271`

**Problem:**
The `generate_response_with_grounding()` method builds a prompt but doesn't explicitly instruct the model to:
- Only use results that mention "Mudrex" specifically
- Reject generic API documentation
- Say "I don't know" if no Mudrex-specific info found

**Current Prompt Structure:**
```python
prompt = self._build_prompt(query, context_documents, chat_history, mcp_context)
# No explicit "Mudrex-only" filter instruction
```

### 6. **No Validation of Retrieved Docs Relevance**

**Location:** `src/rag/pipeline.py:95-98`

**Problem:**
The pipeline logs similarity scores but doesn't validate if they're actually relevant. A doc with 0.55 similarity might be about a completely different topic.

**Missing:**
- Relevance check: Does the doc actually answer the question?
- Topic mismatch detection
- Quality filter before passing to model

---

## Impact Analysis

### High-Impact Scenarios

1. **Out-of-context questions** → Google Search → Generic answers → **WRONG**
2. **Low-similarity relevant docs filtered** → No docs → Google Search → **WRONG**
3. **Low-similarity irrelevant docs pass** → Model uses them → **CONFUSED/WRONG**

### User Trust Impact

- Users get confident-sounding but incorrect answers
- Bot appears knowledgeable but provides wrong information
- Damages credibility of the entire bot

---

## Recommended Fixes

### Fix 1: Remove or Restrict Google Search Grounding (CRITICAL)

**Option A: Remove Grounding Entirely**
- When no docs found, return: "I don't have that in my Mudrex docs. @DecentralizedJM might know."
- No fallback to web search

**Option B: Restrict Grounding with Explicit Filter**
- Only use grounding if Google Search results explicitly mention "Mudrex"
- Add instruction: "If search results don't mention Mudrex specifically, say 'I don't have Mudrex-specific info on this'"

**Recommended:** Option A (simpler, safer)

### Fix 2: Strengthen "I Don't Know" in SYSTEM_INSTRUCTION

**Add to SYSTEM_INSTRUCTION:**
```
## STRICT RULE: OUT-OF-CONTEXT QUESTIONS
- If the Relevant Documentation section is empty or says "No specific documentation found", 
  you MUST respond: "I don't have that in my Mudrex docs. Can you share more details, 
  or @DecentralizedJM might know?"
- DO NOT use general API knowledge or Google Search results to answer Mudrex questions.
- DO NOT assume generic API patterns apply to Mudrex.
```

### Fix 3: Fix Similarity Threshold Inconsistency

**Standardize threshold:**
- Use `0.45` as default (more permissive, catches more relevant docs)
- Or implement adaptive threshold based on query type
- Document the threshold clearly

### Fix 4: Add Confidence Checking

**Before generating response:**
```python
if retrieved_docs:
    top_similarity = retrieved_docs[0]['similarity']
    if top_similarity < 0.65:
        # Low confidence - warn in response
        # Or: return "I'm not 100% sure, but based on similar docs..."
```

### Fix 5: Improve Prompt When No Docs Found

**In `_build_prompt()`:**
```python
if not context_documents:
    parts.append("## WARNING: No Mudrex documentation found for this question.")
    parts.append("You MUST respond: 'I don't have that in my Mudrex docs. Can you share more details?'")
    parts.append("DO NOT use general API knowledge or guess.")
```

### Fix 6: Add Relevance Validation

**Before using retrieved docs:**
- Check if top doc actually mentions keywords from the query
- Filter out docs that are clearly off-topic despite similarity score
- Log when docs are filtered for low relevance

---

## Implementation Priority

### Phase 1: Critical (Immediate)
1. **Remove Google Search grounding** - Replace with "I don't know" response
2. **Fix similarity threshold inconsistency** - Standardize to 0.45
3. **Strengthen SYSTEM_INSTRUCTION** - Add explicit "no docs = say I don't know"

### Phase 2: High (Next)
4. **Add confidence checking** - Warn on low similarity
5. **Improve no-docs prompt** - Explicit instruction to not guess

### Phase 3: Medium (Future)
6. **Add relevance validation** - Filter off-topic docs
7. **Adaptive threshold** - Adjust based on query type

---

## Code Changes Required

### Files to Modify

1. **`src/rag/pipeline.py`**
   - Remove or restrict `generate_response_with_grounding()` call
   - Add confidence checking
   - Return "I don't know" when no docs

2. **`src/rag/gemini_client.py`**
   - Update SYSTEM_INSTRUCTION with strict "I don't know" rule
   - Improve `_build_prompt()` for no-docs case
   - Add confidence warnings

3. **`src/config/settings.py`**
   - Fix similarity threshold inconsistency
   - Add confidence threshold config

4. **`src/rag/vector_store.py`**
   - Consider lowering default threshold
   - Add relevance validation (optional)

---

## Testing Strategy

### Test Cases

1. **Out-of-context question:**
   - Query: "How do I set up webhooks?"
   - Expected: "I don't have that in my Mudrex docs..."
   - Current: Google Search → Generic webhook guide (WRONG)

2. **Low-similarity relevant doc:**
   - Query: "What's the rate limit?"
   - Doc exists with similarity 0.52
   - Expected: Use doc or say "I'm not 100% sure but..."
   - Current: Filtered out → Google Search (WRONG)

3. **No docs found:**
   - Query: "Does Mudrex support futures trading on weekends?"
   - Expected: "I don't have that in my Mudrex docs..."
   - Current: Google Search → Generic exchange info (WRONG)

---

## Success Criteria

- Bot never uses Google Search for Mudrex questions
- Bot always says "I don't know" when docs are missing
- Bot warns when confidence is low (< 0.65 similarity)
- No hallucinations on out-of-context questions
- Similarity threshold is consistent and documented

---

## Risk Assessment

**Low Risk:**
- Removing Google Search grounding (users get honest "I don't know")
- Fixing threshold inconsistency (just standardization)

**Medium Risk:**
- Changing SYSTEM_INSTRUCTION (needs testing to ensure it works)
- Adding confidence checking (might be too conservative)

**Mitigation:**
- Test all changes with real user queries
- Monitor logs for false negatives (legitimate questions getting "I don't know")
- Adjust thresholds based on real-world performance

---

## Conclusion

The primary cause of hallucinations is the **automatic fallback to Google Search grounding** when no documents are found. This should be **removed immediately** and replaced with an honest "I don't know" response. Additional improvements (confidence checking, threshold fixes, stronger instructions) will further reduce hallucinations.

**Recommended Action:** Implement Phase 1 fixes immediately to stop hallucinations.
