#! /usr/bin/python3

import sys
import os
working_dir = sys.path[0] + os.sep

from sys import argv
all_garments_in_msg = len(argv) > 1 and argv[1] == '--all'

width_of_td = 200

class garment:
    def __init__(self, article):
        url_article = 'http://www.wildberries.ru/catalog/{0}/detail.aspx'

        self.article = article
        self.old_price = 0
        self.new_price = 0
        self.description = 'NO_DESCRIPTION'
        self.link = url_article.format(article)
        self.pictures = []

def send_email(html):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    addr_to = 'katherpi@mail.ru'
    addr_from = 'wildberries_price_update@ro.ru'

    msg_mm = MIMEMultipart('alternative')
    msg_mm['To'] = addr_to
    msg_mm['From'] = addr_from
    msg_mm['Subject'] = 'WB update message'

    msg = MIMEText(html, 'html', 'utf_8')
    msg_mm.attach(msg)

    server = smtplib.SMTP('smtp.rambler.ru', 587)
    server.login(addr_from, "myfirstpython7")
    server.sendmail(addr_from, addr_to, msg_mm.as_string())
    server.quit()

def make_table(lst):
    num_colomns_tr = 4

    lst2 = ['<td width="{0}">'.format(width_of_td) + x + '</td>' for x in lst]
    table = str()

    for i in range(0, len(lst2), num_colomns_tr):
        new_tr = ''.join(lst2[:num_colomns_tr])
        table += '<tr>' + new_tr + '</tr>'
        lst2 = lst2[num_colomns_tr+1:]

    ost = ''.join(lst2)
    if ost : table += '<tr>' + ost + '</tr>'

    return '<table>' + table + '</table>'

def get_price(garment):
    from bs4 import BeautifulSoup
    from urllib.request import urlopen

    # парсинг, пробуем три раза, в случае если сайт не открывается
    for i in range(3):
        try:
            html_doc = urlopen(garment.link).read()
        except Exception:
            if i == 2:
                return None
        else:
            break

    soup = BeautifulSoup(html_doc)

    find_price = soup.find_all(attrs={'itemprop':'price'})

    if find_price:
        # товар в наличии

        # определение новой цены
        new_price_str = str(find_price[0].contents[0]).replace('\xa0', '').strip().partition(' ')[0]
        garment.new_price = int(new_price_str)

        garment.description = str(soup.find_all(name='h3', attrs={'itemprop':'name'})[0].contents[0]).strip(' \n\t\r')

        pic = soup.find_all(name = 'img', attrs={'id':'preview-large', 'itemprop':'image'})[0]['src']
        if pic: garment.pictures.append(pic)

        return True

    else:
        # товара в наличии нет

        return False


