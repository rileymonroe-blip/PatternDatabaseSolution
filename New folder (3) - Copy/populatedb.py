import sqlite3
def add_pattern(design, location, difficulty, time, materials,pdf_path, image_url):
    # Connect to the database
    conn = sqlite3.connect('patternsdatabase.db')
    c = conn.cursor()
    
    # SQL query to insert data
    c.execute('''
        INSERT INTO patternsdb (design, location, difficulty, time, materials,pdf_path, image_url)
        VALUES (?, ?, ?, ?, ?,?,?)
    ''', (design, location, difficulty, time, materials,pdf_path, image_url))
    
    # Commit and close connection
    conn.commit()
    conn.close()
    print(f'pattern "{design}" added successfully!')

# Example usage
if __name__ == "__main__":
    
    add_pattern(
        design="Babydoll dress",
        location="PDF",
        difficulty=4,
        time=120,
        materials="zipper, 3 meters fabric, thread,",
        pdf_path="static/pdfs/mint_babydoll.pdf",
        image_url="/static/img/mint.jpg"
    )
    
    
   
   
    
    
    
    
    
   
    
    
   
    import sqlite3

def delete_pattern_by_name(design):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Check first if it exists (optional but helpful)
    c.execute("SELECT * FROM patterns WHERE design = ?", (design,))
    record = c.fetchone()
    if not record:
        print(f'No pattern found with the name "{design,}"')
    else:
        c.execute("DELETE FROM patterns WHERE name = ?", (design,))
        conn.commit()
        print(f'pattern "{design}" deleted successfully!')

    conn.close()





    


    


    