# Wut?

#### Description:
A CLI application written in python to find word meanings, pronunciation, synonyms, antonyms and other details quickly and easily. The project also allows users to bookmark searched words and also view bookmarked words and it's details as a part of my CS50P final project.

---
## What is it?

***Wut*** is a CLI application written in python and uses the [free  dictionary api](https://dictionaryapi.dev/) to fetch the data and display the search results along with a verbal audio pronunciation.

## Why?

Sometimes while reading some articles or reading documentation or even while chatting with your friends, you might jump across wild words that you have no idea about or you are unsure of. The two options here are either to just ignore that it happened or open up a search engine or a dictionary and search for the word. Here's where ***Wut?*** comes to rescue, saving those few but important clicks, keystrokes and time.  
Since it is a command line application, you just have to enter the word and let the program do it's job, within a second you get the results along with it's pronunciation. And as humans, since we are likely to forget things with time the user can also bookmark the searched word and it's meaning for later review.

## How is it implemented?
***Wut?*** uses the python [requests library](ulink) to make a get request to the [free dictionary API](https://dictionaryapi.dev/) with the given word as command line argument (enforced using [argparser](https://pypi.org/project/argparse/)) to fetch the data. The fetched data is properly formatted and then displayed on the user's terminal window using the [rich library](https://pypi.org/project/rich/) in a neat and colorful manner. *Wut?* uses [English to IPA library](https://pypi.org/project/eng-to-ipa/) to display the phonetics of the searched word. The project makes use of the [Google Text-to-Speech library](https://pypi.org/project/gTTS/) with [play sound](https://pypi.org/project/playsound/) to play the pronunciation of the searched word.  

 *Wut?* also provides the users an option to bookmark the searched word and also to view the bookmarked words by saving the search results to a ```bookmarks.json``` file in user's preferred directory.   

*Wut?* also has error checking to ensure that the user would not jump into a screen full of errors. For ensuring that the ```bookmarks.json``` file is of correct format a ```schema.json``` file is present which validates the bookmarks file using [jsonschema library](https://pypi.org/project/jsonschema/).

A number of tests to test the functions of *Wut?* is present in ```test_project.py``` file to ensure that all cases are handled properly.

---

## How to run *Wut?*
Well it's pretty easy.

Make sure [python](https://www.python.org/), [pip](https://pypi.org/project/pip/) and [git](https://git-scm.com/) is installed by running these commands
```bash
python --version # This should return the installed python version
pip --version # This should return the installed pip version
git --version # This should return the installed git version
```
If not installed, install them from [python.org](python.org/downloads/) and [git-scm](https://git-scm.com/downloads).

Now clone the repository and change directory into Wut
```bash
git clone https://github.com/devadathanmb/wut.git
cd wut
```
Now install the required libraries by running
```bash
pip install -r requirements.txt
```

That's it. You are ready to go.


**Wut has three flags at present.**

1. *For searching for a word*
```bash
python project.py -w <word to be searched>
# Example:
python project.py -w hello
```
2. *For displaying the bookmarked words*
```bash
python project.py -bw <path to bookmarks.json>
# Example:
python project.py -bw /home/me/wut/
```
3. *For displaying the bookmarked word along with it's details*
```bash
python project.py -bm <path to bookmarks.json>
# Example:
python project.py -bm /home/me/wut/
```
4. *And to print the usage and for help*
```bash
python project.py -h
```

---

## Known Issues
Since the application uses [free dictionary api](https://dictionaryapi.dev/) to make the [GET](https://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol#Request_methods) requests, the output is completely dependent on the response from the API. The API is known to be missing several words and also is known to be down at times during heavy traffic (the program displays a *connection error* in such cases).  
In such cases the only option is to try again later or just search for the word on the web.


---
## Future plans
1. The code of the program is currently pretty long and there is definitely scope of refactoring it to a certain extend.
2. Currently users can only bookmark words they cannot remove them. In future a feature to remove bookmarked words can be introduced.
3. ```bookmarks.json``` file can get pretty long if the number of bookmarked words are high. This can be avoided by saving it somewhere on the cloud or using a better format to save bookmarks locally. This feature also can be introduced later.
