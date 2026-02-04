import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def run_qwen():
    model_name = "unsloth/Qwen3-14B-unsloth-bnb-4bit"
    max_seq_length = 40960

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        max_seq_length = max_seq_length,
        load_in_4bit = True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    # ★ attention を有効化
    model.config.output_attentions = True
    model.eval()

    prompt = "SQLインジェクションの対策を簡潔に説明してください。"

    messages = [{"role": "user", "content": prompt}]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking = False,
    )

    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=4096,
            temperature=0.6,
            top_p=0.95,
            top_k=20,
            return_dict_in_generate=True,
            output_attentions=True,
        )

    print(tokenizer.decode(outputs.sequences[0], skip_special_tokens=True))

if "__main__" in __name__:
    run_qwen()
