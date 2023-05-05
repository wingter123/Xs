import requests
from bs4 import BeautifulSoup
import time
import pymysql.cursors

# MySQL 数据库连接信息
MYSQL_HOST = '192.168.192.6'
MYSQL_PORT = 3306
MYSQL_USER = 'sisxs'
MYSQL_PASSWORD = 'e6KNen8iXDJw3kxK'
MYSQL_DB = 'sisxs'
MYSQL_CHARSET = 'utf8'

# 连接 MySQL 数据库
connection = pymysql.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    charset=MYSQL_CHARSET
)

# 创建数据库和表
with connection.cursor() as cursor:
    # 创建数据库
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB}")
    # 切换到指定数据库
    cursor.execute(f"USE {MYSQL_DB}")
    # 创建数据表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `posts` (
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `title` varchar(255) NOT NULL,
          `url` varchar(255) NOT NULL,
          `content` LONGTEXT NOT NULL,
          PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
    """)

base_url = 'http://sis001.com/forum/forum-83-{}.html'
url1 = 'http://sis001.com/forum/'
base_content_url = 'http://sis001.com/forum/{}-{}-{}.html'

page_num = 1  # 当前页面的页码

while True:
    url = base_url.format(page_num)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # 获取所有帖子的标签
    threads = soup.find_all('tbody', id=lambda x: x and x.startswith('normalthread'))

    # 遍历所有帖子，依次提取标题和链接信息
    for thread in threads:
        title_link = thread.find('span', id=lambda x: x and x.startswith('thread_'))
        title_name = title_link.text.strip()
        title_url = title_link.a['href']
        title_url = url1 + title_url

        print('文章标题:', title_name)
        print('文章链接:', title_url)

        # 获取文章内容
        response = requests.get(title_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        content_elements = soup.find_all('div', class_='t_msgfont')

        # 遍历所有的 t_msgfont 元素，提取文本内容
        content_list = []
        for content_element in content_elements:
            content = content_element.text.strip()
            content_list.append(content)

        # 获取文章的总页数
        page_nums = soup.find('div', class_='pages')
        if page_nums:
            last_page_num = page_nums.find_all('a')[-2].text.strip()
            print('文章总页数:', last_page_num)

            # 遍历文章的所有页，提取文本内容
            for page in range(2, int(last_page_num) + 1):
                page_url = title_url.replace('-1-', '-{}-').format(page)
                response = requests.get(page_url)
                soup = BeautifulSoup(response.content, 'html.parser')
                content_elements = soup.find_all('div', class_='t_msgfont')
                for content_element in content_elements:
                    content = content_element.text.strip()
                    content_list.append(content)
                print('当前地址:', page_url)

        # 将文章标题、链接和内容插入 MySQL 数据库
        with connection.cursor() as cursor:
            sql = "INSERT INTO `posts` (`title`, `url`, `content`) VALUES (%s, %s, %s)"
            cursor.execute(sql, (title_name, title_url, '\n'.join(content_list)))
            connection.commit()

        time.sleep(5)

    # 处理完当前页面的信息，将 page_num 加1，爬取下一页
    page_num += 1

# 关闭 MySQL 数据库连接
connection

