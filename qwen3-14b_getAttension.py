from unsloth import FastLanguageModel
import torch

def run_qwen():
    model_name = "unsloth/Qwen3-14B-unsloth-bnb-4bit"
    max_seq_length = 40960

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = model_name,
        max_seq_length = max_seq_length,
        load_in_4bit = True,
        load_in_8bit = False,
    )

    prompt = """
    """

    messages = [{"role": "user", "content": prompt}]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )

    inputs = tokenizer(text, return_tensors="pt").to("cuda")

    # ★ ここが変更点
    outputs = model.generate(
        **inputs,
        max_new_tokens=4096,
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        output_attentions=True,
        return_dict_in_generate=True,
    )

    # ========== Attention解析 ==========
    # outputs.attentions:
    # tuple(num_generated_tokens)
    #   -> tuple(num_layers)
    #       -> (batch, num_heads, tgt_len, src_len)

    attentions = outputs.attentions

    # 最後に生成されたトークン
    last_token_attn = attentions[-1]        # tuple(num_layers)
    last_layer_attn = last_token_attn[-1]   # (1, heads, 1, seq_len)

    # ヘッド平均
    attn_scores = last_layer_attn.mean(dim=1).squeeze()  # (seq_len,)

    # 入力トークン列
    input_ids = inputs["input_ids"][0]
    tokens = tokenizer.convert_ids_to_tokens(input_ids)

    # 上位トークン表示
    topk = torch.topk(attn_scores, k=10)

    print("\n=== Attentionが強かった入力トークン ===")
    for score, idx in zip(topk.values, topk.indices):
        token = tokens[idx]
        text_piece = tokenizer.decode([input_ids[idx]])
        print(f"{score.item():.4f} | token='{token}' | text='{text_piece}'")

if "__main__" in __name__:
    run_qwen()