# во входном файле - либо строка с одним числом - артикулом (это только что добавленный товар, за котором не было слежки),
# либо строка в виде:
# ARTICLE OLD_PRICE DESCRIPTION LINK
# где ARTICLE - артикул
#     OLD_PRICE - цена, которая была на прошлой проверке
#     DESCRIPTION - краткое описание товара
#     LINK - ссылка
def main_process():
    filename = working_dir + 'closing_wb.dat'

    msg_new_in_stock = []
    msg_old_in_stock = []
    msg_out_of_stock = str()
    msg_not_changed = []

    msg_404 = str()

    count_new_in_stock = 1
    count_old_in_stock = 1
    count_out_of_stock = 1
    count_not_changed = 1

    new_file = str()

    file = open(filename, encoding='utf_8')

    for line in file:
        line = line.strip()
        if not line:
            continue

        [article, sep, another] = line.partition(' ')
        article = article.strip()
        another = another.strip()

        article = article
        new_garment = garment(article)

        if another:
            # товар уже отслеживался
            new = False
            # определение старой цены
            [price_str, sep, another] = another.partition(' ')
            price_str = price_str.strip()
            new_garment.old_price = int(price_str)

            # определение описания
            [descr, sep, link] = another.rpartition(' ')
            new_garment.description = descr.strip()

        else:
            # новый товар
            new = True

        in_stock = get_price(new_garment)

        if in_stock == None:
            # сайт не открылся, недоступен
            msg_404 += "{0} \n".format(new_garment.link)
            print('{0} IS INACCESSIBLE!'.format(new_garment.link))
            continue
        else:
            print('{0} {1}...'.format(article, new_garment.link))

        if new:
            if in_stock:
                msg_new_in_stock.append('{0}.<a href="{1.link}">{1.description}</a>; цена - {1.new_price} RUR.<br> <img src="{1.pictures[0]}" width="{2}">'.format(str(count_new_in_stock), new_garment, width_of_td))
                count_new_in_stock += 1
            else:
                msg_out_of_stock += '{0}. <a href="{1.link}">{1.description}</a>; ТОВАР РАСПРОДАН.<br>'.format(str(count_out_of_stock), new_garment)
                count_out_of_stock += 1
        else:
            if in_stock:
                diff = new_garment.new_price - new_garment.old_price
                if diff != 0:
                    msg_old_in_stock.append('{0}. <a href="{1.link}">{1.description}</a>; старая цена = {1.old_price} RUR, новая цена = {1.new_price} RUR, разница = {2:+} RUR.<br> <img src="{1.pictures[0]}" width="{3}">'.format( \
                                                                        str(count_old_in_stock), new_garment,  diff, width_of_td))
                    count_old_in_stock += 1
                elif all_garments_in_msg:
                    msg_not_changed.append('{0}. <a href="{1.link}">{1.description}</a>; цена - {1.new_price} RUR. <br><br> <img src="{1.pictures[0]}" width="{2}">'.format(str(count_not_changed), new_garment, width_of_td))
                    count_not_changed += 1

            else:
                if all_garments_in_msg:
                    msg_out_of_stock += '{0}. <a href="{1.link}">{1.description}</a>;'.format(str(count_out_of_stock), new_garment)
                    count_out_of_stock += 1
                elif new_garment.old_price != 0 and new_garment.new_price == 0:
                    msg_out_of_stock += '{0}. <a href="{1.link}">{1.description}</a>; ТОВАР РАСПРОДАН.<br>'.format(str(count_out_of_stock), new_garment)
                    count_out_of_stock += 1


        if not in_stock:
            print('OUT OF STOCK')

        new_file += '{0.article} {0.new_price} {0.description} {0.link}\n'.format(new_garment)

    file.close()

    msg = '<html><head>WILDBERRIES.RU PRICE UPDATE</head> <body><br><br><br><br>'
    msg += ('Новые добавленные: <br><br>{0}'.format(make_table(msg_new_in_stock)) if msg_new_in_stock else '')
    msg += ('<br><br>Товары с изменившимися ценами: <br><br>{0}'.format(make_table(msg_old_in_stock)) if msg_old_in_stock else '')
    msg += ('<br><br>Товары, отсутствующие в продаже: <br><br>{0}'.format(msg_out_of_stock) if msg_out_of_stock else '')
    msg += ('<br><br>Товары с неизменившимися ценами: <br><br>{0}'.format(make_table(msg_not_changed)) if msg_not_changed else '')
    msg += '</body></html>'

    if any((msg_new_in_stock, msg_old_in_stock, msg_out_of_stock, msg_not_changed)):
        send_email(msg)

    file = open(filename, 'w', encoding='utf_8')
    print(new_file, file=file)
    file.close()

    return msg_404


def main():
    from io import StringIO
    import time

    log = StringIO()
    print('{0}, PROCESS STARTED\n'.format(str(time.ctime())), file=log)

    try:
        msg1 = main_process()

        if msg1:
            print('Следующие ссылки были недоступны:\n{0}\n'.format(msg1), file=log)

    except Exception as exc:
        print("EXCEPTION:\n{0}\n".format(exc), file=log)
        raise
    finally:
        print('\nPROCESS ENDED', file=log)

        file = open(working_dir + 'wb_log.dat', 'w', encoding='utf_8')
        print(log.getvalue(), file=file)
        file.close()


main()
