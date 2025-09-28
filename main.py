import os
import sys
import time
import json
import random
import pandas as pd
from PIL import Image
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from image_tools import *
from csv_tools import *
from llm_tools import *
from creds import *

RPT = int(sys.argv[1])

llm = ChatOllama(model="gemma3:4b", temperature=0.01, num_ctx=4096)
json_generation_chain = prompt_func | llm | StrOutputParser()
json_translation_chain = prompt_func | llm | StrOutputParser()

repeat_count = 0
while repeat_count != RPT:
    try:
        df = pd.read_csv(METABASE_CSV)
        random_index = random.choice(df.index.tolist())
        task_link = df.loc[random_index, 'task_link']
        taiga_link = str(task_link)
        task_user_story = df.loc[random_index, 'user_story']
        taiga_user_story = str(task_user_story)
        taiga_title = ""
        taiga_article = ""
        taiga_comments = ""
        downloaded_images = []
        #os.environ["MOZ_HEADLESS"] = "1" ### Comment if you want to run with GUI
        options = Options()
        options.page_load_strategy = 'eager'
        driver = webdriver.Firefox(options=options)
        driver.get("https://taiga.javan.id/login") ### Taiga login and assertion
        time.sleep(10)
        driver.find_element(By.NAME, "username").send_keys(TAIGA_EMAIL)
        driver.find_element(By.NAME, "password").send_keys(TAIGA_PWD)
        driver.find_element(By.CSS_SELECTOR, ".full").click()
        time.sleep(5)
        driver.get(taiga_link)
        time.sleep(10)
        try:
            elements = driver.find_elements(By.XPATH, "//span[contains(.,\'tc_done\')]")
            assert len(elements) == 0
            elements = driver.find_elements(By.XPATH, "//span[contains(.,\'no_tc\')]")
            assert len(elements) == 0
            #Scrape title
            taiga_title = driver.find_element(By.CSS_SELECTOR, ".detail-subject").text
            taiga_title_raw = taiga_title
            taiga_title = ("title = " + str(taiga_title) + "\n")
            
            #Scrape main article
            description = scrape_element_with_images_with_css(driver, MAIN,".html-read-mode > .wysiwyg")
            taiga_article= ("main article = " + str(json.dumps(description, indent=2)) + "\n")
            
            # Download images from main article
            download_images_from_result(downloaded_images, description, MAIN)

            #Scrape comments
            comment_idx = 1
            while True:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, (".comment:nth-child(" + str(comment_idx) + ") .comment-text"))
                    assert len(elements) > 0
                    curr_comment = scrape_element_with_images_with_css(driver, COMMENT,(".comment:nth-child("+str(comment_idx)+") .comment-text"), idx=("_"+str(comment_idx-1)))
                    ("comment #" + str(comment_idx) + " = " + str(json.dumps(curr_comment, indent=2)) + "\n")
                    
                    # Download images from comment
                    download_images_from_result(downloaded_images, curr_comment, COMMENT, idx=("_"+str(comment_idx-1)))
                    
                    comment_idx += 1
                except:
                    break

            try:
                folder_path = os.getcwd()
                image_files = list_png_files(folder_path)
                image_files_converted = []
                for img in image_files:
                    pil_image = Image.open(folder_path+"/"+img)
                    image_b64 = convert_to_base64(pil_image)
                    image_files_converted.append(image_b64)

                json_from_llm = json_generation_chain.invoke({"text": prompt_generator((taiga_title + taiga_article + taiga_comments)), "images": image_files_converted})
                json_from_llm = json_translation_chain.invoke({"text": translator(json_from_llm), "images": []})

                result = json.loads(remove_wrapper_regex(json_from_llm))
                print(remove_wrapper_regex(json_from_llm))

                assert result["module"] != None
                assert result["type"] != None
                assert result["priority"] != None
                assert result["title"] != None
                assert result["tag"] != None
                assert result["description"] != None
                assert result["precondition"] != None
                assert result["num_of_steps"] != None
                assert result["steps"] != None
                assert result["step_results"] != None

                assert len(result["steps"]) == len(result["step_results"])
                
                cleanup_downloaded_images(downloaded_images)
                try:
                    driver.get("https://qa.javan.id/project/9dc4b5b0-a4d8-41f6-8fc2-4cfe242e553b/test-case") ### Internal QA tool login and assertion
                    time.sleep(5)
                    driver.find_element(By.ID, "username").send_keys(QATOOLS_EMAIL)
                    driver.find_element(By.ID, "password").send_keys(QATOOLS_PWD)
                    driver.find_element(By.ID, "kc-login").click()
                    time.sleep(5)
                    driver.find_element(By.XPATH, "//span[contains(.,\'Add Test Case\')]").click()
                    time.sleep(3)

                    driver.find_element(By.CSS_SELECTOR, ".flex-auto").click() ### Module selection
                    if result["module"] == "App":
                        driver.find_element(By.CSS_SELECTOR, ".p-1:nth-child(5) span").click()
                    elif result["module"] == "Studio":
                        driver.find_element(By.CSS_SELECTOR, ".p-1:nth-child(4) span").click()
                    elif result["module"] == "Website":
                        driver.find_element(By.CSS_SELECTOR, ".p-1:nth-child(3) span").click()                    

                    driver.find_element(By.ID, "react-select-2-input").send_keys(str(result["type"])) ### Type selection
                    driver.find_element(By.ID, "react-select-2-input").send_keys(Keys.ENTER)

                    driver.find_element(By.ID, "react-select-3-placeholder").click() ### Priority selection
                    if result["priority"] == "Low":
                        driver.find_element(By.ID, "react-select-3-option-0").click()
                    elif result["priority"] == "Medium":
                        driver.find_element(By.ID, "react-select-3-option-1").click()
                    elif result["priority"] == "High":
                        driver.find_element(By.ID, "react-select-3-option-2").click()
                    elif result["priority"] == "Critical":
                        driver.find_element(By.ID, "react-select-3-option-3").click()

                    driver.find_element(By.ID, "react-select-4-placeholder").click() #### Tag selection
                    if result["tag"] == "Positve":
                        driver.find_element(By.ID, "react-select-4-option-0").click()
                    elif result["tag"] == "Negative":
                        driver.find_element(By.ID, "react-select-4-option-1").click()
                    else: 
                        driver.find_element(By.ID, "react-select-4-option-0").click()

                    driver.find_element(By.ID, "title").send_keys(taiga_title_raw) ### Title

                    driver.find_element(By.ID, "description").send_keys(result["description"]) ### Description

                    driver.find_element(By.ID, "precondition").send_keys(result["precondition"]) ### Precondition

                    driver.find_element(By.XPATH, "//button[contains(.,\'Step\')]").click() ### Switch to steps tab

                    test_tabs_idx = 0
                    while test_tabs_idx != len(result["steps"]):
                        driver.find_element(By.ID, "steps."+str(test_tabs_idx)+".title").send_keys(result["steps"][test_tabs_idx]) 
                        driver.find_element(By.ID, "steps."+str(test_tabs_idx)+".expected_result").send_keys(result["step_results"][test_tabs_idx])
                        if test_tabs_idx + 1 != len(result["steps"]):
                            driver.find_element(By.XPATH, "(//button[@type=\'button\'])["+str(4 + (test_tabs_idx * 2))+"]").click() 

                        test_tabs_idx += 1

                    driver.find_element(By.XPATH, "//button[contains(.,\'Create\')]").click()
                    time.sleep(5)
                    driver.get("https://qa.javan.id/project/9dc4b5b0-a4d8-41f6-8fc2-4cfe242e553b/test-case")
                    time.sleep(5)
                    driver.find_element(By.XPATH, "//span[contains(.,\'All Epic\')]").click()
                    time.sleep(3)
                    driver.find_element(By.XPATH, "//th[contains(.,\'Case Code\')]").click()
                    time.sleep(3)
                    driver.find_element(By.XPATH, "/html/body/div/div[1]/div[2]/main/div/section/div/div[2]/div/div[2]/div/div[3]/table/tbody/tr[1]/td[5]/div/a[2]").click()
                    time.sleep(5)
                    curr_qatools_url = driver.current_url
                    

                    driver.get(taiga_link)
                    time.sleep(5)
                    driver.find_element(By.CSS_SELECTOR, ".add-tag-text").click()
                    time.sleep(3)
                    driver.find_element(By.CSS_SELECTOR, ".tag-input").send_keys("tc_done")
                    time.sleep(3)
                    driver.find_element(By.CSS_SELECTOR, ".save").click()
                    time.sleep(3)
                    driver.find_element(By.CSS_SELECTOR, ".detail-header-line > a > span").click()
                    driver.find_element(By.CSS_SELECTOR, ".detail-header-line > a > span").click()
                    time.sleep(5)
                    current_user_story = driver.find_element(By.CSS_SELECTOR, ".detail-subject").text

                    append_to_links(RESULT_CSV, str(current_user_story), str(curr_qatools_url))

                    df = df.drop(random_index)
                    df.to_csv(METABASE_CSV, index=False)
                    print("TAIGA LINK :"+ str(taiga_link))
                    print("USER STORY :" + str(current_user_story))
                    print("QA TOOLS URL :" + str(curr_qatools_url))
                    driver.quit()
                    repeat_count += 1
                except:
                    print("Failed at test case submission.")
                    driver.quit()
                    cleanup_downloaded_images(downloaded_images)
                    pass
            except:
                print("Failed at test case generation.")
                driver.quit()
                cleanup_downloaded_images(downloaded_images)
                pass
        except:
            df = df.drop(random_index)
            df.to_csv(METABASE_CSV, index=False)
            print("Test case already exists. Rerolling..")
            driver.quit()
            cleanup_downloaded_images(downloaded_images)
            pass
    except:
        print("Failed at Tagia scraping.")
        driver.quit()
        cleanup_downloaded_images(downloaded_images)
        pass