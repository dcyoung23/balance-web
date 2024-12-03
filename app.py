import os
from sql import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure database connection
if os.getenv('DATABASE_URL'):
    db = SQL(os.getenv('DATABASE_URL'))
else:
    # Local debugging
    db = SQL("postgresql://balance_user:balance@localhost/balance")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        # get balances for display on page
        balances = get_balances(db, session["user_id"])

        # format for display on page
        format_balances(balances)

        # get scheduled transactions
        scheduled = get_scheduled(db, session["user_id"])

        # format for display on page
        format_schedule(scheduled)

        return render_template("index.html", balances=balances, scheduled=scheduled)
        #next_scheduled=next_scheduled, future=future

    if request.method == "POST":
        data = {}
        # get schedule_id
        data["schedule_id"] = request.form.get("item")

        # get action
        data["action"] = request.form.get("action")

        # check if action was selected
        if not data["action"]:
            flash('Select an Action.')
            return redirect(url_for('index'))

        # get schedule item
        item = get_item(db, data["schedule_id"])

        # get types
        types = get_types(db)

        # get frequencies
        frequencies = get_frequencies(db)

        # get codes
        codes = get_codes(db)

        if data["action"] == "Snooze":
            # render snooze page
            return render_template("snooze.html", item=item)

        if data["action"] == "Edit":
            # render edit page
            return render_template("edit.html", item=item, types=types, frequencies=frequencies, codes=codes)

        else:
            update_schedule(db, data)

        return redirect(url_for('index'))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""
    # forget any user_id
    session.clear()

    # default login page on load
    if request.method == "GET":
        return render_template("login.html")

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username") or not request.form.get("password"):
            flash('Please provide a username and password.')
            return render_template("login.html")

        # query database for username
        users = db.execute("SELECT * \
                            FROM users \
                            WHERE username = :username;", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(users) != 1 or not pwd_context.verify(request.form.get("password"), users[0]["hash"]):
            flash('Username or password incorrect.')
            return render_template("login.html")

        # remember which user has logged in
        session["user_id"] = users[0]["user_id"]

        # redirect user to home page
        return redirect(url_for("index"))


@app.route("/logout")
def logout():
    """Log user out."""
    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    # default register page on load
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        # must enter a Username, Password and Confirm Password
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            flash('Please enter a Username, Password and Password Confirmation.')
            return redirect(url_for('register'))

        # passwords must match
        elif request.form.get("password") != request.form.get("confirmation"):
            flash('Passwords do not match.')
            return redirect(url_for('register'))

        # check if Username exists
        elif len(db.execute("SELECT username \
                             FROM users \
                             WHERE username = :username;", username=request.form.get("username"))) > 0:
            flash('Username already exists.')
            return redirect(url_for('register'))

        else:
            # insert new user
            db.execute("INSERT INTO users (username, hash) \
                        VALUES(:username, :hash);", username=request.form.get("username"),
                       hash=pwd_context.hash(request.form.get("password")))

            # query database for user
            user = db.execute("SELECT user_id, username \
                              FROM users \
                              WHERE username = :username;", username=request.form.get("username"))

            # remember which user has logged in
            session["user_id"] = user[0]["user_id"]

            # insert new user in balance
            db.execute("INSERT INTO balance (user_id) \
                       VALUES(:user_id);", user_id=user[0]["user_id"])

            # flash message that user successfully registered on Index
            flash('Successfully registered! Set your Balances!')
            return redirect(url_for('update'))


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    # if user reached route via GET (as by submitting a form via POST)
    if request.method == "GET":
        # Get current balances
        balances = get_balances(db, session["user_id"])

        return render_template("update.html", balances=balances)

    if request.method == "POST":
        # get user inputs
        current_input = request.form.get("current")
        available_input = request.form.get("available")

        # check if amounts were entered
        #if not request.form.get("current") or not request.form.get("available"):
        if not current_input:
            #flash('Please enter a Current and Available Amount.')
            flash('Please enter a Current Amount.')
            return redirect(url_for('update'))

        # if no available balance input set to current
        if not available_input:
                available_input = current_input

        # try convert floats
        try:
            current = float(current_input)
            available = float(available_input)

        except:
            flash('Please enter valid Amounts.')
            return redirect(url_for('update'))

        # update balances
        db.execute("UPDATE balance\
                    SET current = :current\
                    ,available = :available\
                    WHERE user_id = :user_id;", current=current, available=available, user_id=session["user_id"])

        # flash message that balances updated on Index
        flash('Balances Updated!')
        return redirect(url_for('index'))


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    # if user reached route via GET (as by submitting a form via POST)
    if request.method == "GET":
        # Get types
        types = get_types(db)

        # Get frequencies
        frequencies = get_frequencies(db)

        # Get codes
        codes = get_codes(db)

        return render_template("add.html", types=types, frequencies=frequencies, codes=codes)

    if request.method == "POST":
        # Create data dict
        data = {}

        # Add schedule fields from form
        data["name"] = request.form.get("name")
        data["type_id"] = request.form.get("type")
        data['pmt_source'] = request.form.get("pmt-source")
        data['pmt_method'] = request.form.get("pmt-method")
        data["current_dt"] = request.form.get("current")
        data["frequency_id"] = request.form.get("frequency")
        data["repeat"] = request.form.get("repeat")
        data["amount"] = request.form.get("amount")

        # check all fields were completed
        for k, v in data.items():
            if not v:
                flash('Please complete all fields.')
                return redirect(url_for('add'))

        # Insert in database
        insert_schedule(db, session["user_id"], data)

        # flash message that item added on Index
        flash('Added!')
        return redirect(url_for('index'))


@app.route("/snooze", methods=["POST"])
@login_required
def snooze():
    if request.method == "POST":
        data = {}

        # get item schedule_id from button
        data["schedule_id"] = request.form.get("item")

        # get snoozed date
        data["snoozed"] = request.form.get("snoozed")

        if not data["snoozed"]:
            # flash message that item not snoozed
            flash('Please enter a date to Snooze item.')
            return redirect(url_for('index'))

        # snooze item
        snooze_item(db, data)

        # flash message that item snoozed
        flash('Snoozed!')
        return redirect(url_for('index'))


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        # create data dict
        data = {}

        # Add schedule fields from form
        data["schedule_id"] = request.form.get("schedule_id")
        data["name"] = request.form.get("name")
        data["type_id"] = request.form.get("type")
        data['pmt_source'] = request.form.get("pmt-source")
        data['pmt_method'] = request.form.get("pmt-method")
        data["current_dt"] = request.form.get("current")
        data["frequency_id"] = request.form.get("frequency")
        data["repeat"] = request.form.get("repeat")
        data["amount"] = request.form.get("amount")
        data["action"] = "Edit"

        # check all fields were completed
        for k, v in data.items():
            if not v:
                flash('Please complete all fields.')
                return redirect(url_for('index'))

        # update schedule
        update_schedule(db, data)

        # flash message that item edited
        flash('Edited!')
        return redirect(url_for('index'))
