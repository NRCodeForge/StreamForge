from selenium import webdriver
from os import system, name
import chromedriver_binary
from time import time, strftime, gmtime, sleep
import pyfiglet, os, threading
import chromedriver_autoinstaller

# Check if the current version of chromedriver exists and, if it doesn't exist, download it automatically
chromedriver_autoinstaller.install()


def clear_terminal():
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')


clear_terminal()
system('title TikTok Engagement Bot')

print(pyfiglet.figlet_format("TikTok Bot", font="slant"))
print("=" * 50)
print("Welcome to TikTok Engagement Bot!")
print("=" * 50)
print("1. Increase Video Views")
print("2. Increase Video Likes")
print("3. Increase Followers")
print("4. Increase Video Shares")
print("5. View Credits")
print("\nNote: Please paste the TikTok URL when prompted.\n")

try:
    mode = int(input("Enter your choice (1-5): "))
    if not 1 <= mode <= 5:
        raise ValueError
except ValueError:
    print("Please enter a valid number between 1 and 5!")
    exit(1)

if mode == 5:
    print("\nTikTok Engagement Bot")
    print("Created by: vdutts7")
    print("GitHub: https://github.com/vdutts7/tiktok-bot")
    exit(0)

if 1 <= mode <= 4:
    url = input("URL: ")

    start = time()
    time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1024, 650)

    metric1 = 0
    metric2 = 10
    metric3 = 100


def beautify(arg):
    return format(arg, ',d').replace(',', '.')


def update_title1():  # Update the title for video views
    global metric1

    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        system(f'title TikTok Bot ^| Views Generated: {beautify(metric1)} ^| Elapsed Time: {time_elapsed}')


def update_title2():  # Update the title for video likes
    global metric2

    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        system(f'title TikTok Bot ^| Likes Generated: {beautify(metric2)} ^| Elapsed Time: {time_elapsed}')


def update_title3():  # Update the title for followers
    global metric3

    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        system(f'title TikTok Bot ^| Followers Generated: {beautify(metric3)} ^| Elapsed Time: {time_elapsed}')


def update_title4():  # Update the title for shares
    global metric3

    while True:
        time_elapsed = strftime('%H:%M:%S', gmtime(time() - start))
        system(f'title TikTok Bot ^| Shares Generated: {beautify(metric3)} ^| Elapsed Time: {time_elapsed}')