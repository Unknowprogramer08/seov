print(" [+] Loading basics...")
import os
import json
import re
from pymongo import MongoClient
import bcrypt
import requests
from pathlib import Path
p = Path(__file__).parents[0]
if os.name == 'nt':
  os.system("color")

os.system("title Social Empires Server")

print(" [+] Loading game config...")
from get_game_config import get_game_config, patch_game_config

from dotenv import load_dotenv
load_dotenv()

print(" [+] Loading players...")
from get_player_info import get_player_info, get_neighbor_info
from sessions import load_saved_villages, all_saves_userid, all_saves_info, save_info, new_village

load_saved_villages()

print(" [+] Loading server...")
from flask import Flask, render_template, send_from_directory, request, redirect, session, Response
from flask.debughelpers import attach_enctype_error_multidict
from command import command
from engine import timestamp_now
from version import version_name
from constants import Constant
from quests import get_quest_map
from bundle import ASSETS_DIR, STUB_DIR, TEMPLATES_DIR, BASE_DIR, SAVES_DIR_BACKUP

host = '0.0.0.0'
site = 'erasuke.com'
port = 5050

app = Flask(__name__, template_folder=TEMPLATES_DIR)

print(" [+] Connecting to database...")

def get_database():
   CONNECTION_STRING = f"mongodb://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_IP')}:{os.getenv('DB_PORT')}/?retryWrites=true&w=majority"
   client = MongoClient(CONNECTION_STRING)
   return client['socialworld']

db = get_database()
se = db["se"]

print(" [+] Configuring server routes...")

##########
# ROUTES #
##########

## PAGES AND RESOURCES


@app.route("/", methods=['GET', 'POST'])
def login():
  # Log out previous session
  session.pop('USERID', default=None)
  session.pop('GAMEVERSION', default=None)
  # Reload saves. Allows saves modification without server reset DISABLED CUZ IT POSSIBLY CAUSES null SAVES
  #load_saved_villages()
  # If logging in, set session USERID, and go to play
  if request.method == 'POST':
    msg = ''
    password = request.form["password"]
    bytePassword = password.encode('utf-8')
    email = request.form["email"].lower()
    account = se.find_one({"email":email})
    print(account)
    print(email)
    #print(password)
    if account != None:
      db_hash = account["password"].encode('utf-8')
      if bcrypt.checkpw(bytePassword,db_hash):
        session['USERID'] = account["userid"]
        session['GAMEVERSION'] = "SocialEmpires0926bsec.swf"
        print("[LOGIN] USERID:", account["userid"])
        print("[LOGIN] GAMEVERSION:", "SocialEmpires0926bsec.swf")
        return redirect("/play.html")
      else:
        print("Wrong password")
        msg = "Invalid e-mail/password entered!"
    else:
      print("Account not existing")
      msg = "Invalid e-mail/password entered!"
    return render_template("login.html", LOGmsg=msg)
  # Login page
  if request.method == 'GET':
    return render_template("login.html")

@app.route("/keeponline")
def keeponline():
  return "Online!"

@app.route("/play.html")
def play():
  print(session)

  if 'USERID' not in session:
    return redirect("/")
  if 'GAMEVERSION' not in session:
    return redirect("/")

  if session['USERID'] not in all_saves_userid():
    return redirect("/")

  USERID = session['USERID']
  GAMEVERSION = session['GAMEVERSION']
  print("[PLAY] USERID:", USERID)
  print("[PLAY] GAMEVERSION:", GAMEVERSION)
  return render_template("play.html",
                         save_info=save_info(USERID),
                         serverTime=timestamp_now(),
                         version=version_name,
                         GAMEVERSION=GAMEVERSION,
                         SERVERIP=site, ASSETSIP=ASSETS_DIR)


@app.route("/new.html", methods=["POST"])
def new():
  username = request.form["Regusername"]
  password = request.form["Regpassword"]
  bytePassword = password.encode('utf-8')
  mySalt = bcrypt.gensalt()
  pwd_hash = bcrypt.hashpw(bytePassword, mySalt)
  email = request.form["Regemail"].lower()
  msg = ''
  if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
    msg = 'Invalid email address!'
  elif not re.match(r'[A-Za-z0-9]+', username):
    msg = 'Username may only contain characters and numbers!'
  elif not username or not password or not email:
    msg = 'Please fill in everything.'
  elif password == "5a93eccd2caa9166a9aa550ab4670e63ce637445a86081ffcc9b24ca317c99196b19df7b0f55238a5b27664ed95ba6f6bbe4b21ea975543fb063b4bd77cfced5":
    msg = 'Please fill in everything.'
  elif len(username) < 3 or len(username) > 20:
    msg = 'Your username should be between 3 and 20 characters!'
  else:
    account = se.find_one({"email":email})
    if account == None:
      session['USERID'] = new_village(username)
      session['GAMEVERSION'] = "SocialEmpires0926bsec.swf"
      se.insert_one({"userid":session['USERID'],"email":email,"password":pwd_hash.decode("utf-8")})
      return redirect("play.html")
    else:
      msg = 'An account with this e-mail already exists!'
  return render_template("login.html", REGmsg=msg)


