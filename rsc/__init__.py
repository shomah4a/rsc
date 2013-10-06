#-*- coding:utf-8 -*-
import os
import sys
import optparse
import tweepy
import urllib
import urllib2
import cookielib
import StringIO
import pickle

from lxml import html


DUMP_FILE = '/tmp/rsc_%s.dump'



def o(*s):

    for i in s:
        print s.encode('utf-8')



def makeparser():

    o = optparse.Option

    optlist = [
        o('--user', dest='user'),
        o('--passwd', dest='passwd'),
        o('--sendto', dest='sendto'),
        o('--consumer-key', dest='consumerKey'),
        o('--consumer-secret', dest='consumerSecret'),
        o('--verifier', dest='verifier'),
        o('--access-key', dest='accessKey'),
        o('--access-secret', dest='accessSecret'),
        ]

    return optparse.OptionParser(option_list=optlist)



class Reservable(object):

    def __init__(self, days, times, name):

        day = int(name[0]) - 1
        time = int(name[1])

        self.day = unicode(days[day])
        self.time = time
        self.start = unicode(times[time-1])


    def make_info(self, time=True):

        if time:
            return u'%s %s時限目(%s)' % (self.day, self.time, self.start)
        return u'%s %s時限目' % (self.day, self.time)



def get_dump_path(userid):

    return DUMP_FILE % userid



def dump_reservable(objects, userid):

    with open(get_dump_path(userid), 'w') as fp:
        pickle.dump(objects, fp)



def load_reservable(userid):

    fpath = get_dump_path(userid)

    if not os.path.exists(fpath):
        return None

    with open(fpath) as fp:
        return pickle.load(fp)



def parse_html(txt):

    txt = txt.decode('sjis')

    fp = StringIO.StringIO(txt)

    el = html.parse(fp)

    tables = el.findall('//table')

    table = tables[1]

    days = [x.find('td').text_content()
           for x in table.findall('./tr')[2:]
           if x.find('td') is not None]

    times = [x.text_content() for x in table.findall('./tr')[1].findall('td')]

    inputs = table.findall('.//input[@src="/images/ko2_kusya.gif"]') + table.findall('.//input[@src="../images/ko2_kusya.gif"]')

    return [Reservable(days, times, x.get('name')) for x in inputs]



def make_opener():

    cj = cookielib.CookieJar()
    cjhdr = urllib2.HTTPCookieProcessor(cj)
    opener = urllib2.build_opener(cjhdr)

    opener.cookiejar = cj

    return opener



def login(opener, usr, passwd):

    url = 'http://125.206.214.67/scripts/mtr0010.asp'

    opener.open(url).read()

    parm = {'mt0010uid':usr,
            'mt0010pwd':passwd,
            'login.x':'100',
            'login.y':'23'}

    return opener.open(url, urllib.urlencode(parm)).read()



def get_reservation_schedule(opener):

    url = 'http://125.206.214.67/scripts/mtr1010.asp'

    parm = {'mtr1010.x':'140',
            'mtr1010.y':'25'}

    return parse_html(opener.open(url, urllib.urlencode(parm)).read())



def logout(opener):

    url = 'http://125.206.214.67/scripts/mtr0020.asp'

    parm = {'logout.x':'38',
            'logout.y':'19'}

    return opener.open(url, urllib.urlencode(parm)).read()




def main(args=sys.argv[1:]):

    opts, args = makeparser().parse_args(args=args)

    auth = tweepy.OAuthHandler(opts.consumerKey, opts.consumerSecret)

    auth.set_access_token(opts.accessKey, opts.accessSecret)
    auth.access_token.set_verifier(opts.verifier)

    api = tweepy.API(auth)

    user = opts.user
    passwd = opts.passwd
    sendto = opts.sendto

    previous = load_reservable(user)

    opener = make_opener()

    login(opener, user, passwd)

    reservables = get_reservation_schedule(opener)

    dump_reservable(reservables, user)

    logout(opener)

    if previous is None:
        previous = set()

    prevs = set([x.make_info(False) for x in previous])
    now = set([x.make_info(False) for x in reservables])

    diff = now - prevs
    removed = prevs - now


    print u'now', ', '.join(sorted(now))
    print u'prevs', ', '.join(sorted(prevs))

    if diff:
        msg = u'空車枠が追加されました: ' + u', '.join(sorted(diff)[:5])

        print msg

        api.send_direct_message(screen_name=sendto,
                                text=msg)

    if removed:
        msg = u'空車枠が埋まりました: ' + u', '.join(sorted(removed)[:5])

        print msg

        api.send_direct_message(screen_name=sendto,
                                text=msg)

