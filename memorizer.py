import streamlit as st
import csv
import random
import urllib
from urllib.request import urlopen
import re
import pickle
import pygame
import requests
from io import BytesIO

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
            pygame.init()
            
            url = match.group()
            
            # Fetch the MP3 file from the URL
            response = requests.get(url)
            mp3_data = BytesIO(response.content)
            
            # Load the MP3 file into pygame
            pygame.mixer.music.load(mp3_data)
            
            # Play the MP3 file
            pygame.mixer.music.play()
            
            # Wait until the music finishes playing
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)            
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
        st.session_state.phrase_rating = pickle.load(open("phrase_rating.p", "rb"))
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
        t1, t2     = random.choice(st.session_state.translations)       
        t1_1, t2_1 = random.choice(st.session_state.translations)       
        t1_2, t2_2 = random.choice(st.session_state.translations)       
        t1_3, t2_3 = random.choice(st.session_state.translations)       
        

        if (get_safe(t1) >= avg_rating) and (get_safe(t2) <= avg_rating + 1):
            res = t2, t1, t1_1.strip() + ' ' + t1_2.strip() + ' ' + t1_3.strip()

        if (get_safe(t1) < avg_rating):
            res =  t1, t2, t2_1.strip() + ' ' + t2_2.strip() + ' ' + t2_3.strip()
        else:
            res = t2, t1, t1_1.strip() + ' ' + t1_2.strip() + ' ' + t1_3.strip()

        base_words  = [w.lower() for w in res[1].strip().split(' ')]
        extra_words = list(set([w.lower() for w in res[2].strip().split(' ')]))
        extra_words = extra_words[:int(len(extra_words) * st.session_state.difficulty_level / 100)]
        
        words = list(set(base_words + extra_words))
        
        random.shuffle(words)
        
        return res[0], res[1], words

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
        pickle.dump(st.session_state.phrase_rating, open("phrase_rating.p", "wb"))
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

st.write("""
# Greek trainer
This app helps to memorize **Greek** phrases!""")

st.subheader('Phrase translation')

original, translation, words = st.session_state.random_pair

col1,col2 = st.columns([20,1])

col1.write('# ' + original) 
col2.button(':loud_sound:',on_click=sayitingreek, args=[original])

with st.sidebar:
    difficulty_level = st.slider("Select dificulty level",0,100,70)
    st.button('Reload dict.csv', on_click=do_reload)
    st.write(f'Length of the dict: {len(st.session_state.translations)}')
    st.write(f'Coverage of the dict: {round(len(st.session_state.phrase_rating) * 50 / len(st.session_state.translations),2)}%')
   

st.text_input('Translation:', key='translation_input', on_change=submit, disabled=True)

col1,col2,col3 = st.columns([2,1,15])
col1.button('Check', on_click=check_pressed)
col2.button(':scissors:',on_click=clear_input)

col_l = []
for wrd in words:
    col_l.append(len(wrd))
    if sum(col_l) > 30 or (words.index(wrd)+1 == len(words)):
        cols = st.columns([i + 5 for i in col_l])

        for w in words[:words.index(wrd)+1]:
            word_rating = 0
            if w in translation:                
                for phrase in st.session_state.phrase_rating:
                    if w in phrase:
                        word_rating += st.session_state.phrase_rating[phrase]
                    
            if word_rating > 1:
                cols[words.index(w)].text_input('', key=w, on_change=put_word2, args=[w])
            else:
                cols[words.index(w)].button(w, key=w,  on_click=put_word, args=[w])
        words = words[words.index(wrd)+1:]
        col_l = []
            
st.write(f'Previous Phrase: {st.session_state.this_original}')
st.write(f'Correct Translation: {st.session_state.correct_translation}')
st.write(f'Your Translation: {st.session_state.this_translation}')

col1, col2 = st.columns(2)
col1.write(f':green[Correct answers: {st.session_state.correct_answers}]')
col2.write(f':red[Incorrect answers: {str(st.session_state.incorrect_answers)}]')

