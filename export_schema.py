import sqlite3

def dump_sqlite_schema():
    # Point this to your actual database file path
    db_path = "museums.db" 
    
    conn = sqlite3.connect(db_path)
    with open("schema.sql", "w", encoding="utf-8") as f:
        for line in conn.iterdump():
            # iterdump includes inserts; filter for table/index creation schemas if preferred, 
            # or keep it as-is for the full dump.
            f.write(f"{line}\n")
    conn.close()
    print("Successfully dumped schema via Python sqlite3!")

if __name__ == "__main__":
    dump_sqlite_schema()