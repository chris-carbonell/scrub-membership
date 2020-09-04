# general
import time
import datetime

# config
import config

# multiprocessing
# https://pymotw.com/2/multiprocessing/basics.html
import multiprocessing
import psutil

# modules
import scrub as ss
import vpn_tools as vt

def switch_vpn(p_scrub, int_wait = None):

    if int_wait is None:
        int_wait = config.gbl_int_wait

    while True:
        
        # activate
        p_scrub_pid.suspend()
        p = vt.activate_vpn()
        p_scrub_pid.resume()
        
        # do
        time.sleep(int_wait)
        
        # deactivate
        p_scrub_pid.suspend()
        vt.deactivate_vpn(p)

    return

def scrub():

    # wait for p_vpn to catch up
    while vt.get_external_ip() == config.gbl_str_orig_ip:
        time.sleep(30)

    # scrub
    ss.scrub_manager()

    return

p_scrub = multiprocessing.Process(name='scrub', target=scrub)
p_scrub.start() # improvement: add wait to beginning of master here
p_scrub_pid = psutil.Process(p_scrub.pid)

p_vpn = multiprocessing.Process(name='update_vpn', target=switch_vpn, args=(p_scrub_pid,))
p_vpn.start()

p_scrub.join()
p_vpn.terminate()