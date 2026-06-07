import json
import os
from typing import List, Dict

def generate_typo_grammar_dataset(output_path: str, samples: List[Dict]):
    """
    Generate dataset for FT-1/FT-2: Typo and Grammar correction.
    Format: JSONL with system, user, and assistant fields for SFT.
    """
    system_prompt = "你是学术论文纠错助手，只输出 JSON 数组，每项含 span_id, original_text, suggested_text, issue_type, reason"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in samples:
            record = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": sample["input"]},
                    {"role": "assistant", "content": json.dumps(sample["output"], ensure_ascii=False)}
                ]
            }
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    # Dummy data for demonstration
    dummy_samples = [
        {
            "input": "【上下文】这篇论文提出了一种新的算发。\n【待检 spans】[{\"span_id\": \"s1\", \"text\": \"这篇论文提出了一种新的算发。\"}]",
            "output": [
                {
                    "span_id": "s1",
                    "original_text": "算发",
                    "suggested_text": "算法",
                    "issue_type": "typo",
                    "reason": "同音词误用"
                }
            ]
        }
    ]
    
    os.makedirs(os.path.dirname(__file__) + "/../data", exist_ok=True)
    generate_typo_grammar_dataset(os.path.dirname(__file__) + "/../data/typo_grammar.jsonl", dummy_samples)
    print("Dataset generated successfully.")
