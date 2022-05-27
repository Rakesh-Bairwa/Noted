from tkinter import *
from tkinter.filedialog import askopenfile
from tkVideoPlayer import TkinterVideo

from pytesseract import pytesseract
import datetime
import pyautogui
import time

import numpy as np
import networkx as nx
import regex
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords

import os
from fpdf import FPDF
from PIL import Image
from PyPDF3 import PdfFileMerger

# path to tesseract exectable file in linux
path_to_tesseract = r"/usr/bin/tesseract"
# Providing the tesseract executable location
pytesseract.tesseract_cmd = path_to_tesseract

window = Tk()
window.title("Make Notes : Now make your notes on a click!")
window.geometry("700x450")
window.configure(bg="white")

file = ""
videoplayer = ""

def open_file():
    global file
    global videoplayer
    if (file != ""):
        videoplayer.destroy()
    file = askopenfile(mode='r', filetypes=[('Video Files', ["*.mp4", "*.png", "*.jpg", "*.jpeg"])])
    if file is not None:
        global filename
        filename = file.name
        videoplayer = TkinterVideo(master=window, scaled=True)
        videoplayer.load(r"{}".format(filename))
        videoplayer.pack(expand=True, fill="both")
        videoplayer.play()

def playAgain():
    print(filename)
    videoplayer.play()

def StopVideo():
    print(filename)
    videoplayer.stop()
 
def PauseVideo():
    print(filename)
    videoplayer.pause()    

def cropIt(img):
    left = 0
    upper = img.size[0]*0.08 # cropping 7.5% of image from top only coz ubuntu don't have bottom taskbar
    right = img.size[0] # img.size() --> [width, height]
    bottom = img.size[1]
    return img.crop((left, upper, right, bottom))

def takeNote():
    name_of_file = 'myscreen'+ str(datetime.datetime.now()) + '.png'
    img = cropIt(pyautogui.screenshot())
    img.save(name_of_file)
    extract(img, name_of_file)

def extract(img, path):
    text = pytesseract.image_to_string(img)
    notes = generate_summary(text[:-1])

    # removal of additional space from string 
    notes = re.sub(' +', ' ', notes)
    notes += "\n\n"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size = 12)
    pdf.multi_cell(185, 10, txt = "|<------Notes------>|", border = 1, align = "C")
    pdf.multi_cell(200, 5, txt = notes, align = "L")
    pdf.multi_cell(200, 10, txt = "\n**screenshot attached below of presenter screen", align = "L")

    # Fitting image to pdf Page
    # pass org image for better resolution temp = Image.open("ss1.png")
    pdf.add_page()
    size = (595, 841)
    img = img.resize(size, Image.Resampling.LANCZOS)
    img.save(path)

    pdf.image(path, x = 0, y = 10)

    if (os.path.exists("notes.pdf") == False):
        pdf.output("notes.pdf")
    else:
        pdf.output("temp.pdf")
        pdf_merger = PdfFileMerger()
        base_pdf = open("notes.pdf", "rb")
        pdf_merger.append(base_pdf)
        pdf_merger.append("temp.pdf")
        merged = open("notes.pdf", "wb")
        pdf_merger.write(merged)
        os.remove("temp.pdf")
    os.remove(path)

def read_text(data):
    article = data.split(". ")
    sentences = []
    for sentence in article:
        review = regex.sub("[^A-Za-z0-9]",' ', sentence)
        sentences.append(review.replace("[^a-zA-Z]", " ").split(" "))        
    sentences.pop()     
    return sentences

def build_similarity_matrix(sentences, stop_words):
    # Create an empty similarity matrix
    similarity_matrix = np.zeros((len(sentences), len(sentences)))
 
    for idx1 in range(len(sentences)):
        for idx2 in range(len(sentences)):
            if idx1 == idx2: #ignore if both are same sentences
                continue 
            similarity_matrix[idx1][idx2] = sentence_similarity(sentences[idx1], sentences[idx2], stop_words)

    return similarity_matrix

def sentence_similarity(sent1, sent2, stopwords=None):
    if stopwords is None:
        stopwords = []
 
    sent1 = [w.lower() for w in sent1]
    sent2 = [w.lower() for w in sent2]
 
    all_words = list(set(sent1 + sent2))
 
    vector1 = [0] * len(all_words) #makes a vector of len all_words
    vector2 = [0] * len(all_words)
 
    # build the vector for the first sentence
    for w in sent1:
        if w in stopwords:
            continue
        vector1[all_words.index(w)] += 1
 
    # build the vector for the second sentence
    for w in sent2:
        if w in stopwords:
            continue
        vector2[all_words.index(w)] += 1
 
    return 1 - nltk.cluster.util.cosine_distance(vector1, vector2)

def generate_summary(inputText, top_n=5): #top_n is no. of lines it reduce input text
    stop_words = stopwords.words('english')
    summarize_text = []

    # Step 1 - Read text anc split it
    sentences =  read_text(inputText)
    
    # Step 2 - Generate Similary Martix across sentences
    sentence_similarity_martix = build_similarity_matrix(sentences, stop_words)

    # Step 3 - Rank sentences in similarity martix
    sentence_similarity_graph = nx.from_numpy_array(sentence_similarity_martix)
    scores = nx.pagerank(sentence_similarity_graph)

    # Step 4 - Sort the rank and pick top sentences
    ranked_sentence = sorted(((scores[i],s) for i,s in enumerate(sentences)), reverse=True)
    rows = len(ranked_sentence)
    
    if (rows < top_n):
        top_n = rows
    
    for i in range(top_n):
      summarize_text.append(" ".join(ranked_sentence[i][1]))

    # Step 5 - Output the summarize text
    a = ".\n".join(summarize_text)
    return a

# center this label
lbl1 = Label(window, text="Make Notes ✎", fg="black", font="none 24 bold")
lbl1.config(anchor=CENTER)
lbl1.pack(anchor=NW)

openbtn = Button(window, text='Open', font= 10, bg="sky blue", command=lambda: open_file())
openbtn.place(x=285, y =5)
 
playbtn = Button(window, text='Play Video', font= 10, bg="sky blue", command=lambda: playAgain())
playbtn.place(x=360, y =5)
 
stopbtn = Button(window, text='Stop Video', font= 10, bg="sky blue", command=lambda: StopVideo())
stopbtn.place(x=475, y =5)
 
pausebtn = Button(window, text='Pause Video', font= 10, bg="sky blue", command=lambda: PauseVideo())
pausebtn.place(x=595, y =5)

screenshot = Button(text='Take Notes', command=takeNote, bg='green',fg='white',font= 10)
screenshot.place(x=725, y =5)

window.mainloop()