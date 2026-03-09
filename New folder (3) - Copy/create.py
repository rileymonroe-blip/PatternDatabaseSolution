import sqlite3
conn = sqlite3.connect('patternsdatabase.db')
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS patternsdb (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        design TEXT,
        location TEXT,
        difficulty INTEGER, 
        time INTEGER,
        materials TEXT,
        pdf_path TEXT,
        image_url TEXT
        
    );
    
""")

conn.commit()
conn.close()
print("Database created successfully!")

