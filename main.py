import json
import sanic
import sanic.response
import base64
import os
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader

app = sanic.Sanic("orbite")
password = "b3JiaXRlJXBpcnhjeS5jaGFtc2VkZGlu"

env = Environment(
  loader=FileSystemLoader(
    './templates', 
    encoding='utf8'
  )
)

def add_login(email:str, password:str):
    with open("accounts.json") as f:
        file = json.load(f)

    file.append(
        {
            "email":email,
            "password":password
        }
    )
    try:
            
        with open("accounts.json", "w") as f:
            json.dump(file,f,indent=2)
            return True
    except:
        return False
    
def add_submission(info):
    with open("submissions.json") as f:
        file = json.load(f)

    file.append(
        {
            "firstname":info["firstName"],
            "lastname":info["lastName"],
            "ighandle":info["instagram"],
            "email":info["email"],
        }
    )
    try:
            
        with open("submissions.json", "w") as f:
            json.dump(file,f,indent=2)
            return True
    except:
        return False
    
def validate_login(email:str, password:str):
    with open("accounts.json") as f:
        file = json.load(f)
        
    for account in file:
        stored_email = account["email"]
        stored_password = account["password"]
        print(stored_email,stored_password)
        if email == stored_email and password == stored_password:
            return True
        else:
            continue
    return False
    
def render_template(file_, **kwargs) -> str:
  template = env.get_template(file_)
  return sanic.response.html(template.render(**kwargs))
        

@app.route("/")
async def index(request: sanic.HTTPResponse):
    account = {
        "title_text": "Sign-Up",
        "waitlist_text": "Sign Up to Join waitlist",
        "waitlist_link": '''onclick="location.href = '#contact'"''',
        "href": "#contact",
        "form_html": """
            <h2>Join the ORBITE Community</h2>
            <p>
                Be the first to access new drops, exclusive events, and
                members-only content.
            </p>
            <form class="newsletter-form" id="signup-form" action="/register" method="POST" style="display: flex; flex-direction: column; gap: 10px; max-width: 300px;">
                <input
                    type="email"
                    name="email"
                    placeholder="Your email address"
                    class="newsletter-input"
                    required
                />
                <input
                    type="password"
                    name="password"
                    placeholder="Create a password"
                    class="newsletter-input"
                    required
                />
                <button type="submit" class="newsletter-btn">Sign Up</button>
            </form>
            <br>
            <p>Already have an account? <a href="/login">Login.</a></p>
        """
    }
    if str(request.cookies).__contains__("@"):
        print("hi")
        account["title_text"] = "Sign Out"
        account["href"] = "/logout"
        account["waitlist_link"] = 'id="notify-btn"'
        account["waitlist_text"] = 'Notify Me'
        account["form_html"] = """
            <h2>Welcome to the ORBITE Community</h2>
            <p>
                You are on of the first to access new drops, exclusive events, and
                members-only content.
            </p>
            <br>
            <p>Signout? <a href="/logout">Click here.</a></p>
        """
        
    return render_template("index.html",account=account)

