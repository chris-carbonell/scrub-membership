# general
import os
import random
import time

# subprocess
import subprocess

# config
# import yaml
import config

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

def activate_vpn(str_path_config = None, str_path_pass = None):
    '''
    use subprocess to activate a given VPN

    arguments:
    str_path_config (str): rel/abs path to .ovpn

    returns:
    process (subprocess): process of VPN activation

    notes:
    - to kill, use process.terminate()

    example call:
    activate_vpn("./openvpn/us-tpa.prod.surfshark.com_udp.ovpn")
    '''

    # make assumptions if necessary

    if str_path_config is None:
        str_path_config = get_random_ovpn()

    if str_path_pass is None:
        str_path_pass = config.gbl_str_path_pass

    # build bashCommand
    # bashCommand = "openvpn --config ./openvpn-test/ss-test.ovpn --auth-user-pass ./openvpn-test/ss-pass.txt" # testing
    ls_bash_command = ["sudo", "openvpn", "--auth-nocache", "--config", str_path_config, "--auth-user-pass", str_path_pass]

    process = subprocess.Popen(ls_bash_command, stdout=subprocess.PIPE, preexec_fn=os.setpgrp)
    # output, error = process.communicate() # this would wait until it terminates which activating never does
    # if you activate via the command line, it stays open until you kill it yourself

    # wait until VPN activated
    while get_external_ip() == config.gbl_str_orig_ip:
        time.sleep(1)

    return process

def deactivate_vpn(process_vpn, int_wait = 10):
    '''
    deactivate vpn

    arguments:
    process_vpn (subprocess): process of VPN activation

    returns:
    None
    '''

    # process_vpn.terminate()
    # https://stackoverflow.com/questions/50618411/killing-sudo-started-subprocess-in-python
    subprocess.check_call(["sudo", "kill", str(process_vpn.pid)])
    
    # wait until terminated
    while check_pid(process_vpn.pid):
        time.sleep(5)

    time.sleep(int_wait)

    return

def get_random_ovpn(str_path_ovpn_root = None):

    # str_path_ovpn_root = "./openvpn/" # incl last /
    if str_path_ovpn_root is None:
        str_path_ovpn_root = config.gbl_str_path_ovpn_root

    str_extension = "ovpn" # excl .

    ls_ovpn = [f for f in os.listdir(str_path_ovpn_root) if f.endswith('.' + str_extension)]

    return str_path_ovpn_root + random.choice(ls_ovpn)

def check_pid(pid):        
    """ Check For the existence of a unix pid. """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True
