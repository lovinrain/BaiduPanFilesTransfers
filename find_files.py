import requests, re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from filelock import FileLock

text = (requests.get("https://www.7help.net/40.html").content.decode())
soup = BeautifulSoup(text, 'html.parser')
all_href = soup.find_all('a', href=True)
all_href_links = [a['href'] for a in all_href]
all_check_links = [a for a in all_href_links if '7help' in a and a.endswith('html')]
print(len(all_check_links), sep='\n')


# exit(1)


def check_link(url):
    # print(f'checking {url}')
    retry_total = 5
    retry_cnt = 0
    while retry_cnt < retry_total:
        try:
            html_content = requests.get(url,timeout=60).content.decode()
            soup = BeautifulSoup(html_content, 'html.parser')
            all_hrefs = soup.find_all('a', href=True)
            all_href_links = [a['href'] for a in all_hrefs]
            for i in all_href_links:
                if "pan.baidu.com" in i:
                    with FileLock("output.txt.lock"):
                        with open("output.txt", 'a') as f:
                            f.write(str(i) + '\n')
                            # print(f"wrote {i}")
                        return
            if len(html_content) > 1000:
                print(f"Didn't found for {url} + {len(html_content)}, will not retry")
                return
            else:
                print(f"Didn't found for {url} + {len(html_content)}, will retry")
                retry_cnt += 1
        except Exception as e:
            print(f"Error!!! {url} ", + str(e))
            # print(e)
            retry_cnt = retry_cnt + 1
            print(f"retry : {retry_cnt} for  {url}")
    print(f"after all retries, still failed: {url}")


# print(check_link("https://www.7help.net/27155.html"))

print("start")
with ThreadPoolExecutor(max_workers=10) as executors:
    # check_result = executors.map(check_link, all_check_links)
    executors.map(check_link, all_check_links)
print("end")

# filtered_result = list(filter(lambda x: x is not None, check_result))
# print(len(filtered_result))

# with open("output1.txt", 'w') as f:
#     print(*filtered_result, sep='\n', file=f)
