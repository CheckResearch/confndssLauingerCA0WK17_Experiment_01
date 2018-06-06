import json
import time
import os
import sys
from selenium import webdriver

start_with = int(sys.argv[1])

# File from https://github.com/RetireJS/retire.js/blob/master/repository/jsrepository.json
with open('../data/jsrepository.json') as f:
    retirejs_json = json.load(f)

libraries = {}
for lib, data in retirejs_json.items():
    if lib not in ['retire-example', 'dont check']:
        if 'func' in data['extractors']:
            libraries[lib] = ['return ' + x for x in data['extractors']['func']]
        else:
            libraries[lib] = []

# Add additonal extractors
libraries['jquery-migrate'].append('return jQuery.migrateVersion')
libraries['swfobject'].append('var version = (window.swfobject) ? "2" : (window.SWFObject) ? "1" : false;if(version === "2"){if(swfobject.switchOffAutoHideShow){version = "2.2";} else if(swfobject.removeSWF){version = "2.1";}else{version = "2.0";}}return version;')  # Source: http://learnswfobject.com/advanced-topics/detecting-swfobject-version/index.html
libraries['flowplayer'].append('return flowplayer.version')

urls = []

outfile = open('../data/crawler_result.csv', 'w')
logfile = open('../data/crawler_result.log', 'w')
timeoutfile = open('../data/crawler_result_timeout.log', 'w')
with open('../data/list.txt') as f:
    for line in f:
        host = line[:-1]
        urls.append([host, 'http://' + host])

def trycatch(query):
    return 'try { ' + query + ' } catch {return null}'

def create_driver():
    options = webdriver.ChromeOptions()
    #options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    options.binary_location = '/usr/bin/google-chrome'
    options.add_argument('headless')
    options.add_argument('incognito')
    options.add_argument('window-size=1200x800')

    driver = webdriver.Chrome(chrome_options=options)
    driver.set_page_load_timeout(45)
    return driver


def log_to_file(string):
    print(string)
    logfile.write(str(string))
    logfile.write("\n")
    logfile.flush()

driver = create_driver()
i = 1
timeouts = 0
start_time = time.time()
for host, url in urls:
    if start_with > 0:
        start_with -= 1
        i += 1
        continue
    log_to_file('Loading %d/%d (%.2f%%) - %s' % (i, len(urls), 100.0 * i/len(urls), url))
    try:
        driver.delete_all_cookies()
        driver.get(url)
        
        time.sleep(.5)
        for lib, queries in libraries.items():
            for query in queries:
                result = driver.execute_script(trycatch(query))
                if result:
                    outline = '%s;%s;%s' % (host, lib, result)
                    log_to_file(outline)
                    outfile.write(outline + "\n")
                    outfile.flush()
                    break
    except Exception as e:
        log_to_file(type(e))
        log_to_file(e)
        try_close = True
        while True:
            try:
                if try_close:
                    try_close = False
                    driver.close()  # Sometimes the driver cannot be closed
                os.system('killall "chromedriver" 2>/dev/null')
                #os.system('killall "Google Chrome" 2>/dev/null')
                os.system('killall "google-chrome" 2>/dev/null')
                os.system('killall "chrome" 2>/dev/null')
                time.sleep(1)
                driver = create_driver()
                break
            except Exception as e:
                log_to_file(type(e))
                log_to_file(e)
                time.sleep(3)
        timeouts += 1
        timeoutfile.write(host + "\n")
        timeoutfile.flush()
    i += 1
time_needed = time.time() - start_time

timeoutfile.close()
outfile.close()
driver.close()
os.system('killall "chromedriver" 2>/dev/null')
#os.system('killall "Google Chrome" 2>/dev/null')
os.system('killall "google-chrome" 2>/dev/null')
os.system('killall "chrome" 2>/dev/null')

if timeouts != 0:
    log_to_file('%d/%d (%.2f%%) did time out!' % (timeouts, len(urls), 100.0 * timeouts/len(urls)))
log_to_file('%.2fs needed, that is an average of %.2fs per website!' % (time_needed, time_needed/len(urls)))
log_to_file('Finished crawling!')

logfile.close()