@app.route("/crossdomain.xml")
def crossdomain():
  return send_from_directory(STUB_DIR, "crossdomain.xml")

@app.route("/saves/<path:path>")
def saves(path):
  return send_from_directory(SAVES_DIR_BACKUP, path)

@app.route("/img/<path:path>")
def images(path):
  return send_from_directory(TEMPLATES_DIR + "/img", path)


@app.route("/css/<path:path>")
def css(path):
  return send_from_directory(TEMPLATES_DIR + "/css", path)


## GAME STATIC


#@app.route(
#  "/default01.static.socialpointgames.com/static/socialempires/swf/05122012_projectiles.swf"
#)
#def similar_05122012_projectiles():
#  return send_from_directory(ASSETS_DIR + "/swf", "20130417_projectiles.swf")
#
#
#@app.route(
#  "/default01.static.socialpointgames.com/static/socialempires/swf/05122012_magicParticles.swf"
#)
#def similar_05122012_magicParticles():
#  return send_from_directory(ASSETS_DIR + "/swf",
#                             "20131010_magicParticles.swf")
#
#
#@app.route(
#  "/default01.static.socialpointgames.com/static/socialempires/swf/05122012_dynamic.swf"
#)
#def similar_05122012_dynamic():
#  return send_from_directory(ASSETS_DIR + "/swf", "120608_dynamic.swf")


@app.route(
  "/default01.static.socialpointgames.com/static/socialempires/<path:path>")
def static_assets_loader(path):
    # Add exceptions for missing files
    if path == "swf/05122012_projectiles.swf":
      URL = "https://cdn.jsdelivr.net/gh/AcidCaos/socialemperors/assets/swf/20130417_projectiles.swf"
      filename = os.path.basename("20130417_projectiles.swf")
    elif path == "swf/05122012_magicParticles.swf":
      URL = "https://cdn.jsdelivr.net/gh/AcidCaos/socialemperors/assets/swf/20131010_magicParticles.swf"  
      filename = os.path.basename("20131010_magicParticles.swf")
    elif path == "swf/05122012_dynamic.swf":
      URL = "https://cdn.jsdelivr.net/gh/AcidCaos/socialemperors/assets/swf/120608_dynamic.swf"
      filename = os.path.basename("120608_dynamic.swf")


    # Replit size limitations: download file from github (due to cors it doesn't work directly from the game)
    else:
      URL = f"https://socialassets.michielvan4.repl.co/assets.php?url=https://cdn.jsdelivr.net/gh/AcidCaos/socialemperors/assets/{path}"
      filename = os.path.basename(path)
#    r = requests.get(URL, stream=True)
    return redirect(URL)
  # return send_from_directory(ASSETS_DIR, path)
  #if not os.path.exists(ASSETS_DIR + "/" + path):
  #  # File does not exists in provided assets
  #  if not os.path.exists(f"{BASE_DIR}/download_assets/assets/{path}"):
  #    # Download file from SP's CDN if it doesn't exist
#
  #    # Make directory
  #    directory = os.path.dirname(f"{BASE_DIR}/download_assets/assets/{path}")
  #    #if not os.path.exists(directory):
  #    #  os.makedirs(directory)
#
  #    # Download File
  #    URL = f"https://cdn.jsdelivr.net/gh/AcidCaos/socialemperors/assets/{path}"
  #    try:
  #      response = urllib.request.urlretrieve(
  #        URL, f"{BASE_DIR}/download_assets/assets/{path}")
  #    except urllib.error.HTTPError:
  #      return ("", 404)
#
  #    print(f"====== DOWNLOADED ASSET: {URL}")
  #    return send_from_directory(os.path.join(p, "download_assets", "assets"), path)
  #  else:
  #    # Use downloaded CDN asset
  #    print(f"====== USING EXTERNAL: download_assets/assets/{path}")
  #    try:
  #      return send_from_directory(os.path.join(p, "download_assets", "assets"), path)
  #    except Exception as e:
  #      print(e)
  #else:
  #  # Use provided asset
  #  return send_from_directory(ASSETS_DIR, path)


## GAME DYNAMIC


@app.route(
  "/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/track_game_status.php",
  methods=['POST'])