@app.route("/logout")
async def logout(request):
    response = sanic.response.redirect("/")
    date_str = (datetime.utcnow() - timedelta(days=1)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    dt_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")
    response.cookies["email"] = ""
    return response

@app.route("/register", methods=["POST"])
async def register(request: sanic.Request):
    try:
        if not request.body:
            return sanic.response.json(
                {"error": "No data provided"}, 
                status=400
            )

        # Parse the request data
        try:
            data = json.loads(request.body.decode())
        except json.JSONDecodeError:
            return sanic.response.json(
                {"error": "Invalid JSON data"}, 
                status=400
            )

        # Validate required fields
        if "email" not in data or "password" not in data:
            return sanic.response.json(
                {"error": "Email and password are required"}, 
                status=400
            )

        # Check if accounts.json exists, create if not
        if not os.path.exists("accounts.json"):
            with open("accounts.json", "w") as f:
                json.dump([], f)

        # Read existing accounts
        try:
            with open("accounts.json", "r") as f:
                accounts = json.load(f)
        except json.JSONDecodeError:
            accounts = []

        # Check if email already exists
        if any(account["email"] == data["email"] for account in accounts):
            return sanic.response.json(
                {"error": "Email already registered"}, 
                status=409
            )

        # Add new account
        accounts.append({
            "email": data["email"],
            "password": data["password"],
            "joined_waitlist": False
        })

        # Write back to file
        with open("accounts.json", "w") as f:
            json.dump(accounts, f, indent=2)

        # Set cookie and return success
        response = sanic.response.json(
            {"success": True, "email": data["email"]},
            status=201
        )
        response.cookies["email"] = data["email"]
        response.cookies["email"]["path"] = "/"
        response.cookies["email"]["httponly"] = True
        return response

    except Exception as e:
        return sanic.response.json(
            {"error": f"Internal server error: {str(e)}"}, 
            status=500
        )



@app.route("/login",methods=["GET","POST"])
async def login(request:sanic.HTTPResponse):
    if request.method == "GET":
        if str(request.cookies).__contains__("@"):
            return sanic.response.redirect("/")
        return await sanic.response.file("templates/login.html")
    elif request.method == "POST" and request.body:
        data = request.body.decode()
        print(data)
        info = json.loads(data)
        valid = validate_login(info["email"],info["password"])
        if valid:
            resp =  await sanic.response.file("templates/index.html")
            resp.cookies["email"] = info["email"]
            resp.cookies["email"]["path"] = "/"  # Global across the site
            resp.cookies["email"]["httponly"] = True
            resp.cookies["email"]["samesite"] = "Lax"
            return resp
        else:
            return sanic.response.empty(status=401)
        
    
@app.route("/sl", methods=["POST"])
async def secret_login(request: sanic.HTTPResponse):
    if request.body:
        entered_password = json.loads(request.body.decode())["password"]
        correct = bool(entered_password == base64.b64decode(password).decode())
        if correct:
            return sanic.response.json({"result": "success"})#type:ignore
        return sanic.response.json({"result": f"{entered_password} is wrong."},status=401)#type:ignore
    
@app.route("/accounts", methods = ["GET","POST"])
async def accounts(request:sanic.HTTPResponse):
    if request.method == "GET":
        return await sanic.response.file("templates/accounts.html")
    elif request.method == "POST" and request.body:
        entered_password = json.loads(request.body.decode())["password"]
        correct = bool(entered_password == base64.b64decode(password).decode())
        if correct:
            return await sanic.response.file("accounts.json")#type:ignore
        return sanic.response.json({"result": f"{entered_password} is wrong."},status=401)#type:ignore
    
@app.route("/submissions", methods = ["GET","POST"])
async def submissions(request:sanic.HTTPResponse):
    if request.method == "GET":
        return await sanic.response.file("templates/submissions.html")
    elif request.method == "POST" and request.body:
        entered_password = json.loads(request.body.decode())["password"]
        correct = bool(entered_password == base64.b64decode(password).decode())
        if correct:
            return await sanic.response.file("submissions.json")#type:ignore
        return sanic.response.json({"result": f"{entered_password} is wrong."},status=401)#type:ignore

@app.route("/check-picked", methods=["GET"])
async def check_picked(request):
    if not request.cookies.get("email"):
        return sanic.response.json({"picked": False})
    
    user_email = request.cookies.get("email")
    
    with open("submissions.json", "r") as f:
        submissions = json.load(f)
        for user in submissions:
            if user["email"] == user_email:
                return sanic.response.json({"picked": user.get("picked", False)})
    
    return sanic.response.json({"picked": False})

@app.route("/update-pick", methods=["GET","POST"])
async def update_pick(request):
    try:
        # Verify password first (using your existing auth system)
        if not request.body:
            return sanic.response.json({"success": False, "error": "No data provided"}, status=400)
        
        data = json.loads(request.body.decode())
        index = data.get("index")
        picked = data.get("picked")
        
        # Read current submissions
        with open("submissions.json", "r") as f:
            submissions = json.load(f)
        
        # Validate index
        if index is None or picked is None:
            return sanic.response.json({"success": False, "error": "Missing fields"}, status=400)
        
        if index < 0 or index >= len(submissions):
            return sanic.response.json({"success": False, "error": "Invalid index"}, status=400)
        
        # Update the picked status
        submissions[index]["picked"] = picked
        
        # Write back to file
        with open("submissions.json", "w") as f:
            json.dump(submissions, f, indent=2)
        
        return sanic.response.json({"success": True})
    
    except Exception as e:
        return sanic.response.json({"success": False, "error": str(e)}, status=500)

# Add these new endpoints to main.py

@app.route("/user-status", methods=["GET"])
async def user_status(request):
    if not request.cookies.get("email"):
        return sanic.response.json({
            "logged_in": False,
            "waitlist_status": None,
            "picked": False
        })
    
    user_email = request.cookies.get("email")
    
    # Check account status
    with open("accounts.json", "r") as f:
        accounts = json.load(f)
        account = next((a for a in accounts if a["email"] == user_email), None)
    
    if not account:
        return sanic.response.json({
            "logged_in": False,
            "waitlist_status": None,
            "picked": False
        })
    
    # Check waitlist status
    with open("submissions.json", "r") as f:
        submissions = json.load(f)
        submission = next((s for s in submissions if s["account_email"] == user_email), None)
    
    return sanic.response.json({
        "logged_in": True,
        "waitlist_status": "joined" if submission else "not_joined",
        "picked": submission["picked"] if submission else False,
        "email": user_email
    })

# Update the submit endpoint to link accounts
@app.route("/submit", methods=["POST"])
async def submit(request: sanic.HTTPResponse):
    if request.body:
        data = request.body.decode()
        info = json.loads(data)
        
        # Link submission to account
        info["account_email"] = request.cookies.get("email", "")
        
        # Update account to mark as joined waitlist
        with open("accounts.json", "r+") as f:
            accounts = json.load(f)
            for account in accounts:
                if account["email"] == info["account_email"]:
                    account["joined_waitlist"] = True
                    break
            f.seek(0)
            json.dump(accounts, f, indent=2)
            f.truncate()
        
        add_submission(info)
        return sanic.response.text(str(request.body))
    else:
        return sanic.response.empty()

if __name__ == "__main__":
    app.run(port=1942)#type:ignore
