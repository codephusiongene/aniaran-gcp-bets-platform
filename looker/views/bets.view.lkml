view: bets {
  sql_table_name: `bets_dataset.live_bets` ;;

  dimension_group: event_ts {
    type: time
    timeframes: [raw, time, hour, date, week, month]
    sql: ${TABLE}.event_ts ;;
  }

  dimension: bet_id { primary_key: yes sql: ${TABLE}.bet_id ;; }
  dimension: user_id { sql: ${TABLE}.user_id ;; }
  dimension: game_id { sql: ${TABLE}.game_id ;; }
  dimension: sport { sql: ${TABLE}.sport ;; }
  dimension: country { sql: ${TABLE}.country ;; }
  dimension: channel { sql: ${TABLE}.channel ;; }
  dimension: status { sql: ${TABLE}.status ;; }

  measure: bets_count { type: count }
  measure: total_stake { type: sum sql: ${TABLE}.stake_amount ;; }
  measure: total_payout { type: sum sql: ${TABLE}.payout ;; }
  measure: avg_odds { type: average sql: ${TABLE}.odds ;; }
}
