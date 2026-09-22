import sqlite3
def list_all(conn): return [dict(r) for r in conn.execute("SELECT * FROM loans ORDER BY id").fetchall()]
def get(conn, lid):
    row = conn.execute("SELECT * FROM loans WHERE id=?", (lid,)).fetchone()
    return dict(row) if row else None
def insert(conn, name, principal, annual_rate, months):
    cur = conn.execute("INSERT INTO loans(name,principal,annual_rate,months) VALUES (?,?,?,?)",
        (name, principal, annual_rate, months))
    return int(cur.lastrowid)
def delete(conn, lid): conn.execute("DELETE FROM loans WHERE id=?", (lid,))
def update_annual_rate(conn, lid, annual_rate):
    conn.execute("UPDATE loans SET annual_rate=? WHERE id=?", (annual_rate, lid))
