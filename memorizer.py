import streamlit as st
import csv
import random
import urllib
from urllib.request import urlopen
import re
import pickle
import sqlite3
from passlib.hash import pbkdf2_sha256
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Greek phrase memorizer")#, layout="wide")

screen_width = streamlit_js_eval(js_expressions='window.innerWidth', key = 'SCR')

#st.write(f"Screen width is {screen_width}")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'username' not in st.session_state:
    st.session_state.username = ''
    
# Create or connect to the SQLite database
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()

# Create users table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
             id INTEGER PRIMARY KEY,
             username TEXT NOT NULL,
             password TEXT NOT NULL)''')

# Function to register a new user
def register(username, password):
    hashed_password = pbkdf2_sha256.hash(password)
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()

# Function to authenticate user
def login(username, password):
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if user and pbkdf2_sha256.verify(password, user[2]):
        st.success("Login successful!")
        st.write(f"Welcome back, {username}!")
        st.session_state.logged_in = True
        st.session_state.username = username
    else:
        st.error("Invalid username or password.")
        
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ''

# User registration form
def register_form():
    st.title("User Registration")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if password == confirm_password:
            register(username, password)
            st.success("Registration successful. You can now login.")
        else:
            st.error("Passwords do not match.")

# User login form
def login_form():
    st.title("User Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    st.button("Login", on_click=login, args=[username, password] )
            
if 'mp3_url' not in st.session_state:
    st.session_state.mp3_url = ''
    
def sayitingreek(text):

    url = "http://vaassl3.acapela-group.com/Services/Synthesizer"
    
    values = {
		'cl_env' : 'FLASH_AS_3.0',
		'req_snd_kbps' : 'EXT_CBR_128',
		'cl_vers' : '1-30',
		'req_snd_type' : '',
		'cl_login' : 'demo_web',
		'cl_app' : '',
		'req_asw_type' : 'INFO',
		'req_voice' : 'dimitris22k',
		'cl_pwd' : 'demo_web',
		'prot_vers' : '2',
		'req_text' : text
		}

    data = urllib.parse.urlencode(values).encode('utf-8')
	
    headers = { 
		"User-Agent" : "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0",
		"Content-Type" : "application/x-www-form-urlencoded",
		"Host" : "vaassl3.acapela-group.com" 
		}   

    req = urllib.request.Request(url, data, headers)

    try:
        response = urlopen(req)
        page = response.read()
        match = re.search(r'http://(.*)mp3', page.decode('utf-8'))
        if match: 
           st.session_state.mp3_url = match.group()
    except:
        return
    
def do_reload():
    with open('dict.csv', newline='', encoding='utf-8') as csvfile:
        st.session_state.translations = list(csv.reader(csvfile))

if 'translations' not in st.session_state:
    do_reload()
       
if 'phrase_rating' not in st.session_state:
    st.session_state.phrase_rating = dict()
else:
    try:
        st.session_state.phrase_rating = pickle.load(open(f"phrase_rating_{st.session_state.username}.p", "rb"))
    except:
        st.session_state.phrase_rating = st.session_state.phrase_rating 
    
if 'difficulty_level' not in st.session_state:
    st.session_state.difficulty_level = 50
    
if 'correct_answers' not in st.session_state:
    st.session_state.correct_answers = 0

if 'incorrect_answers' not in st.session_state:
    st.session_state.incorrect_answers = 0

if 'translation_input' not in st.session_state:
    st.session_state.translation_input = ''
    
    
def get_safe(k):
    try:
        return st.session_state.phrase_rating[k]
    except:
        return 0
    
def get_random_translation():
    try:
        avg_rating = sum(st.session_state.phrase_rating.values())/len(st.session_state.phrase_rating)
    except:
        avg_rating = 1

    while True:
        t1, t2 = random.choice(st.session_state.translations)       
        
        greek_first = (get_safe(t1) < avg_rating)
        russian_first = (get_safe(t2) < avg_rating)
        
        if greek_first or russian_first:
            break

    t1_1, t2_1 = random.choice(st.session_state.translations)       
    t1_2, t2_2 = random.choice(st.session_state.translations)       
    t1_3, t2_3 = random.choice(st.session_state.translations)       

    if greek_first:
        res =  t1, t2, t2_1.strip() + ' ' + t2_2.strip() + ' ' + t2_3.strip()
        sayitingreek(t1)
    else:
        res = t2, t1, t1_1.strip() + ' ' + t1_2.strip() + ' ' + t1_3.strip()
        
    base_words  = [w.lower() for w in res[1].strip().split(' ')]
    extra_words = list(set([w.lower() for w in res[2].strip().split(' ')]))
    extra_words = extra_words[:int(len(extra_words) * st.session_state.difficulty_level / 100)]
    
    words = list(set(base_words + extra_words))
    
    random.shuffle(words)
    
    return res[0], res[1], words, greek_first

def put_word(w):
    st.session_state.translation_input = (st.session_state.translation_input + ' ' + w).strip()
    
def put_word2(w):
    st.session_state.translation_input = (st.session_state.translation_input + ' ' + st.session_state[w]).strip()

def clear_input():
    try:
        st.session_state.translation_input = st.session_state.translation_input.replace(st.session_state.translation_input.split(' ')[-1],'').strip()
    except:
        return
    
def submit():
    st.session_state.this_original = original 
    st.session_state.correct_translation = translation 
    
    st.session_state.this_translation = st.session_state.translation_input
    st.session_state.translation_input = ''
    
    if st.session_state.this_translation.upper().strip() == st.session_state.correct_translation.upper().strip():
        st.session_state.correct_answers += 1
        st.balloons()
        try:
            st.session_state.phrase_rating[original] += 1
        except:
            st.session_state.phrase_rating[original] = 1

        # To save a dictionary to a pickle file:
        pickle.dump(st.session_state.phrase_rating, open(f"phrase_rating_{st.session_state.username}.p", "wb"))
    else:
        st.session_state.incorrect_answers += 1

def check_pressed():
    submit()
    st.session_state.random_pair = get_random_translation()   	
            
if 'random_pair' not in st.session_state:
    st.session_state.random_pair = get_random_translation()
        
if 'this_translation' not in st.session_state:
    st.session_state.this_translation = ''

if 'this_original' not in st.session_state:
    st.session_state.this_original = ''

if 'correct_translation' not in st.session_state:
    st.session_state.correct_translation = ''
    
if 'check' not in st.session_state:
    st.session_state.check = 1

def fix_mobile_columns():    
    st.write('''<style>
    [data-testid="column"] {
        width: calc(33.3333% - 1rem) !important;
        flex: 1 1 calc(33.3333% - 1rem) !important;
        min-width: calc(33.3333% - 1rem) !important;
    }
    </style>''', unsafe_allow_html=True)
	
st.write("""
# Greek trainer
This app helps to memorize **Greek** phrases!""")

st.subheader('Phrase translation')

original, translation, words, greek_first = st.session_state.random_pair

st.write('# ' + original) 
st.audio(st.session_state.mp3_url, format="audio/mpeg", loop=False)
    
with st.sidebar:
    if st.session_state.logged_in:
        st.title("Logged In")
        st.write(f"You are logged in, {st.session_state.username}!")
        st.button("Logout", on_click=logout)
    else:
        page = st.radio("Go to", ["Login", "Register"])
        
        if page == "Login":
            login_form()
        elif page == "Register":
            register_form()    
        
    difficulty_level = st.slider("Select dificulty level",0,100,70)
    st.button('Reload dict.csv', on_click=do_reload)
    st.write(f'Length of the dict: {len(st.session_state.translations)}')
    st.write(f'Coverage of the dict: {round(len(st.session_state.phrase_rating) * 50 / len(st.session_state.translations),2)}%')

st.text_input('Translation:', key='translation_input', on_change=submit, disabled=True)

col1,col2,col3 = st.columns([2,1,15])
col1.button('Check', on_click=check_pressed)
col2.button(':scissors:',on_click=clear_input)

#st.write('''<style>
#[data-testid="column"] {
#    width: fit-content !important;
#    flex: 1 1 calc(20% - 1rem) !important;
#    min-width: fit-content !important;
#}
#</style>''', unsafe_allow_html=True)

