import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from classes import Bookie
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "arb",
    "user": "postgres",
    "password": "Wu1542558901"
}

def get_conn():
    return psycopg2.connect(**DB_CONFIG)

def save_bookie(bookie: Bookie):
    sql = """
    INSERT INTO bookies(name, balance, pnl, bonus, bonus_reset, loss_back, can_use_loss_back, loss_back_reset, traded, updated_at)
    VALUE(%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    ON CONFLICT(name) DO UPDATE
    name = EXCLUDED.name,
    balance = EXCLUDED.balance,
    pnl = EXCLUDED.pnl,
    bonus = EXCLUDED.bonus,
    bonus_rest = EXCLUDED.bonus,reset,
    loss_back = EXCLUDED.loss_back,
    can_use_loss_back = EXCLUDED.can_use_loss_back,
    loss_back_reset = EXCLUDED.loss_back_reset,
    traded = EXCLUDED.traded,
    updated_at = NOW();
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (bookie.name, bookie.balance, bookie.pnl, bookie.bonus, bookie.bonus_reset, bookie.loss_back, bookie.can_use_loss_back, bookie.loss_back_reset, bookie.traded))

def load_bookie(name: str) -> Bookie:
    sql = """
    SELECT * FROM bookies WHERE name = %s;
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (name,))
            row = cur.fetchone()
            return Bookie(
                name=row["name"],
                balance=row["balance"],
                pnl=row["pnl"],
                bonus=row["bonus"],
                bonus_reset=row["bonus_reset"],
                loss_back=row["loss_back"],
                can_use_loss_back=row["can_use_loss_back"],
                loss_back_reset=row["loss_back_reset"],
                traded=row["traded"],
            )

def load_all_bookie() -> list[Bookie]:
    sql = """
    SELECT * from bookies;
    """
    bookies = []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            for row in rows:
                bookies.append(
                    Bookie(
                    name=row["name"],
                    balance=row["balance"],
                    pnl=row["pnl"],
                    bonus=row["bonus"],
                    bonus_reset=row["bonus_reset"],
                    loss_back=row["loss_back"],
                    can_use_loss_back=row["can_use_loss_back"],
                    loss_back_reset=row["loss_back_reset"],
                    traded=row["traded"])
                )
            return bookies

def get_bookie_id(name: str) -> int:
    sql = """
    SELECT id FROM bookies WHERE name = %s;
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (name, ))
            row = cur.fetchone()
            return row["id"]

def save_odds_snapshot(bookie_id: int, game_name: str, market: str, outcomes: dict[str, float], game_date=None):
    sql = """
    INSERT INTO odds(bookie_id, game_name, market, outcome, price, snapshot_id, game_date)
    VALUES(%s, %s, %s, %s, %s, %s, %s);
    """

    uid = str(uuid.uuid4())
    with get_conn() as conn:
        with conn.cursor() as cur:
            for outcome, price in outcomes.items():
                cur.execute(sql, (bookie_id, game_name, market, outcome, price, uid, game_date))

def save_margin_snapshot(game_name: str, margin: float, selected_odds: list[tuple[str, float]]):
    date = datetime.now()
    selected_books_str = ""
    selected_odds_str = ""
    selected_odds.sort()
    for name, odd in selected_odds:
        selected_books_str += name + " "
        selected_odds_str += str(odd) + " "
    selected_books_str.rstrip(" ")
    selected_odds_str.rstrip(" ")
    sql = """
    INSERT INTO margin(game_name, margin, selected_odds, selected_bookies, date)
    VALUES(%s, %s, %s, %s, %s);
    """

    with get_conn() as conn:
        with conn.cursor as cur:
            cur.execute(sql, (game_name, margin, selected_odds_str, selected_books_str, date))

