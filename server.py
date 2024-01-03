from flask import Flask, render_template, request
import requests
import sqlite3
import os
import sys


# SQLITE DB
con = sqlite3.connect("recipes.db", check_same_thread=False)
app = Flask(__name__)

@app.route("/")
def index():
	return render_template("index.html")
    
@app.route("/recipes")
def all_recipes():
    cur = con.cursor()
    cur.execute(f"""
    SELECT 
      * 
    FROM 
      recipes
    ORDER BY name
    """)
    recipes = cur.fetchall()
    return render_template("recipes.html", recipes=recipes)
    
@app.route("/recipes/<int:id>")
def recipe(id):
    cur = con.cursor()
    cur.execute(f"""
    SELECT 
      * 
    FROM 
      recipes 
    WHERE
      id = {id}
    """)
    recipe = cur.fetchone()
    
    cur.execute(f"""
    SELECT 
      ingredients.*,
      recipe_ingredient.quantity,
      recipe_ingredient.unit,
      recipe_ingredient.comment      
    FROM 
      recipe_ingredient 
    INNER JOIN
      ingredients on recipe_ingredient.ingredient_id = ingredients.id
    WHERE
      recipe_ingredient.recipe_id = {id}
    """)
    ingredients = cur.fetchall()
    return render_template("recipe.html", recipe=recipe, ingredients=ingredients)
    
@app.route("/search")
def search():
    query = request.args.get("q")
    cur = con.cursor()
    cur.execute(f"""
    SELECT 
      * 
    FROM 
      recipes 
    WHERE 
      lower(name) like '%{query.lower()}%'
    
    UNION
    
    SELECT DISTINCT 
      recipes.* 
    FROM
      recipes
    INNER JOIN
      recipe_ingredient ON recipes.id = recipe_ingredient.recipe_id
    INNER JOIN
      ingredients ON recipe_ingredient.ingredient_id = ingredients.id
    WHERE
      lower(ingredients.name) like '%{query.lower()}%' 
    ;
    """)
    res = cur.fetchall()
    return res

@app.route("/get_token")
def callback():
    code = request.args.get("code")
    res = requests.post("https://todoist.com/oauth/access_token",
                        data={
                            "client_id": os.getenv("todoist_client_id"),
                            "client_secret": os.getenv("todoist_client_secret"),
                            "code": code,
                            "redirect_uri":"recipedb.ngrok.app/token"
                        })

    return res.json()["access_token"]

@app.route("/add_item")
def add_item():
    pass
 
if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5001, debug=True)
