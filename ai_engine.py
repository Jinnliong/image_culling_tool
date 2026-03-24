import ollama
import re

def analyze_image(base64_img, op_mode):
    # --- UPDATED PROMPT: Now asks for Emotional Impact ---
    prompt = f"""Evaluate this {op_mode} photo quantitatively. 
CRITICAL RULE: You MUST use the exact line-by-line format below. DO NOT output a markdown table. DO NOT write conversational filler.

COMPETITION_STATUS: [PASS or DQ]
SHARPNESS: [0-100]
EXPOSURE: [0-100]
COMPOSITION: [0-100]
NARRATIVE: [0-100]
EMOTIONAL_IMPACT: [0-100]
CHINNY_ROAST: [0-100]
PRIVACY_FLAG: [YES or NO]
CRITIQUE: [1 sentence]"""

    response = ollama.chat(model='llava-phi3', messages=[{'role': 'user', 'content': prompt, 'images': [base64_img]}], options={'temperature': 0})
    reply = response['message']['content']
    
    def get_val(keyword, text, is_text=False):
        if is_text:
            m = re.search(rf'{keyword}.*?(YES|NO|PASS|DQ)', text, re.IGNORECASE | re.DOTALL)
            return m.group(1).upper() if m else "PASS"
        v = re.search(rf'{keyword}.*?(\d+)', text, re.IGNORECASE | re.DOTALL)
        return int(v.group(1)) if v else 0

    s, e, c = get_val('SHARPNESS', reply), get_val('EXPOSURE', reply), get_val('COMPOSITION', reply)
    
    # --- UPDATED RETURN: Now extracts Emotional Impact ---
    return {
        "Competition Status": get_val('COMPETITION_STATUS', reply, True),
        "Sharpness": s,
        "Exposure": e,
        "Composition": c,
        "Narrative Score": get_val('NARRATIVE', reply),
        "Emotional Impact": get_val('EMOTIONAL_IMPACT', reply),
        "Chinny Roast": get_val('CHINNY_ROAST', reply),
        "Privacy Alert": get_val('PRIVACY_FLAG', reply, True),
        "Tech Score": int((s * 0.4) + (e * 0.3) + (c * 0.3)),
        "Raw Reply": reply
    }

def categorize_photo(metrics, min_sharp, min_exp, min_comp, keeper_threshold, min_narrative, min_emotional):
    
    # LAYER 0: Objective Technical Failures
    if metrics['Sharpness'] < min_sharp or metrics['Exposure'] < min_exp or metrics['Composition'] < min_comp: 
        return "Discard"
    
    # Evaluate the Thresholds
    tech_pass = metrics['Tech Score'] >= keeper_threshold
    narr_pass = metrics['Narrative Score'] >= min_narrative
    emo_pass = metrics['Emotional Impact'] >= min_emotional
    comp_pass = metrics['Competition Status'] == 'PASS'
    
    # TIER 1: Technical + Narrative + Emotional
    if tech_pass and narr_pass and emo_pass and comp_pass:
        return "Keeper_Masterpiece"
        
    # TIER 2: Technical + Narrative
    elif tech_pass and narr_pass and comp_pass:
        return "Keeper_Storyteller"
        
    # TIER 3: Technical + Emotional
    elif tech_pass and emo_pass and comp_pass:
        return "Keeper_Mood"
        
    # TIER 4: Technical Only
    elif tech_pass and comp_pass:
        return "Keeper_Technical"
        
    # TIER 5: The Safety Net
    else:
        return "Review"