st.markdown("""
            <style>
                div[data-testid="column"] {
                    width: fit-content !important;
                    flex: unset;
                }
                div[data-testid="column"] * {
                    width: fit-content !important;
                }
            </style>
            """, unsafe_allow_html=True)
col_l = []
for wrd in words:
    col_l.append(len(wrd))
    if sum(col_l) > (30 * screen_width / 650) or (words.index(wrd)+1 == len(words)):
        cols = st.columns([1 for i in col_l])

        for w in words[:words.index(wrd)+1]:
            word_rating = 0
            if w in translation.split(' '):                
                for phrase in st.session_state.phrase_rating:
                    if w in phrase.split(' '):
                        word_rating += st.session_state.phrase_rating[phrase]
                    
            if word_rating > 1:
                cols[words.index(w)].text_input('', key=w, on_change=put_word2, args=[w])
            else:
                cols[words.index(w)].button(w, key=w,  on_click=put_word, args=[w])
        words = words[words.index(wrd)+1:]
        col_l = []
	fix_mobile_columns()
            
st.write(f'Previous Phrase: {st.session_state.this_original}')
st.write(f'Correct Translation: {st.session_state.correct_translation}')
st.write(f'Your Translation: {st.session_state.this_translation}')

col1, col2 = st.columns(2)
col1.write(f':green[Correct answers: {st.session_state.correct_answers}]')
col2.write(f':red[Incorrect answers: {str(st.session_state.incorrect_answers)}]')

