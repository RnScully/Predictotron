'''a script which scrapes a user's reviews given user ID number, a simple int from 1 to over 100m, each a unique goodreads user ID'''

import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import selenium.common.exceptions as seleniumerrors
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

ignored_exceptions=(NoSuchElementException,StaleElementReferenceException,)

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
        print(str(elements)[:20]) #hash this out, testing
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
    docs = []
    pages = 0
    while True:
        print('letting this load')
        
        time.sleep(2)
        new_doc =scoop_reviews()
	print(len(new_doc))
        for i in new_doc:
            print(i[:90])
            docs.append(i)
        
        try:
            elm = driver.find_element_by_class_name('next_page')
            print('getting the next ten reviews')
            pages +=1
            elm.click()
        except seleniumerrors.NoSuchElementException:
            print("this book didn't have more than one page of reviews")
            return docs # stops looking and returns docs if this book doesn't have more pages. 
        time.sleep(1)
        

        try:
            elm= driver.find_element_by_class_name('next_page')
            if 'disabled' in elm.get_attribute('class'):
                print('I got to the end of these pages!')
                return docs
        except:
            print('got {} pages of reviews from this book!'.format(pages))

            return docs
        
        print('going to next page!')
        
    print('got {} pages of reviews from this book!'.format(pages))
    return docs


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
        f.write(str(samples[current_index]))

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
    
    ratings_url = 'https://www.goodreads.com/book/show/{}'.format(book_id)
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
    progress = int(np.loadtxt('progress.txt'))
    print ('{} is in the progress log'.format(progress))
    
    return samples.index(progress)

def save_to_mongo(review_lst):
    '''
    Helperfunction that takes a list of reviews, appends them to dictonaries, and feeds them into mongodb
    
    Attributes:
    review_lst (list):reviews
    '''
    #connect to the mongo thing
    client = MongoClient()
    db = client['reviews']
    gr_collection = db['book_reviews']
    
    for item in review_lst:
        print(item[:20])
        mongo_dict = {'book_id':str(book_id), 'reviews' : item}
        gr_collection.insert_one(mongo_dict) 
    #add doc to mongodb
    #disconnect from mongo(do this over and over, don't keep mongo open, hopefully saves ram!?)
    client.close()

if __name__ == "__main__":
    option = webdriver.FirefoxOptions()
    option.add_argument('-headless')
    print("Hello, I'm just getting everything together")
    driver =  webdriver.Firefox(options=option)
    actions = ActionChains(driver)




    first_page = True
    print('checking on the samples!')
    samples = list(np.arange(1,70000000)) # the bookreads books are...bad. 
    current_index = get_last_index()
    print('everything seems to be in order.')
    print(current_index)

    for book_id in samples[int(current_index):-1]:
        print("**stretches**")
        current_index+=1
    #         current_index = samples.pop()
        log_current_sample()
        get_next_page(book_id)
        time.sleep(1)

        if (str(book_id)in driver.current_url) != True:
                
                print(book_id)
                print("Uhhh....I'm a little confused, but somehow I ended up at {}".format(driver.current_url))
                continue
    #         print('loading '+book_review_url)

        if first_page == True:
                click_in_margin()
                first_page = False

        #print('scrolling down')
        #scroll_to_bottom(1.5)  # let the website load for 1.5 secs...ugh
        print('scooping reveiws')
        review_lst = each_page()
	for elements in review_lst:
        	print(str(elements)[:20])
        save_to_mongo(review_lst)
        #add doc to mongodb
        print('book {} done, now sleeping'.format(book_id))
        time.sleep(1) #sleep now exists in the go to the next page step. . 
    #end loop

driver.close()

