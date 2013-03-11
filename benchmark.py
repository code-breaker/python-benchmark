#!/usr/bin/env python
# -*- coding: utf8 -*-
# code by codebreaker
import sys,time
import gevent
from gevent import monkey,Timeout
from urlparse import urlparse
from optparse import OptionParser
from urllib2 import urlopen, URLError, HTTPError

monkey.patch_all()


def get_options():
    usage = "python %prog [options] [http://]hostname[:port]/path"
    parser = OptionParser(usage=usage, version="%prog 1.0")
    parser.add_option("-n", "--requests", dest="requst_num", type = "int",
                       help="Number of requests to perform")
    
    parser.add_option("-c", "--concurrency", dest="concurrency_num", type = "int",
                       help="Number of multiple requests to make")
    parser.add_option("-t", "--timelimit", dest="timelimit", type = "int",default = 0,
                       help="Seconds to max. wait for responses")
    return parser


def make_conn(url,timelimit):
    global SUCCESS_RECORD,FAIL_RECORD,TOTAL_SIZE,REQTIME_ARR
    time_start = time.time()
    
    if timelimit:
        timeout = Timeout(timelimit)
        timeout.start()
    
    try:
        f = urlopen(url)
        if f.getcode() == 200:
            time_end = time.time()
            server_info = f.info()
            content_type = server_info['content-type'].split(";")[0]
            if content_type == "text/html":
                data = f.read()
		size = int(server_info['content-length'])
            else:
                size = int(server_info['content-length'])
            REQTIME_ARR.append((time_end - time_start) * 1000)
            TOTAL_SIZE = TOTAL_SIZE + size
            SUCCESS_RECORD += 1
        else:
            FAIL_RECORD += 1
    except Timeout:
        FAIL_RECORD += 1
        return
    except Exception,e:
        FAIL_RECORD += 1
        return
    finally:
        if timelimit:
            timeout.cancel()


def test_and_get_server_info(url):
    try:
        f = urlopen(url)
        server_info = f.info()
        return server_info
    except HTTPError, e:
        print "HTTP Error:",e.code , url
        OPT.print_help()
        sys.exit()
    except URLError, e:
        print "URL Error:",e.reason , url
        OPT.print_help()
        sys.exit()

def out_msg(hostname,port,server_info,url_path,time_used,request_num,concurrency_num):
    print "Server Software:%s" % server_info['server']
    print "Server Hostname:%s" % hostname
    print "Server Port:%d" % port

    print "Document Path:%s" % url_path
    print "Document Length:%s" % server_info['content-length']

    print "Concurrency Level:%d" % concurrency_num
    print "Time taken for tests:%fseconds" % time_used
    print "Complete requests:%d" % request_num
    print "Failed requests:%d" % FAIL_RECORD
    
    print "Total transferred:%d bytes" % TOTAL_SIZE
    
    # Complete requests/time token
    print "Requests per second:%f [#/sec] (mean)" % (request_num/time_used)
    # time token/(Complete requests/Concurrency Level)
    if request_num%concurrency_num == 0:
        loop_time = request_num/concurrency_num
    else:
        loop_time = (request_num/concurrency_num)+1   
    print "Time per request:%f [ms] (mean)" %  (time_used/loop_time*1000)
    # time token/Complete requests
    print "Time per request:%f [ms] (mean, across all concurrent requests)" % (time_used/request_num*1000)
    # Total transferred/Time taken for tests/1024
    print "Transfer rate: %d [Kbytes/sec] received" %  (TOTAL_SIZE/time_used/1024)

    print "Percentage of the requests served within a certain time (ms)"
    
    REQTIME_ARR.sort()
    reqtime_len = len(REQTIME_ARR)
    
    print "50%% %d" % REQTIME_ARR[(reqtime_len/2)-1]
    print "66%% %d" % REQTIME_ARR[int(reqtime_len*0.66)-1]
    print "75%% %d"  % REQTIME_ARR[int(reqtime_len*0.75)-1]
    print "80%% %d"  % REQTIME_ARR[int(reqtime_len*0.8)-1]
    print "90%% %d"  % REQTIME_ARR[int(reqtime_len*0.9)-1]
    print "100%% %d (longest request)"  % REQTIME_ARR[reqtime_len-1]

def main():
    global OPT,SUCCESS_RECORD,FAIL_RECORD,TOTAL_SIZE,REQTIME_ARR
    SUCCESS_RECORD = 0
    FAIL_RECORD = 0
    TOTAL_SIZE = 0
    REQTIME_ARR=[]
    OPT = get_options()
    (options, args) = OPT.parse_args()
    
    if len(args) == 0:
        OPT.print_help()
        sys.exit()
    
    uri = args[0]
    uri = urlparse(uri)
    url = uri.geturl()
    hostname = uri.netloc
    port = uri.port or 80
    url_path = uri.path or "/"
    
    server_info = test_and_get_server_info(url)
    request_num = options.requst_num
    concurrency_num = options.concurrency_num
    
    timelimit = options.timelimit

    if not request_num or not concurrency_num:
        OPT.print_help()
    
    time_start = time.time()

    for i in xrange(request_num/concurrency_num):
        jobs = []
        for j in xrange(concurrency_num):
            job = gevent.spawn(make_conn, url,timelimit)
            jobs.append(job)
        gevent.joinall(jobs)
    
    # make conn which is out loop if request_num%concurrency_num != 0
    jobs = []
    for i in xrange(request_num%concurrency_num):
        job = gevent.spawn(make_conn, url,timelimit)
        jobs.append(job)
    gevent.joinall(jobs)
    time_end = time.time()
    time_used = time_end - time_start
    # print stat info 
    out_msg(hostname,port,server_info,url_path,time_used,request_num,concurrency_num)



if __name__ == "__main__":  
    main()   
