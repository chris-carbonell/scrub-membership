# basic
import sys
import time
import random
import datetime
import pandas as pd
import os

# string
import string
import itertools

# webscraping
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# subprocess
import subprocess

# config
import config

# output
import csv

# vpn
import vpn_tools as vt

def scrub_manager():
    
    # improvement: randomize movement
    # improvement: read in via yaml and connect yaml to host machine
    # for tuple_combo in itertools.product(string.ascii_letters[:26], repeat=2):
    for str_combo in config.gbl_ls_combo:

        # get driver
        driver = get_driver_chrome()
        time.sleep(3) # give it time to load
        
        try:
            driver.get(gbl_str_website) # start at search form
            load_and_wait(driver)
        except:
            print_log_message('scrub_manager', 'quitting before scrub: ' + str_combo)
            driver.quit() # im guessing im getting a bunch of memory leak errors

        # scrub
        try:
            scrub_results(driver, str_combo, config.gbl_str_filename)
        except:
            print_log_message('scrub_manager', 'failed: ' + str_combo)
            print(sys.exc_info())

        # quit driver
        driver.quit()

    return

def scrub_results(driver, str_search, str_filename):

    print_log_message('scrub_results', 'attempting to scrub: ' + str_search)

    # enter search
    elem = driver.find_element_by_name(config.secrets.gbl_str_id_last_name)
    elem.clear()
    elem.send_keys(str_search)
    elem.send_keys(Keys.RETURN)
    load_and_wait(driver)

    # if too many records returned, recursively iterate over an additional letter
    if config.secrets.gbl_str_too_many_records in driver.page_source:
        print_log_message('scrub_results', 'too many records: ' + str_search)
        for str_letter in string.ascii_letters:
            scrub_results(driver, str_search + str_letter, str_filename)
    else:

        if config.secrets.gbl_str_no_records in driver.page_source:
            print_log_message('scrub_results', 'no results: ' + str_search)
            return
        else:

            # set up output
            file_csv = open(str_filename, 'a', newline='') # append
            csv_writer = csv.writer(file_csv)

            print_log_message('scrub_results', 'scrubbing: ' + str_search)

            # while pages exist to be scrubbed
            # scrub them
            # move to next page in results if necessary
            # dont repeat pages we already scrubbed

            # the firstpage is already selected so the links start at 2
            # first page goes 1 to 10 and ...
            # second page can repeat some if there aren't enough pages

            # scrub first page
            ls_pages_scrubbed = ['1']
            scrub_results_page(csv_writer, driver)

            # identify pages to scrub
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            ls_pages_available = [x.string for x in soup.findAll("a", href=lambda x: x and config.secrets.gbl_str_id_pages in x)] # start with first results page

            # scrub remaining pages
            while len(ls_pages_available) > 0:
                
                str_page = ls_pages_available[0] # eg '3'
                
                if str_page not in ls_pages_scrubbed:
                    
                    # go to next page
                    click_and_wait(driver, driver.find_element_by_link_text(str_page))
                    
                    if str_page == '...':    
                        soup_results_page = BeautifulSoup(driver.page_source, 'html.parser')
                        ls_pages_available = [x.string for x in soup_results_page.findAll("a", href=lambda x: x and config.secrets.gbl_str_id_pages in x)]
                        ls_pages_scrubbed.append('11') # clicking on ... opens page 11 so just like 1, we need to scrub 11 here
                    else:
                        ls_pages_scrubbed.append(str_page)
                    
                    scrub_results_page(csv_writer, driver)

                    ls_pages_available.remove(str_page)
                    
                else:
                    # already scrubbed
                    ls_pages_available.remove(str_page)
    
            # close csv
            file_csv.close()

    return

def get_valid_table_links(soup):
    
    # start return list
    ls_return = []
    
    # get table
    soup_table = soup.find(id=config.secrets.gbl_str_id_table)

    # loop through rows in table
    # skip header and blank bottom row
    for row in soup_table.find_all('tr')[1:-1]:
         # get the text from all the td's from each row
        ls_row = row.find_all('td')
                
        if len(ls_row[2].getText()) > 1:
            ls_return.append(ls_row[0].find('a').getText()) # get link text
        
    return ls_return

def save_screenshot(driver, str_desc):
    driver.save_screenshot("./output/screenshots/" + " ".join([
        datetime.datetime.now().strftime("%Y%m%d %H%M%S"),
        str_desc,
        "screenshot.png"]))
    return

