#! /usr/bin/python3

import sys
import os

working_dir = '/1home/pi/wb_update/'

print(os.path.split(os.path.realpath(__file__))[0]+'/')

class garment:
    def __init__(self, article):
        url_article = 'http://www.wildberries.ru/catalog/{0}/detail.aspx'

        self.article = article
        self.old_price = 0
        self.new_price = 0
        self.description = 'NO_DESCRIPTION'
        self.link = url_article.format(article)
        self.pictures = []

def send_email(msg):
    import smtplib
    from email.mime.text import MIMEText
    addr_to = 'katherpi@mail.ru'
    addr_from = 'wildberries_price_update@ro.ru'

    msg = MIMEText(msg.encode('cp866', 'ignore'))
    msg['To'] = addr_to
    msg['From'] = addr_from
    msg['Subject'] = 'Wildberries update message'

    server = smtplib.SMTP('smtp.rambler.ru', 587)
    server.login(addr_from, "myfirstpython7")
    server.sendmail(addr_from, addr_to, msg.as_string())
    server.quit()


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

    msg_new_in_stock = str()
    msg_old_in_stock = str()
    msg_out_of_stock = str()

    msg_404 = str()

    count_new_in_stock = 1
    count_old_in_stock = 1
    count_out_of_stock = 1

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
            msg_404 += "{0} \n".format(new_garment.link)
            print('{0} IS INACCESSIBLE!'.format(new_garment.link))
            continue
        else:
            print('{0} {1}...'.format(article, new_garment.link))

        if new:
            if in_stock:
                msg_new_in_stock += '\t{0}. {1.description}; цена - {1.new_price} RUR. Ссылка: {1.link}\n\n'.format(str(count_new_in_stock), new_garment)
                count_new_in_stock += 1
            else:
                msg_out_of_stock += '\t{0}. {1.description}; ТОВАР РАСПРОДАН. Ссылка: {1.link}\n\n'.format(str(count_out_of_stock), new_garment)
                count_out_of_stock += 1
        else:
            if in_stock:
                diff = new_garment.new_price - new_garment.old_price
                sign = '+' if diff > 0 else ''
                if diff != 0:
                    msg_old_in_stock += '\t{0}. {1.description}; старая цена = {1.old_price} RUR, новая цена = {1.new_price} RUR, разница = {2:+} RUR. Ссылка: {1.link}\n\n'.format( \
                                                                        str(count_old_in_stock), new_garment,  diff)
                    count_old_in_stock += 1
            else:
                if new_garment.old_price != 0 and new_garment.new_price == 0:
                    msg_out_of_stock += '\t{0}. {1.description}; ТОВАР РАСПРОДАН. Ссылка: {1.link}\n\n'.format(str(count_out_of_stock), new_garment)
                    count_out_of_stock += 1

        if not in_stock:
            print('OUT OF STOCK')

        new_file += '{0.article} {0.new_price} {0.description} {0.link}\n'.format(new_garment)

    count_all = count_out_of_stock + count_old_in_stock + count_new_in_stock

    msg = 'WILDBERRIES.RU PRICE UPDATE \n\n\n\n\n\n'
    if count_new_in_stock > 1:
        msg += 'Новые добавленные: \n\n{0}'.format(msg_new_in_stock)
    if count_old_in_stock > 1:
        msg += '\n\nТовары с изменившимися ценами: \n\n{0}'.format(msg_old_in_stock)
    if count_out_of_stock > 1:
        msg += '\n\nТовары, отсутствующие в продаже: \n\n{0}'.format(msg_out_of_stock)

    file.close()

    if count_all > 3:
        send_email(msg)

    file = open(filename, 'w', encoding='utf_8')
    print(new_file, file=file)
    file.close()

    return msg_404


def main():
    err_msg = str()

    try:
        file = open(working_dir + 'wb_log.dat', 'w', encoding='utf_8')

        import time
        print('{0}, PROCESS STARTED\n'.format(str(time.ctime())), file=file)

        msg1 = main_process()

        if msg1:
            err_msg += 'Следующие ссылки были недоступны:\n{0}\n'.format(msg1)

    except Exception as exc:
        err_msg += "EXCEPTION:\n{0}\n".format(exc)
        raise
    finally:
        if err_msg:
            print(err_msg, file=file)

        print('\nPROCESS ENDED', file=file)
        file.close()


main()
