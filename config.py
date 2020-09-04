# program-wide, public config

# since using as config, best to use absolute ref

# ip
import subprocess

# combos
import itertools
import string
import random

# secrets
import secrets # ie private config

##########
# IP
##########

# duplicated here from vpn_tools to avoid circular reference
def get_external_ip():
    '''
    get external ip

    arguments:
    None

    returns:
    output (str): external ip
    '''

    # subprocess
    # https://stackoverflow.com/questions/4256107/running-bash-commands-in-python

    # sudo apt-get install dnsutils

    # https://www.cyberciti.biz/faq/how-to-find-my-public-ip-address-from-command-line-on-a-linux/
    # bashCommand = "dig TXT +short o-o.myaddr.l.google.com @ns1.google.com" # this works
    bashCommand = 'wget http://ipinfo.io/ip -qO -'

    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    return str(output.decode('utf-8'))[:-1] # convert bytes to string

gbl_str_orig_ip = get_external_ip()

##########
# openvpn
##########

gbl_str_path_pass = secrets.gbl_str_path_pass
gbl_str_path_ovpn_root = "/scrub/openvpn/config/" # incl last /

gbl_int_wait = 600 # how many seconds until next VPN

##########
# selenium
##########

gbl_str_path_chromedriver = "/usr/local/bin/chromedriver"

##########
# scraping
##########

gbl_str_website = secrets.gbl_str_website

gbl_str_filename = "/scrub/output/scraping_results.csv"
gbl_str_path_log = "/scrub/output/log.txt"

# starting points for scrubbing results
gbl_ls_combo = [''.join(item) for item in itertools.product(string.ascii_letters[:26], repeat=3)]
random.shuffle(gbl_ls_combo)