connection: bigquery_connection

include: "/views/*.view.lkml"

explore: bets {
  from: bets
  label: "Bets"
  description: "Live bets landing table"
}
