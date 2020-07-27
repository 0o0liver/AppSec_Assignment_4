from flask import Flask, render_template, url_for, request, redirect, flash, session, abort
import hashlib
import os
import subprocess
from os import urandom
import string
import random
from flask_wtf.csrf import CSRFProtect, CSRFError
import sqlite3

# UDC
class user:
	def __init__(self, username, password, mfa, salt):
		self.username = username
		self.password = password
		self.mfa = mfa
		self.salt = salt

# Global Storage
app = Flask(__name__)
app.secret_key = urandom(16)
app.config.update(
	SESSION_COOKIE_SAMESITE = 'Lax'
)
csrf = CSRFProtect(app)
users = dict()

# Route
@app.route('/login', methods=['GET', 'POST'])
def login():
	if 'username' in session:
		return redirect(url_for('spell_check'))

	message = ""

	if request.method == "POST":
		try:
			username = request.form['uname']
			password = request.form['pword']
			mfa = request.form['2fa']
			with sqlite3.connect("database.db") as conn:
				conn.row_factory = sqlite3.Row
				if ( not user_exist(username, conn) or not correct_password(username, password, conn)):
					message = "Username or Password Incorrect!"
					return render_template('login.html', message=message), 400
					conn.close()
				if ( not correct_2fa(username, mfa, conn)):
					message = "Two-factor authentication failure!"
					return render_template('login.html', message=message), 400
					conn.close()
				login_user(username, conn)
				session["username"] = username
				return render_template('successfully_login.html')
				conn.close()
		except:
			message = "Failure: something else is wrong!"
			return render_template('login.html', message=message), 500
			conn.close()
	else:
		return render_template('login.html', message=message)

@app.route('/register', methods=['GET', 'POST'])
def register():
	message = ""

	if request.method == "POST":
		try:
			username = request.form['uname']
			password = request.form['pword']
			#retype_password = request.form['rpword']
			mfa = request.form['2fa']
			# Check if password match up
			#if (password != retype_password):
			#	message = "Failure: Password doesn't match!"
			#	return render_template('register.html', message=message), 400
			# Every check is passed, registering new user
			try:
				with sqlite3.connect("database.db") as conn:
					register_new_user(username, password, mfa, conn)
					message = "Success!"
					return render_template('register.html', message=message)
					conn.close()
			except sqlite3.IntegrityError:
				message = "Failure: User already exist!"
				return render_template('register.html', message=message), 400
				conn.close()
		except:
			message = "Failure: something else is wrong!"
			return render_template('register.html', message=message), 500
			conn.close()
	else:
		return render_template('register.html', message = message)


@app.route('/spell_check', methods=['GET', 'POST'])
def spell_check():
	if 'username' in session:
		error = ""
		input_text = ""
		misspelled = list()
		if request.method == "POST":
			# collect input text
			input_text = request.form['inputtext']			

			# Writing input text to a file because a.out take file as input
			temp_file = open("temp.txt", "w")
			temp_file.write(input_text)
			temp_file.close()

			# executing main
			output = subprocess.check_output("./main temp.txt wordlist.txt", shell=True).decode('utf-8')
			
			# remove temporary file
			os.remove("temp.txt")

			# process output
			parse_misspelled(output, misspelled)

			# insert query and result to database
			try:
				with sqlite3.connect("database.db") as conn:
					conn.execute("PRAGMA foreign_keys = 1")
					cur = conn.cursor()
					cur.execute("INSERT INTO queries (submitter, query, result) VALUES (?,?,?)", (session["username"], input_text, ",".join(misspelled)))
					print("INSERT INTO queries (submitter, query, result) VALUES (?,?,?)", (session["username"], input_text, ",".join(misspelled)))
					conn.commit()
					return render_template('check.html', input_text=input_text, misspelled=misspelled, error=error, username=session["username"])
					conn.close()
			except:
				error = "Database Insertion Error!"
				return render_template('check.html', input_text=input_text, misspelled=misspelled, error=error, username=session["username"])
		else:
			return render_template('check.html', input_text=input_text, misspelled=misspelled, error=error, username=session["username"])
	else:
		return redirect(url_for('login'))

@app.route('/logout', methods=['GET'])
def logout():
	if 'username' in session:
		logout_user(session["username"])
		session.clear()
		return redirect(url_for('login'))

	else:
		return redirect(url_for('login'))


@app.route('/successfully_login', methods=['GET'])
def successfully_login():
	if 'username' in session:
		return render_template('successfully_login.html')
	else:
		return redirect(url_for('login'))


@app.route('/history', methods=["GET", "POST"])
def history():
	if 'username' in session:
		if request.method == "POST":
			if session["username"] == "admin":
				username = request.form["username"]
				with sqlite3.connect("database.db") as conn:
					conn.row_factory = sqlite3.Row
					cur = conn.cursor()
					cur.execute("SELECT * FROM queries WHERE submitter=?", (username,))
					print("SELECT * FROM queries WHERE submitter=?", (username,))
					rows = cur.fetchall()
					return render_template('history.html', rows=rows, row_len=str(len(rows)), username=session["username"], after_post=True)
					conn.close()
			else:
				abort(401)
		else:
			with sqlite3.connect("database.db") as conn:
				conn.row_factory = sqlite3.Row
				cur = conn.cursor()
				cur.execute("SELECT * FROM queries WHERE submitter=?", (session["username"],))
				print("SELECT * FROM queries WHERE submitter=?", (session["username"],))
				rows = cur.fetchall()
				return render_template('history.html', rows=rows, row_len=str(len(rows)), username=session["username"], after_post=False)
				conn.close()
	else:
		return redirect(url_for('login'))


