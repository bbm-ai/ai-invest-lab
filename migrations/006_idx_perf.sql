-- Day19: performance indexes
CREATE INDEX IF NOT EXISTS idx_prices_symbol_date ON prices(symbol, date);
CREATE INDEX IF NOT EXISTS idx_news_date ON news(published_at);
CREATE INDEX IF NOT EXISTS idx_sentiments_news_id ON sentiments(news_id);
CREATE INDEX IF NOT EXISTS idx_strategies_date_symbol ON strategies(date, symbol);
CREATE INDEX IF NOT EXISTS idx_tech_signals_date_symbol ON tech_signals(date, symbol);
-- 小幫手：策略查最新一日（常用）
CREATE INDEX IF NOT EXISTS idx_strategies_created_at ON strategies(created_at);
