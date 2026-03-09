from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash#importing liabaries from Flask to use later
import sqlite3#allows for pattern database to read and written to 
import os
from functools import wraps
app = Flask(__name__) #flask notation
ADMINPW = os.environ.get("ADMINPW", "1234")#where teacher password is defined 

app.secret_key = "fcghjgfdgh67448"# Nessiary for session object, makes sure users can not modify unless they know this key: https://flask.palletsprojects.com/en/stable/quickstart/

def fetchpatterns():#function to connect to pattern database
    conn = sqlite3.connect("patternsdatabase.db")
    return conn

#below is a function to make sure user intputs for numbers are integers
def numcheck(value: str, field_name: str, *, minval=None, maxval=None, required=False):#chatGPT gnenerated
    value = (value or "").strip()
    if not value:
        if required:
            return None, f"{field_name} is empty please enter a whole number"
        return None, None  
    try:
        n = int(value)
    except ValueError:
        return None, f"{field_name} please enter a whole number"
    if minval is not None and n < minval:
        return None, f"{field_name} must be ≥ {minval}."
    if maxval is not None and n > maxval:
        return None, f"{field_name} must be ≤ {maxval}."
    return n, None

def getpatterns(design="",location="",difficulty="",time="", materials="", pdf_path="",image_url="",kw=""):#this function is modified from a previouse project of mine which was modified from chatGPT generated code 
    conn=fetchpatterns()
    c=conn.cursor()
    #Querying the pattern database based on the what filters the user entered, general query statment for everything but gets narrowed down by the appends
    query = """
        SELECT id, design, location, difficulty, time, materials, pdf_path, image_url
        FROM patternsdb
        WHERE 1=1
    """# Where 1=1 is always true so the whole database is queried 
    params = []
    if design:#if user entered something in design the query bellow is added 
        query += " AND design LIKE ?"#like means that it just has to similar not exact
        params.append(f"%{design}%")#question mark is equal to this 
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if difficulty:
        query += " AND difficulty = ?"#must be exactly equal
        params.append(int(difficulty))
    if time:
        query += " AND time <= ?"#must eqaul to or less than time entered by the user
        params.append(int(time))
    if materials:
        query += " AND materials LIKE ?"
        params.append(f"%{materials}%")
    if pdf_path:
        query += " AND pdf_path LIKE ?"
        params.append(f"%{pdf_path}%")
    if image_url:
        query += " AND image_url LIKE ?"
        params.append(f"%{image_url}%")
    if kw:
        #keyword search across a few fields using LIKE so it does not have to be exact
        like = f"%{kw.lower()}%"
        query += " AND (LOWER(design) LIKE ? OR LOWER(materials) LIKE ? OR LOWER(location) LIKE ?)"
        params.extend([like, like, like])
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

import re

def normalize(s: str) -> str: #GPT generated 
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9\s\-]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s

def sepmaterials(text: str) -> set[str]:
    if not text:
        return set()
    parts = re.split(r"[,\n;]+", text)
    return {normalize(p) for p in parts if normalize(p)}
def meters(materials):
    total=0
    for i in materials:
        if "fabric" in i:
            nummeters=re.search(r"\d+(\.\d+)?",i)
            if nummeters:
                total=total+float(nummeters.group())
    return total

def rank_patterns(rows, have_text: str):
    have_set = sepmaterials(have_text)
    ranked = []

    for row in rows:
        need_set = sepmaterials(row[5])  
        matches = have_set & need_set
        missing = need_set - have_set
        posfabric=meters(have_set)
        needfabric=meters(need_set)
        score = (len(matches) / len(need_set)) if need_set else 0.0
        if needfabric >0 and needfabric!=posfabric:
           additional=min(posfabric/needfabric,1)  
           score = ((len(matches)+additional) / len(need_set)) if need_set else 0.0

        ranked.append({
            "row": row,
            "score": score,
            "match_count": len(matches),
            "need_count": len(need_set),
            "missing": sorted(missing),
        })

    ranked.sort(key=lambda x: (x["score"], x["match_count"]), reverse=True)#rank materials based on their score
    return ranked


def isteacher(f):#ChatGPT generated
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("teacher"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/admin", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == ADMINPW:
            session["teacher"] = True
            return redirect(url_for("collection"))  # go to database page 
        else:
            flash("Wrong password please try again or login as a student")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))   

@app.route("/", methods=["GET"])
def landing():
    return render_template("landing.html")

@app.route("/student")
def student():
    session.pop("teacher", None)   
    return redirect(url_for("collection"))

@app.route('/collection' ,methods=['GET'])
def collection():
    have = request.args.get("have", "").strip()  
    filters = dict(
        design=request.args.get("design", "").strip(),
        location=request.args.get("location", "").strip(),
        difficulty=request.args.get("difficulty", "").strip(),
        time=request.args.get("time", "").strip(),
        materials=request.args.get("materials", "").strip(),
        pdf_path=request.args.get("pdf_path", "").strip(),
        image_url=request.args.get("image_url", "").strip(),
        kw=request.args.get("q", "").strip(),
    )   
    rows = getpatterns(**filters)    
    if have != False:
        ranked = rank_patterns(rows, have)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":#chatGPT generated
            return render_template("partials/patternsranked.html", ranked=ranked, have=have)

        return render_template("collection.html", ranked=ranked, have=have)

    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("partials/patterns.html", patterns=rows)

    return render_template("collection.html", patterns=rows)

@app.route("/new", methods=["GET", "POST"])
@isteacher
def new():
    
    if request.method == "POST":
        
        design = request.form.get("design", "").strip()#get design that user just entered and clear it 
        location = request.form.get("location", "").strip()
        difficulty = request.form.get("difficulty", "").strip()
        time = request.form.get("time", "").strip()
        materials = request.form.get("materials", "").strip()
        pdf_path = request.form.get("pdf_path", "").strip()
        image_url = request.form.get("image_url", "").strip()
    
        differror = numcheck(
            request.form.get("difficulty", ""), "Difficulty",minval=1,maxval=5, required=False)
        if differror==True:
            flash(differror)
            return render_template("new.html")
        
        timeerror = numcheck(request.form.get("time", ""),"Time (minutes)",minval=0,required=False)
        if timeerror==True:
            flash(timeerror)
            return render_template("new.html")

        # validate required design
        if not design:
            flash("Design is required.")
            return render_template("new.html")    
        conn = fetchpatterns()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO patternsdb (design, location, difficulty, time, materials, pdf_path, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (design, location, difficulty, time, materials, pdf_path, image_url))
        conn.commit()
        conn.close()
        return render_template("new.html") 
    return render_template("new.html")    

@app.route("/deleat", methods=["GET", "POST"])
@isteacher
def deleat():
    if request.method == "POST":
        #get values to delete
        design = request.form.get("design", "").strip()
        conn = fetchpatterns()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM patternsdb WHERE design = ?""", (design,))
        deleted=cur.rowcount #counts the rows deleated sucessfuly would be 1
        conn.commit()
        conn.close()
        if deleted==0:#if no pattern was deleted the folowing message gets flashed
            flash(f'Pattern"{design}" does not exist try again and check the spelling')
        return render_template("deleat.html")
    return render_template("deleat.html")    

if __name__ == '__main__':
    app.run(debug=True)
    
    