def track_game_status_response():
  status = request.values['status']
  installId = request.values['installId']
  user_id = request.values['user_id']

  print(
    f"track_game_status: status={status}, installId={installId}, user_id={user_id}. --",
    request.values)
  return ("", 200)


@app.route(
  "/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_game_config.php"
)
def get_game_config_response():
  spdebug = None

  USERID = request.values['USERID']
  user_key = request.values['user_key']
  if 'spdebug' in request.values:
    spdebug = request.values['spdebug']
  language = request.values['language']

  print(f"get_game_config: USERID: {USERID}. --", request.values)
  return get_game_config()


@app.route(
  "/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_player_info.php",
  methods=['POST'])
def get_player_info_response():

  USERID = request.values['USERID']
  user_key = request.values['user_key']
  spdebug = request.values['spdebug'] if 'spdebug' in request.values else None
  language = request.values['language']
  neighbors = request.values[
    'neighbors'] if 'neighbors' in request.values else None
  client_id = request.values['client_id']
  user = request.values['user'] if 'user' in request.values else None
  map = int(request.values['map']) if 'map' in request.values else None

  print(f"get_player_info: USERID: {USERID}. user: {user} --", request.values)

  # Current Player
  if user is None:
    return (get_player_info(USERID), 200)
  # Arthur
  elif user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_1 \
  or user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_2 \
  or user == Constant.NEIGHBOUR_ARTHUR_GUINEVERE_3:
    return (get_neighbor_info(user, map), 200)
  # Quest
  elif user.startswith("100000"):  # Dirty but quick
    return get_quest_map(user)
  # Neighbor
  else:
    return (get_neighbor_info(user, map), 200)


@app.route(
  "/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/sync_error_track.php",
  methods=['POST'])
def sync_error_track_response():
  spdebug = None

  USERID = request.values['USERID']
  user_key = request.values['user_key']
  if 'spdebug' in request.values:
    spdebug = request.values['spdebug']
  language = request.values['language']
  error = request.values['error']
  current_failed = request.values['current_failed']
  tries = request.values['tries'] if 'tries' in request.values else None
  survival = request.values['survival']
  previous_failed = request.values['previous_failed']
  description = request.values['description']
  user_id = request.values['user_id']

  print(
    f"sync_error_track: USERID: {USERID}. [Error: {error}] tries: {tries}. --",
    request.values)
  return ("", 200)


@app.route("/null")
def flash_sync_error_response():
  sp_ref_cat = request.values['sp_ref_cat']

  if sp_ref_cat == "flash_sync_error":
    reason = "reload On Sync Error"
  elif sp_ref_cat == "flash_reload_quest":
    reason = "reload On End Quest"
  elif sp_ref_cat == "flash_reload_attack":
    reason = "reload On End Attack"

  print("flash_sync_error", reason, ". --", request.values)
  return redirect("/play.html")


@app.route(
  "/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/command.php",
  methods=['POST'])
def command_response():
  spdebug = None

  USERID = request.values['USERID']
  user_key = request.values['user_key']
  if 'spdebug' in request.values:
    spdebug = request.values['spdebug']
  language = request.values['language']
  client_id = request.values['client_id']

  print(f"command: USERID: {USERID}. --", request.values)

  data_str = request.values['data']
  data_hash = data_str[:64]
  assert data_str[64] == ';'
  data_payload = data_str[65:]
  data = json.loads(data_payload)

  command(USERID, data)

  return ({"result": "success"}, 200)


@app.route(
  "/dynamic.flash1.dev.socialpoint.es/appsfb/socialempiresdev/srvempires/get_continent_ranking.php"
)
def get_continent_ranking_response():

  USERID = request.values['USERID']
  worldChange = request.values['worldChange']
  if 'spdebug' in request.values:
    spdebug = request.values['spdebug']
  town_id = request.values['map']
  user_key = request.values['user_key']

  # TODO - stub
  response = {
    "world_id":
    0,
    "continent": [
      {
        "posicion": 0,
        "nivel": 1,
        "user_id": 1111
      },  # villages/AcidCaos
      {
        "posicion": 1,
        "nivel": 0
      },
      {
        "posicion": 2,
        "nivel": 0
      },
      {
        "posicion": 3,
        "nivel": 0
      },
      {
        "posicion": 4,
        "nivel": 0
      },
      {
        "posicion": 5,
        "nivel": 0
      },
      {
        "posicion": 6,
        "nivel": 0
      },
      {
        "posicion": 7,
        "nivel": 0
      }
    ]
  }
  return (response)


########
# MAIN #
########

print(" [+] Running server...")

if __name__ == '__main__':
  app.secret_key = 'SECRET_KEY'
  app.run(host=host, port=port, debug=False)
