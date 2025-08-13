-- Hot window
SELECT
  TIMESTAMP_TRUNC(event_ts, MINUTE) AS minute,
  game_id,
  COUNT(*) AS bets,
  SUM(stake_amount) AS stake,
  SUM(payout) AS payout,
  AVG(odds) AS avg_odds
FROM `YOUR_PROJECT_ID.bets_dataset.live_bets`
WHERE event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 10 MINUTE)
GROUP BY minute, game_id
ORDER BY minute DESC, bets DESC;

-- Country breakdown
SELECT country, COUNT(*) AS bets, SUM(stake_amount) AS stake
FROM `YOUR_PROJECT_ID.bets_dataset.live_bets`
WHERE event_ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
GROUP BY country
ORDER BY stake DESC;
