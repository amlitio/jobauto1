import os
import time
import requests
from bs4 import BeautifulSoup
import cloudscraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def ask_chatbot(question, context):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a job seeker."},
            {"role": "user", "content": question},
            {"role": "assistant", "content": context}
        ]
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)
    response.raise_for_status()
    answer = response.json()["choices"][0]["message"]["content"]
    return answer


def sign_in(driver):
    driver.get("https://secure.indeed.com/account/login")
    input("Please sign in to Indeed in the browser window, then press Enter here to continue...")


def search_indeed(job_titles, locations, resume):
    driver = webdriver.Chrome()
    sign_in(driver)
    scraper = cloudscraper.create_scraper(delay=10, browser={'custom': 'ScraperBot/1.0'})

    for title in job_titles:
        for location in locations:
            url = f"https://www.indeed.com/jobs?q={title.replace(' ', '+')}&l={location.replace(' ', '+')}"
            while True:
                try:
                    req = scraper.get(url)
                    soup = BeautifulSoup(req.content, 'html.parser')
                    job_listings = soup.find_all('div', class_='jobsearch-SerpJobCard')

                    print(f"--- {title} in {location} ---")
                    for listing in job_listings:
                        title_elem = listing.find('a', class_='jobtitle')
                        company_elem = listing.find('span', class_='company')
                        location_elem = listing.find('span', class_='location')
                        link_elem = listing.find('a', class_='jobtitle')

                        if None not in (title_elem, company_elem, location_elem, link_elem):
                            job_title = title_elem.text.strip()
                            company = company_elem.text.strip()
                            location = location_elem.text.strip()
                            link = "https://www.indeed.com" + link_elem['href']

                            print(f"Title: {job_title}")
                            print(f"Company: {company}")
                            print(f"Location: {location}")
                            print(f"Apply here: {link}")
                            print()

                            try:
                                apply_for_job(driver, link, resume)
                            except Exception as e:
                                print(f"Failed to apply for job. Error: {e}")

                    next_page_elem = soup.find('a', {'aria-label': 'Next'})
                    if next_page_elem is None:
                                                break
                    else:
                        url = "https://www.indeed.com" + next_page_elem['href']
                except Exception as e:
                    print(f"Error: {e}")
                    break

def apply_for_job(driver, link, resume):
    driver.get(link)
    time.sleep(2)  # Wait for the page to load

    try:
        apply_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'indeedApplyButtonContainer'))
        )
        apply_button.click()
        time.sleep(2)  # Wait for the apply form to load

        prompts = ["Tell us about your relevant experience:", "What are your key skills?", "Why are you interested in this role?"]
        for prompt in prompts:
            try:
                answer = ask_chatbot(prompt, resume)
                print(f"Q: {prompt}")
                print(f"A: {answer}\n")
                input_field = driver.find_element(By.XPATH, f"//textarea[contains(.,'{prompt}')]")
                input_field.send_keys(answer)
            except Exception as e:
                print(f"Error in answering prompt: {e}")
                continue

        submit_button = driver.find_element(By.XPATH, "//button[contains(.,'Submit application')]")
        submit_button.click()

        print("Application submitted successfully.")
        print()

    except Exception as e:
        print(f"Failed to apply for job. Error: {e}")


#job_titles = ["Software Engineer", "Data Scientist"]
#locations = ["New York", "Remote"]
#resume = "My experience..."  # replace with your resume
#search_indeed(job_titles, locations, resume)
