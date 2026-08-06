"""Check if sim algorithm has a bug."""
from difflib import SequenceMatcher


def normalize(s):
    return "".join(ch.lower() if ch.isalnum() or ch.isspace() else " " for ch in s)


def sim(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


# 第一个例子
en = '"Perfect" by Ed Sheeran remains the most popular wedding video song globally, but the best choice is always the song that\'s personally meaningful to you and your partner. Trends change — your connection to a song doesn\'t.'
back = "Ed Sheeran's \"Perfect\" remains the most popular wedding video song globally, but the best choice is always the song that's personally meaningful to you and your partner. Popular trends change, but your connection to the song doesn't."

print(f"EN:    {en}")
print(f"back:  {back}")
print()
print(f"  raw sim:        {sim(en, back):.3f}")
print(f"  char match %:   ", end="")
n1, n2 = normalize(en), normalize(back)
print(f"len(EN)={len(n1)} len(back)={len(n2)}")
print(f"  sim on normalized: {SequenceMatcher(None, n1, n2).ratio():.3f}")
print()
print("Normalized EN: ", n1[:120])
print("Normalized back:", n2[:120])
print()
# Token-based comparison
import re
tokens1 = re.findall(r"\w+", n1)
tokens2 = re.findall(r"\w+", n2)
print(f"  EN tokens: {len(tokens1)}, back tokens: {len(tokens2)}")
common = set(tokens1) & set(tokens2)
print(f"  common tokens: {len(common)}")
print(f"  token_jaccard: {len(common)/len(set(tokens1)|set(tokens2)):.3f}")

# Second example
print()
print("=== Example 2 ===")
en2 = "At WeddingAI.video, we specialize in the hybrid approach — AI efficiency combined with human editorial oversight. Our platform processes your footage with advanced AI, then our team of experienced editors ensures the final product tells your unique story. The result is professional-quality wedding films delivered faster and more affordably than traditional editing."
back2 = "At WeddingAI.video, we specialize in a hybrid approach—AI efficiency combined with human editorial oversight. Our platform uses advanced artificial intelligence to process your footage, then our experienced editorial team ensures the final product tells your unique story. The result is a professional-quality wedding video delivered faster and more cost-effectively than traditional editing."
print(f"  raw sim: {sim(en2, back2):.3f}")
n1, n2 = normalize(en2), normalize(back2)
print(f"  sim on normalized: {SequenceMatcher(None, n1, n2).ratio():.3f}")
