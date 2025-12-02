<?php
// A single-file PHP memo app using session for storage
session_start();
if (!isset($_SESSION['memos'])) {
    $_SESSION['memos'] = [];
}

// Save new or updated memo
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {
    if ($_POST['action'] === 'save') {
        $id = $_POST['id'] !== '' ? intval($_POST['id']) : time();
        $_SESSION['memos'][$id] = [
            'title' => $_POST['title'],
            'body'  => $_POST['body']
        ];
        exit(json_encode(['status' => 'ok']));
    }
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>PHP Memo App</title>
<style>
body { font-family: sans-serif; margin:0; padding:0; }
#header { padding: 10px; background:#f5f5f5; display:flex; justify-content:flex-end; }
#memoList { padding: 20px; }
.memo { border:1px solid #ccc; padding:10px; margin-bottom:10px; cursor:pointer; }
.memo-title { font-weight: bold; display:flex; justify-content:space-between; align-items:center; }
.memo-body { display:none; margin-top:10px; white-space:pre-wrap; }
#overlay {
    position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.4);
    display:none; justify-content:center; align-items:center;
}
#editor {
    background:white; width:400px; padding:20px; border-radius:8px; position:relative;
}
#editor textarea { width:100%; height:200px; }
#editor button { padding:8px 12px; margin:5px; }
#cancelBtn { position:absolute; left:10px; bottom:10px; }
#saveBtn { position:absolute; right:10px; bottom:10px; }
</style>
</head>
<body>
<div id="header">
    <button onclick="openEditor()">メモ作成</button>
</div>
<div id="memoList">
<?php foreach ($_SESSION['memos'] as $id => $m): ?>
    <div class="memo" onclick="toggleMemo(<?= $id ?>)">
        <div class="memo-title">
            <span><?= htmlspecialchars($m['title']) ?></span>
            <button onclick="event.stopPropagation(); editMemo(<?= $id ?>)">✏️</button>
        </div>
        <div class="memo-body" id="body-<?= $id ?>"><?= nl2br(htmlspecialchars($m['body'])) ?></div>
    </div>
<?php endforeach; ?>
</div>

<div id="overlay">
  <div id="editor">
    <input type="hidden" id="memoId">
    <label>タイトル(必須):</label><br>
    <input id="titleInput" type="text" maxlength="100" style="width:100%"><br><br>
    <label>内容(最大1000文字):</label><br>
    <textarea id="bodyInput" maxlength="1000"></textarea>
    <button id="cancelBtn" onclick="closeEditor()">キャンセル</button>
    <button id="saveBtn" disabled onclick="saveMemo()">完了</button>
  </div>
</div>

<script>
function toggleMemo(id){
    const b = document.getElementById('body-' + id);
    b.style.display = (b.style.display === 'block') ? 'none' : 'block';
}
function openEditor(){
    document.getElementById('memoId').value = '';
    document.getElementById('titleInput').value='';
    document.getElementById('bodyInput').value='';
    checkValid();
    document.getElementById('overlay').style.display='flex';
}
function editMemo(id){
    const title = document.querySelector(`[onclick="toggleMemo(${id})"] .memo-title span`).textContent;
    const body = document.querySelector(`#body-${id}`).textContent;
    document.getElementById('memoId').value = id;
    document.getElementById('titleInput').value = title;
    document.getElementById('bodyInput').value = body;
    checkValid();
    document.getElementById('overlay').style.display='flex';
}
function closeEditor(){
    document.getElementById('overlay').style.display='none';
}
function checkValid(){
    const t = document.getElementById('titleInput').value.trim();
    const s = document.getElementById('saveBtn');
    s.disabled = (t.length === 0);
}
document.getElementById('titleInput').addEventListener('input', checkValid);
function saveMemo(){
    const id = document.getElementById('memoId').value;
    const title = document.getElementById('titleInput').value;
    const body = document.getElementById('bodyInput').value;
    const formData = new FormData();
    formData.append('action','save');
    formData.append('id',id);
    formData.append('title',title);
    formData.append('body',body);
    fetch('',{method:'POST',body:formData})
        .then(r=>r.json())
        .then(()=>location.reload());
}
</script>
</body>
</html>
