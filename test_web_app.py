from flask import session
from app import app
from bs4 import BeautifulSoup as bs

app.config['WTF_CSRF_ENABLED'] = False

# Testing /register

def test_get_register_page():
	response = app.test_client().get('/register')
	assert response.status_code == 200

def test_successfully_register_a_user():
	data_dict = {'uname': 'test_user', 'pword': 'oliverlbh', '2fa': '9492026942', 'submit': 'Register'}
	response = app.test_client().post('/register', data=data_dict)
	assert response.status_code == 200
	assert "Success" in bs(response.data.decode('utf-8'), features='html.parser').find(id='success').string

def test_register_with_duplicate_username():
	data_dict = {'uname': 'test_user', 'pword': 'oliverlbh', '2fa': '9492026942', 'submit': 'Register'}
	# send second request
	response1 = app.test_client().post('/register', data=data_dict)
	assert response1.status_code == 400
	assert "Failure" in bs(response1.data.decode('utf-8'), features='html.parser').find(id='success').string

# Testing /login

def test_get_login_page():
	response = app.test_client().get('/login')
	assert response.status_code == 200

def test_login_page_before_register():
	data_dict = {'uname': 'oliver', 'pword': 'oliverlbh', '2fa': '9492026942', 'submit': 'login'}
	response = app.test_client().post('/login', data=data_dict)
	assert response.status_code == 400
	assert "Incorrect" in bs(response.data.decode('utf-8'), features='html.parser').find(id='result').string

def test_incorrect_username():
	data_dict = {'uname': '9o9liver', 'pword': 'oliverlbh', '2fa': '9492026942', 'submit': 'login'}
	response = app.test_client().post('/login', data=data_dict)
	assert response.status_code == 400
	assert "Incorrect" in bs(response.data.decode('utf-8'), features='html.parser').find(id='result').string

def test_incorrect_password():
	data_dict = {'uname': 'test_user', 'pword': 'OLIVERLBH', '2fa': '9492026942', 'submit': 'login'}
	response = app.test_client().post('/login', data=data_dict)
	assert response.status_code == 400
	assert "Incorrect" in bs(response.data.decode('utf-8'), features='html.parser').find(id='result').string

def test_incorrect_2fa():
	data_dict = {'uname': 'test_user', 'pword': 'oliverlbh', '2fa': '1234567890', 'submit': 'login'}
	response = app.test_client().post('/login', data=data_dict)
	message = bs(response.data.decode('utf-8'), features='html.parser').find(id='result').string
	assert response.status_code == 400
	assert "Two-factor" in message and "failure" in message

def test_successful_login():
	data_dict = {'uname': 'test_user', 'pword': 'oliverlbh', '2fa': '9492026942', 'submit': 'Register'}
	response = app.test_client().post('/login', data=data_dict)
	print(response.data)
	assert response.status_code == 200
	assert "Success" in bs(response.data.decode('utf-8'), features='html.parser').find(id='result').string

# Testing /spell_check
def test_access_spell_check_without_session():
	response = app.test_client().get('/spell_check')
	assert response.status_code == 302

def test_access_spell_check_with_session():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'test_user'
		response = client.get('/spell_check')
		assert response.status_code == 200

def test_if_spell_check_has_inputtext():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'test_user'
		response = client.get('/spell_check')
		assert response.status_code == 200
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='inputtext')

def test_if_spell_check_has_textout_and_misspelled_after_retrieval():
	data_dict = {'inputtext': 'hello my name si oliver. Very nice to meeet you.', 'submit': 'check'}
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'test_user'
		response = client.post('/spell_check', data=data_dict)
		assert response.status_code == 200
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='textout')
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='misspelled')

def test_spell_check_accuracy():
	input_string = "Hello my nmea is oilver, I am 22 yeras old, very niceeee to meeet yuo"
	misspelled_string = "nmea,oilver,yeras,niceeee,meeet,yuo"
	data_dict = {'inputtext': input_string, 'submit': 'check'}
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'test_user'
		response = client.post('/spell_check', data=data_dict)
		assert response.status_code == 200
		assert input_string == bs(response.data.decode('utf-8'), features='html.parser').find(id='textout').string
		assert misspelled_string == bs(response.data.decode('utf-8'), features='html.parser').find(id='misspelled').string

# Testing /history
def test_history_has_numqueries():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'test_user'
		response = client.get('/history')
		assert response.status_code == 200
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='numqueries').string

def test_history_has_userquery_for_admin():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'admin'
		response = client.get("/history")
		assert response.status_code == 200
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='userquery')

def test_history_has_numqueries_after_admin_post():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'admin'
		response = client.post('/history', data={'username': 'test_user', 'submit': "Retrieve"})
		assert response.status_code == 200
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='numqueries').string

# Testing /history/query#
def test_query_review_page_has_required_tags():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'test_user'
		response = client.get('/history/query4')
		assert response.status_code == 200
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='queryid')
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='username')
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='querytext')
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='queryresults')

# Testing /login_history
def test_login_history_has_required_tags_before_post():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'admin'
		response = client.get('/login_history')
		assert response.status_code == 200
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='userid')	

def test_login_history_has_required_tags_after_post():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'admin'
		response = client.post('/login_history', data={'userid': 'test_user', 'submit': 'Retrieve'})
		assert response.status_code == 200
		assert bs(response.data.decode('utf-8'), features='html.parser').find(id='login4')

# Testing access control
def test_non_admin_user_post_to_history():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'test_user'
		response = client.post("/history", data={'username': 'test_user', 'submit': 'Retrieve'})
		assert response.status_code == 401

def test_non_admin_user_access_non_permitted_query():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'another_test_user'
		response = client.get("/history/query1")
		assert response.status_code == 401

def test_admin_access_user_query():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'admin'
		response = client.get("/history/query1")
		assert response.status_code == 200

def test_non_admin_user_retrieve_login_history():
	with app.test_client() as client:
		with client.session_transaction() as session:
			session['username'] = 'test_user'
		response0 = client.get('/login_history')
		response1 = client.post('/login_history', data={'userid': 'test_user', 'submit': 'Retrieve'})
		assert response0.status_code == 401
		assert response1.status_code == 401