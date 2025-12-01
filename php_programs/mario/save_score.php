<?php
// ファイルパス
$file_path = 'highscores.txt';
// ランキングに表示する最大件数
$max_scores = 10;

// POSTデータを受け取る
$new_score = filter_input(INPUT_POST, 'score', FILTER_VALIDATE_INT);
$new_name = filter_input(INPUT_POST, 'name', FILTER_SANITIZE_STRING);

// データの検証
if (!$new_score || $new_score < 0 || !$new_name) {
    // スコアがない場合は、単にランキングを返して終了（念のため）
    echo json_encode(['ranking' => get_ranking($file_path, $max_scores)]);
    exit;
}

// スコアと名前を結合した新しいエントリー
$new_entry = ['score' => $new_score, 'name' => $new_name, 'new' => true];
$ranking = get_ranking($file_path, $max_scores);

// 新しいスコアをランキングに追加
$ranking[] = $new_entry;

// スコアの高い順にソート
usort($ranking, function($a, $b) {
    return $b['score'] <=> $a['score'];
});

// 最大件数にカット
$ranking = array_slice($ranking, 0, $max_scores);

// テキストファイルに書き込み
save_ranking($file_path, $ranking);

// PHPのレスポンスとしてJSONでランキングを返す
header('Content-Type: application/json');
echo json_encode(['ranking' => $ranking]);


/**
 * ランキングデータをファイルから読み込む関数
 * @param string $file_path
 * @param int $max_scores
 * @return array
 */
function get_ranking($file_path, $max_scores) {
    $ranking = [];
    if (file_exists($file_path)) {
        // ファイルから全行を読み込み
        $lines = file($file_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($lines as $line) {
            // "スコア|名前" の形式でパース
            $parts = explode('|', $line);
            if (count($parts) === 2) {
                $ranking[] = [
                    'score' => (int)$parts[0],
                    'name' => $parts[1],
                    'new' => false // ファイルから読み込んだものは新規ではない
                ];
            }
        }
        // スコアの高い順にソートし、最大件数にカット
        usort($ranking, function($a, $b) {
            return $b['score'] <=> $a['score'];
        });
        return array_slice($ranking, 0, $max_scores);
    }
    return $ranking;
}

/**
 * ランキングデータをファイルに書き込む関数
 * @param string $file_path
 * @param array $ranking
 * @return void
 */
function save_ranking($file_path, $ranking) {
    $data_to_write = [];
    foreach ($ranking as $item) {
        // "スコア|名前" の形式で保存
        $data_to_write[] = "{$item['score']}|{$item['name']}";
    }
    // ファイルに書き込み (上書き)
    file_put_contents($file_path, implode("\n", $data_to_write), LOCK_EX);
}
?>