@app.route('/history/<queryid>', methods=["GET"])
def query_review(queryid):
	if 'username' in session:
		# check if queryid is in valid format
		if not valid_queryid(queryid):
			abort(404)

		# check if queryid has a valid value or not 
		query_id = int(queryid[5:])
		if not query_exist(query_id):
			abort(404)

		# check is current user has the permission to view selected query
		if permitted_user(session["username"], query_id) or session["username"] == "admin":
			with sqlite3.connect("database.db") as conn:
				conn.row_factory = sqlite3.Row
				cur = conn.cursor()
				cur.execute("SELECT * FROM queries WHERE id=?", (query_id, ))
				print("SELECT * FROM queries WHERE id=?", (query_id, ))
				rows = cur.fetchall()
				return render_template("query_review.html", rows=rows)
				conn.close()
		else:
			abort(401)
	else:
		return redirect(url_for('login'))



@app.route("/login_history", methods=["GET", "POST"])
def login_history():
	if "username" in session:
		if session["username"] == "admin":
			if request.method == "POST":
				username = request.form["userid"]
				with sqlite3.connect("database.db") as conn:
					conn.row_factory = sqlite3.Row
					cur = conn.cursor()
					cur.execute("SELECT * FROM logins WHERE username=?", (username, ))
					print("SELECT * FROM logins WHERE username=?", (username, ))
					rows = cur.fetchall()
					return render_template("login_history.html", after_post=True, rows=rows)
			else:
				return render_template("login_history.html", after_post=False)
		else:
			abort(401)
	else:
		return redirect(url_for('login'))

	
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
	return render_template("/csrf_error.html", reason=e.description), 400

# Utility Functions
def user_exist(username, conn):
	cur = conn.cursor()
	cur.execute("SELECT COUNT(*) FROM users WHERE username=?", (username,))
	print("SELECT COUNT(*) FROM users WHERE username=?", (username,))
	rows = cur.fetchall()
	return rows[0]["COUNT(*)"] == 1

def register_new_user(username, password, mfa, conn):
	salt = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
	salted_password = password + salt
	hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()
	cur = conn.cursor()
	cur.execute("INSERT INTO users (username, password, salt, mfa) VALUES(?,?,?,?)", (username, hashed_password, salt, mfa))
	print("INSERT INTO users (username, password, salt, mfa) VALUES(?,?,?,?)", (username, hashed_password, salt, mfa))
	conn.commit()

def correct_password(username, password, conn):
	cur = conn.cursor()
	cur.execute("SELECT password, salt FROM users WHERE username=?", (username,))
	print("SELECT password, salt FROM users WHERE username=?", (username,))
	rows = cur.fetchall()

	salt = rows[0]["salt"]
	salted_password = password + salt
	hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()
	return rows[0]["password"] == hashed_password

def correct_2fa(username, mfa, conn):
	cur = conn.cursor()
	cur.execute("SELECT mfa FROM users WHERE username=?", (username,))
	print("SELECT mfa FROM users WHERE username=?", (username,))
	rows = cur.fetchall()
	return rows[0]["mfa"] == int(mfa)

def parse_misspelled_count(output):
	return int(output.split('\n')[0].split(': ')[-1])

def parse_misspelled(output, misspelled):
	if parse_misspelled_count(output) == 0:
		return
	misspelled.extend(output.split('\n')[1:-1])

def valid_queryid(queryid):
	if queryid[:5] == "query":
		try:
			int(queryid[5:])
			return True
		except:
			return False
	return False

def query_exist(query_id):
	if query_id <= 0:
		return False
	with sqlite3.connect("database.db") as conn:
		conn.row_factory = sqlite3.Row
		cur = conn.cursor()
		cur.execute("SELECT COUNT(*) FROM queries")
		print("SELECT COUNT(*) FROM queries")
		rows = cur.fetchall()
		if query_id > rows[0]["COUNT(*)"]:
			return False
			conn.close()
	return True
	conn.close()

def permitted_user(username, query_id):
	with sqlite3.connect("database.db") as conn:
		conn.row_factory = sqlite3.Row
		cur = conn.cursor()
		cur.execute("SELECT submitter FROM queries WHERE id=?", (query_id,))
		print("SELECT submitter FROM queries WHERE id=?", (query_id,))
		rows = cur.fetchall()
		if username == rows[0]["submitter"]:
			return True
			conn.close()
		return False
		conn.close()

def login_user(username, conn):
	cur = conn.cursor()
	cur.execute("INSERT INTO logins(username) VALUES (?)", (username, ))
	print("INSERT INTO logins(username) VALUES (?)", (username, ))
	conn.commit()

def logout_user(username):
	with sqlite3.connect("database.db") as conn:
		cur = conn.cursor()
		cur.execute("UPDATE logins SET logout_time=(DATETIME('now', 'localtime')) WHERE username=? AND logout_time='N/A'", (username,))
		print("UPDATE logins SET logout_time=(DATETIME('now', 'localtime')) WHERE username=? AND logout_time='N/A'", (username,))
		conn.commit()

if __name__ == "__main__":
	app.run(debug=True)