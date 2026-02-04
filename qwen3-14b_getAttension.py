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
        dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
        attn_implementation="eager",
    )

    # ★ attention を有効化
    model.config.output_attentions = True
    model.eval()

    prompt = """
You are a white hat hacker tasked with discovering vulnerabilities in the provided source code.

Perform the following three actions on the source code below:
1. Identify the vulnerability
2. Present the risks of leaving it unaddressed
3. Provide a solution to eliminate the vulnerability

Additionally, for each identified vulnerability, assign a confidence score indicating 
the likelihood that the vulnerability actually exists in the source code.

- The score must be a real number between 0.0 and 1.0
- 0.0 means "the vulnerability definitely does not exist"
- 1.0 means "the vulnerability definitely exists"
- The score should reflect your confidence based solely on evidence in the code

When assigning the score:
- Use ≥ 0.8 if clear exploitable patterns are present
- Use 0.4–0.7 if the vulnerability is plausible but uncertain
- Use ≤ 0.3 if little to no evidence is found

Ensure your output adheres to the following three points:
1. Output in Japanese
2. Be clear and concise
3. Use Markdown format

---
<?php
// --- サーバーサイド (PHP) ---
// ユーザーからの入力を処理する部分です

$alarmTime = "";
$message = "アラーム時間をセットしてください。";

// フォームが送信されたか確認
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // 入力を取得
    if (isset($_POST['set_time']) && !empty($_POST['set_time'])) {
        // 入力された時間を変数に格納（サニタイズ処理）
        $alarmTime = htmlspecialchars($_POST['set_time'], ENT_QUOTES, 'UTF-8');
        $message = "アラームを **" . $alarmTime . "** に設定しました！";
    }
}
?>

<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PHP Alarm Clock</title>
    <style>
        body { font-family: sans-serif; text-align: center; margin-top: 50px; background-color: #f0f0f0; }
        .clock-container { background: white; padding: 30px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { font-size: 3em; margin: 10px 0; color: #333; }
        .status { margin-bottom: 20px; color: #007bff; font-weight: bold; }
        form { margin-top: 20px; }
        input[type="time"] { padding: 10px; font-size: 1.2em; border-radius: 5px; border: 1px solid #ccc; }
        button { padding: 10px 20px; font-size: 1.2em; background-color: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #218838; }
    </style>
</head>
<body>

<div class="clock-container">
    <h2>現在時刻</h2>
    <h1 id="clock">00:00:00</h1>
    
    <div class="status">
        <?php echo $message; ?>
    </div>

    <form method="POST" action="">
        <input type="time" name="set_time" required value="<?php echo $alarmTime; ?>">
        <button type="submit">設定する</button>
    </form>
</div>

<script>
    // --- クライアントサイド (JavaScript) ---
    // PHPから受け取った時間をJSの変数に渡す
    let alarmTarget = "<?php echo $alarmTime; ?>"; 
    let alarmTriggered = false; // 重複アラーム防止フラグ

    function updateClock() {
        const now = new Date();
        
        // 時・分・秒のフォーマット (2桁埋め)
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        
        // 時計表示の更新
        document.getElementById('clock').textContent = `${hours}:${minutes}:${seconds}`;

        // アラームチェック (秒まで待つと長いので、分単位で一致したら鳴らす)
        const currentTimeString = `${hours}:${minutes}`;

        // アラームが設定されていて、まだ鳴っていなくて、時間が一致した場合
        if (alarmTarget !== "" && currentTimeString === alarmTarget && !alarmTriggered) {
            playAlarm();
            alarmTriggered = true; // 1分間鳴り続けないようにフラグを立てる
        }
    }

    function playAlarm() {
        // シンプルにアラートを表示
        // 音声を鳴らしたい場合はここに audio.play() などを記述します
        alert("時間です！ (" + alarmTarget + ")");
        
        // 実際のアラーム音を鳴らしたい場合の例（コメントアウト）:
        // let audio = new Audio('alarm_sound.mp3');
        // audio.play();
    }

    // 1秒ごとに時計を更新
    setInterval(updateClock, 1000);
    
    // 初回実行
    updateClock();
</script>

</body>
</html>
"""

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

    # attentions:
    # tuple(num_layers)
    #   └─ tuple(num_steps)
    #        └─ Tensor(batch, heads, tgt_len, src_len)
    attentions = outputs.attentions

    # ===== 最終レイヤ =====
    last_layer = attentions[-1]

    # ===== 最終生成ステップ =====
    last_step_attn = last_layer[-1]  # Tensor(batch, heads, tgt_len, src_len)

    # ===== 最後に生成された1トークン =====
    last_token_attn = last_step_attn[:, :, -1, :]  # (batch, heads, src_len)

    # ===== ヘッド平均 =====
    attn_scores = last_token_attn.mean(dim=1).squeeze(0)  # (src_len,)

    # ===== 入力トークン =====
    input_ids = inputs["input_ids"][0]
    tokens = tokenizer.convert_ids_to_tokens(input_ids)

    # 長さ調整（安全）
    seq_len = min(len(attn_scores), len(tokens))
    attn_scores = attn_scores[:seq_len]
    tokens = tokens[:seq_len]
    input_ids = input_ids[:seq_len]

    # ===== 上位トークン =====
    k = min(15, seq_len)
    topk = torch.topk(attn_scores, k=k)

    print("\n=== 出力決定時に強く参照された入力トークン（特殊トークン含む）===")
    for score, idx in zip(topk.values, topk.indices):
        idx = idx.item()
        token = tokens[idx]
        text_piece = tokenizer.decode([input_ids[idx]])
        print(f"{score.item():.4f} | idx={idx:4d} | token='{token}' | text='{text_piece}'")


if "__main__" in __name__:
    run_qwen()
