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
        attn_implementation="eager",
    )

    # ★ attention を有効化
    model.config.output_attentions = True
    model.eval()

    prompt = """
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

if "__main__" in __name__:
    run_qwen()
