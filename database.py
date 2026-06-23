import sqlite3

def init_db():
    conn = sqlite3.connect('pln.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS pelanggan
                 (id INTEGER PRIMARY KEY,
                  nama TEXT,
                  tarif TEXT,
                  tagihan INTEGER)''')
    
    # Insert data dummy
    c.execute("DELETE FROM pelanggan")
    c.executemany('INSERT INTO pelanggan VALUES (?,?,?,?)', [
        (1, 'Budi Santoso', 'R1', 150000),
        (2, 'Siti Rahayu', 'R2', 320000),
        (3, 'Agus Wijaya', 'B1', 875000),
    ])
    
    conn.commit()
    conn.close()
    print("Database initialized!")