import os.path
import sqlite3
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def init_db():
    # SQLITE DB
    con = sqlite3.connect("recipes.db")

    cur = con.cursor()

    cur.execute("""
        DROP TABLE IF EXISTS recipes;
    """)
    cur.execute("""
        DROP TABLE IF EXISTS ingredients;
    """)
    cur.execute("""
        DROP TABLE IF EXISTS recipe_ingredient;
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            name char(50),
            description char(50),
            book char(50),
            page_number char(50),
            link char(50)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY,
            name char(50),
            category char(50)
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipe_ingredient (
            recipe_id INTEGER,
            ingredient_id INTEGER,
            quantity char(50),
            unit char(50),
            comment char(256)
        );
    """)
    
    return con

def parse_sheet(values):
    # Parse Recipe details
    recipe = values[2:7]
    recipe_metadata = {x[1]: (x[2] if len(x) > 2 else "") for x in recipe}

    # Parse Ingredients
    ingredients = values[9:]
    headers = ingredients[0][1:]
    ingredients_metadata = [dict(zip(headers,x[1:])) for x in ingredients[1:]]

    return recipe_metadata, ingredients_metadata


def read_sheets():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  # If modifying these scopes, delete the file token.json.
  SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

  # The ID and range of a sample spreadsheet.
  SPREADSHEET_ID = "1LFY_aU3TxbCH_pXZeHcaRKFopdZhGXSk5Sm89xUXk4U"

  con = init_db()
  cur = con.cursor()
  creds = None
  ingredient_dict = {}
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheets = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    ranges = [f"{tab['properties']['title']}!A1:F" for tab in sheets["sheets"]]
    sheet_values = service.spreadsheets().values().batchGet(spreadsheetId=SPREADSHEET_ID, ranges=ranges).execute()
    for sheet in sheet_values["valueRanges"]:
        if sheet["range"].split("!")[0] not in ("Instructions","TEMPLATE", "LOOKUPS"):
            recipe, ingredients = parse_sheet(sheet["values"])
            cur.execute("""
                INSERT INTO recipes (name, description, book, page_number, link) VALUES (?, ?, ?, ?, ?)
            """, [x.lower() for x in recipe.values()])
            recipe_id = cur.lastrowid
            
            # Insert unique ingredients
            for ingredient in ingredients:
                if ingredient["Name"].strip() != "":
                    ingredient_id = ingredient_dict.get(ingredient["Name"].strip().lower(),-1)
                    if ingredient_id == -1:
                        cur.execute("""
                            INSERT INTO ingredients (name, category) VALUES (?, ?) 
                        """, [ingredient["Name"].strip().lower(), ingredient.get("Category","").strip().lower()])
                        ingredient_dict[ingredient["Name"].strip().lower()] = cur.lastrowid
                        
                    cur.execute("""
                        INSERT INTO recipe_ingredient VALUES (?, ?, ?, ?, ?)
                    """,[recipe_id, ingredient_dict[ingredient["Name"].strip().lower()], ingredient.get("Quantity",""), ingredient.get("Unit",""), ingredient.get("Comment","")])
                    
    con.commit()

  except HttpError as err:
    print(err)


if __name__ == "__main__":
  read_sheets()