def scrub_results_page(csv_writer, driver):

    # get soup
    soup_results_page = BeautifulSoup(driver.page_source, 'html.parser')
    
    # take screenshot
    save_screenshot(driver, "results")
    
    # loop over links for names
    for str_name in get_valid_table_links(soup_results_page):
        
        # open name link
        try:
            click_and_wait(driver, driver.find_element_by_link_text(str_name))
        except:
            click_and_wait(driver, driver.find_element_by_link_text(str_name.strip())) # eg "Xin, Dan "

        # get soup and save details to csv
        scrub_profile(driver, csv_writer)

        # go back to results
        driver.execute_script("window.history.go(-1)") 
        load_and_wait(driver)

    return

def scrub_profile(driver, csv_writer):

    # get soup
    soup_profile = BeautifulSoup(driver.page_source, 'html.parser')

    # screenshot
    save_screenshot(driver, "profile")
                           
    # save to csv
    
    ls_profile = [
            driver.current_url,
            get_profile_detail(soup_profile, 'span', config.secrets.gbl_str_profile_target_1),
            get_profile_detail(soup_profile, 'span', config.secrets.gbl_str_profile_target_2),
            get_profile_detail(soup_profile, 'span', config.secrets.gbl_str_profile_target_3),
            get_profile_detail(soup_profile, 'a', config.secrets.gbl_str_profile_target_4),
            "\"" + get_profile_detail(soup_profile, 'span', config.secrets.gbl_str_profile_target_5) + "\"",
            get_profile_detail(soup_profile, 'span', config.secrets.gbl_str_profile_target_6).replace("<br/>", ", "),
            get_profile_detail(soup_profile, 'span', config.secrets.gbl_str_profile_target_7).replace("<br/>", ", ")
        ]
    
    csv_writer.writerow(ls_profile)

def get_profile_detail(soup, str_tag, str_endswith):
    
    try:
        str_detail = soup.findAll(str_tag, id=lambda x: x and x.endswith(str_endswith))[0].string
    except:
        str_detail = ''

    str_detail = '' if str_detail is None else str_detail # some details can be missing

    str_detail.encode('unicode_escape') # https://stackoverflow.com/questions/4415259/convert-regular-python-string-to-raw-string

    return str_detail

def get_driver_chrome(bool_headless = True, str_user_agent = None):

    # str_user_agent = r'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'

    # improvement: can we select firefox OR chrome here? i know opts only applies to Chrome so it'd be a big if/then

    # list of verified user agents
    ls_user_agents = config.secrets.gbl_ls_user_agents

    # set up chrome options
    opts = Options()
    
    # sandbox
    opts.add_argument("--no-sandbox")

    # set user agent
    if str_user_agent is not None:
        opts.add_argument("user-agent=" + str_user_agent)
    else:
        opts.add_argument("user-agent=" + random.choice(ls_user_agents))

    # headless
    if bool_headless:
        opts.add_argument("--headless")

    opts.add_argument("--window-size=1920,1080")

    # suppress warning
    # https://stackoverflow.com/questions/47392423/python-selenium-devtools-listening-on-ws-127-0-0-1
    opts.add_experimental_option('excludeSwitches', ['enable-logging'])

    # get chrome driver
    driver = webdriver.Chrome(options=opts, executable_path=config.gbl_str_path_chromedriver)

    return driver

def click_and_wait(driver, link):
    link.click()
    load_and_wait(driver)
    return

def load_and_wait(driver):

    # test text
    str_loaded = ">Terms of Use</a>" # ie if this text exists, then the page must be loaded

    # continue when loaded
    while str_loaded not in driver.page_source:
        time.sleep(1)

    # wait randomly
    time.sleep(10 + random.randint(-5,5))

    return

def print_log_message(str_module, str_message, str_filename = None):
    
    # default to config
    if str_filename is None:
        str_filename = config.gbl_str_path_log
    
    # build message
    ls_log = [datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), vt.get_external_ip(), str_module, str_message]
    
    # save to log
    file_csv = open(str_filename, 'a', newline='') # append
    csv_writer = csv.writer(file_csv)
    csv_writer.writerow(ls_log)
    
    # stdout
    print(", ".join(ls_log))
    
    return

if __name__ == "__main__":
    scrub_manager()