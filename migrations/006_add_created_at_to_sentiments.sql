BEGIN TRANSACTION;

-- 1) 加欄位（不用預設值，避免 SQLite 限制）
ALTER TABLE sentiments ADD COLUMN created_at TEXT;

-- 2) 回填：優先用 news.published_at，沒有就用當下時間
UPDATE sentiments
SET created_at = COALESCE(
  (SELECT published_at FROM news WHERE news.id = sentiments.news_id),
  datetime('now')
)
WHERE created_at IS NULL;

-- 3) 後續新插入資料：若未提供 created_at，自動填入當下時間
CREATE TRIGGER IF NOT EXISTS trg_sentiments_set_created_at
AFTER INSERT ON sentiments
FOR EACH ROW
WHEN NEW.created_at IS NULL
BEGIN
  UPDATE sentiments
  SET created_at = datetime('now')
  WHERE id = NEW.id;
END;

COMMIT;
