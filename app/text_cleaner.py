import re

def clean_wikipedia_text(text: str) -> str:
    """
    Removes common Wikipedia-specific artifacts from text.
    """
    # Remove [edit], [citation needed], etc.
    text = re.sub(r'\[\d*\]|\[edit\]|\[citation needed\]', '', text)
    
    # Remove lines that are just headers (like 'History\n[edit]') or metadata
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove lines that are just section titles or dividers
        if line.strip().startswith('==') and line.strip().endswith('=='):
            continue
        # Remove template text like "| Whatever"
        if line.strip().startswith('|'):
            continue
        cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines)

def clean_generic_text(text: str) -> str:
    """
    Performs general cleaning on scraped text from various web sources.
    """
    # List of common boilerplate/junk phrases to remove entirely
    junk_phrases = [
        "Verifying you are human",
        "needs to review the security of your connection",
        "Enable JavaScript and cookies to continue",
        "This article needs additional citations for verification",
        "Was this article helpful?",
        "Subscribe to our newsletter"
    ]
    
    for phrase in junk_phrases:
        if phrase in text:
            # If we find junk, it's often a sign the whole page is bad
            # (e.g., a CAPTCHA page). We discard the whole thing.
            print(f"Junk phrase '{phrase}' found. Discarding content.")
            return ""

    # Split into lines to process individually
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Remove lines that are very short, as they are often navigation links or noise
        if len(line.strip()) < 50 and '{' not in line and '}' not in line:
            continue
            
        cleaned_lines.append(line.strip())
        
    # Rejoin the text, but use a single newline to normalize spacing
    full_text = "\n".join(cleaned_lines)
    
    # Collapse multiple newlines into a maximum of two (to preserve paragraphs)
    return re.sub(r'\n{3,}', '\n\n', full_text).strip()