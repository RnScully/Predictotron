'''a script which scrapes a user's reviews given user ID number, a simple int from 1 to over 100m, each a unique goodreads user ID'''

import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import selenium.common.exceptions as seleniumerrors

import numpy as np

import time
import json

from pymongo import MongoClient




#hacky way to easily edit the range to operate over in nano on the ec2
#start, stop = 4667023, 4667025


def click_in_margin():
    '''gets rid of an annoying pop-up that asks you to log in whenever you load a page'''
    actions.move_by_offset(25,150).click().perform()
    actions.move_by_offset(-25,-150).perform()


def scroll_to_bottom(scroll_wait):
    '''a function which rolls through a page to force the lazy loader to load everything'''
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        time.sleep(scroll_wait) #wait for page to load
        
        last_height = new_height

def scoop_reviews():
    '''
    a function to take the page of reviews and turn it into jsons

    Attributes:
    None

    Returns:
    jsons: list of jsons
    
    '''
    # pull all class objects called 'bookalike review' into a list 
    try:
        reviews = driver.find_elements_by_class_name("friendReviews")
    except:
        print ('that book had no reviews')
        pass
    #turn the bookalikes into json lists
    for elements in reviews:
        print(elements) #hash this out, testing
    jsons = [items.get_attribute('outerHTML') for items in reviews]
        
    return jsons

def each_page():
    '''
    helper function that will go to the next page in the reviews page.
    
    Attributes:
    None
    
    Returns:
    dicontary: book_id : list of reviews
    '''
    while True:
        docs = []
        new_doc =scoop_reviews()
        docs =[i for i in new_doc]
        
        try:
            elm = driver.find_element_by_class_name('next_page')
        except seleniumerrors.NoSuchElementException:
            return docs # stops looking and returns docs if this book doesn't have more pages. 
            
        if 'disabled' in elm.get_attribute('class'):
            print('I got to the end of these pages!')
            break
        print('going to next page!')
        elm.click()

        return {book_id : docs}


def log_current_sample():
    '''
    a simple helperfunction that keeps track of where in the sampling order we are
    ++++++++++
    Attributes
    None    
    ++++++++++
    Returns
    None    
    '''
    with open('progress.txt', 'w')as f:
        f.write(str(current_index))

def import_samples():
    '''
    takes the list of samples and turns them into a workable list
    ++++++++++
    Attributes
    None
    ++++++++++
    Returns
    the list of sample goodreads user ids generated by random sampling
    '''

    samples = np.loadtxt('samples.txt')
    return [int(items) for items in samples]

def get_next_page(book_id):
    '''moves to the next page according to the samples
    ++++++++++
    Attributes
    
    ++++++++++
    Returns
    book_id: (int) the userid from samples
        
    '''
    
    ratings_url = 'https://www.goodreads.com/review/list/{}?sort=rating&view=reviews'.format(book_id)
    print('trying to load '+ratings_url)
    driver.get(ratings_url)
    

def get_last_index():
    '''
    checks our progress for system restarts
    ++++++++++
    Attributes
    None
    ++++++++++
    Returns
    the index of the most recent sample pulled from goodreads
    '''

    return samples.index(int(np.loadtxt('progress.txt'))) 

def save_to_mongo(review_dict):

    #connect to the mongo thing
    client = MongoClient()
    db = client['reviews']
    gr_collection = db['book_reviews']
    gr_collection.insert_one(review_dict)
    #add doc to mongodb
    #disconnect from mongo(do this over and over, don't keep mongo open, hopefully saves ram!?)
    client.close()

if __name__ == "__main__":
    #create an option to run the script without a window (headless mode)
    option = webdriver.FirefoxOptions()
    option.add_argument('-headless')
    print("Hello, I'm just getting everything together")
    driver =  webdriver.Firefox(options=option)
    actions = ActionChains(driver)




    first_page = True
    print('checking on the samples!')
    samples = import_samples()
    current_index = get_last_index()
    print('everything seems to be in order.')
         
    
    for book_id in samples[current_index:-1]:
        print("**stretches**")
#         current_index = samples.pop()
        log_current_sample()
        get_next_page(book_id)

        if (str(book_id)in driver.current_url) != True:
                print("Uhhh....I'm a little confused, but somehow I ended up at {}".format(driver.current_url))
                continue
        print('loading '+book_review_url)

        if first_page == True:
                click_in_margin()
                first_page = False

        print('scrolling down')
        #scroll_to_bottom(1.5)  # let the website load for 1.5 secs...ugh
        print('scooping reveiws')
        review_dict = each_page()
        save_to_mongo(review_dict)
        #add doc to mongodb
        print('book {} done, now sleeping'.format(book_id))
        time.sleep(3) #sleep of 4 felt too long. see if 3 gets you kicked. 
    #end loop

    driver.close()

