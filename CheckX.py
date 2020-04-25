from ctypes import windll
from multiprocessing.dummy import Pool as ThreadPool
from os import path, mkdir, system
from queue import Queue
from threading import Thread
from time import sleep, strftime

from colorama import Fore, init
from requests import ConnectionError, get
from urllib3.connectionpool import SocketError, SSLError, MaxRetryError, ProxyError
from yaml import full_load

init()
default_values = '''checker:

  # Check if current version of CheckX is latest  
  check_for_updates: true

  # Higher for better accuracy but slower (counted in milliseconds)
  timeout: 8000

  # Threads for account checking
  threads: 200

  # Proxy types: https | socks4 | socks5
  proxy_type: 'socks4'
  
  # Save not working proxies (will take a little longer than normal)
  save_dead: true

  # Normal users should keep this false unless problem start happening
  debugging: false
'''
while True:
    try:
        config = full_load(open('config.yml', 'r', errors='ignore'))
        break
    except FileNotFoundError:
        open('config.yml', 'w').write(default_values)
        system('cls')


class Main:
    def __init__(self):
        self.dead = 0
        self.live = 0
        self.cpm = 0
        self.trasp = 0
        self.savedead = Queue()
        self.savelive = Queue()
        self.savetrans = Queue()
        self.version = '1.0'
        sign = f'''{Fore.LIGHTCYAN_EX}
_________ .__                   __    ____  ___
\_   ___ \|  |__   ____   ____ |  | __\   \/  /
/    \  \/|  |  \_/ __ \_/ ___\|  |/ / \     /
\\     \___|   Y  \  ___/\  \___|    <  /     \\
 \______  /___|  /\___  >\___  >__|_ \/___/\  \\
        \/     \/     \/     \/     \/      \_/
'''
        self.myip = str(get('http://api.ipify.org').text)
        self.proxyjudge = 'http://azenv.net'
        windll.kernel32.SetConsoleTitleW(f'CheckX-{self.version} | By ShadowOxygen')
        self.checktype = Checker.type
        if Checker.version_check:
            try:
                gitversion = str(
                    get(url='https://raw.githubusercontent.com/ShadowBlader/CheckX/master/version').text)
                if f'{self.version}\n' != gitversion:
                    print(sign)
                    print(f'{Fore.LIGHTRED_EX}Your version is outdated.')
                    print(
                        f'Your version: {self.version}\nLatest version: {gitversion}\nGet latest version in the link below\nhttps://github.com/ShadowBlader/CheckX/releases\n\nStarting in 6 seconds...{Fore.LIGHTCYAN_EX}')
                    sleep(6)
                    system('cls')
            except Exception as e:
                if Checker.debug:
                    print(f'\nError for updating checking:\n {e}\n')
                pass
        try:
            self.announcement = get(
                url='https://raw.githubusercontent.com/ShadowBlader/CheckX/master/announcement').text
        except:
            self.announcement = ''
            pass
        print(sign)
        while True:
            if self.checktype not in ['socks4', 'socks5', 'https', 'http']:
                print(Fore.LIGHTRED_EX)
                self.checktype = input(
                    'Proxy type is unknown, Please enter correct proxy type (SOCKS4, SOCKS5, HTTPS): ').lower()
                continue
            else:
                break
        while True:
            print(Fore.LIGHTCYAN_EX)
            file = input('Please Enter Proxylist Name (Please include extension name, Example: proxylist.txt): ')
            try:
                self.proxylist = open(file, 'r', encoding='u8', errors='ignore').read().split('\n')
                break
            except FileNotFoundError:
                print(f'\n{Fore.LIGHTRED_EX}File not found, please try again.{Fore.LIGHTCYAN_EX}\n')
                continue
        print('\nLoading Threads...\n')
        unix = str(strftime('[%d-%m-%Y %H-%M-%S]'))
        self.folder = f'results/{unix}'
        if not path.exists('results'):
            mkdir('results')
        if not path.exists(self.folder):
            mkdir(self.folder)
        self.accounts = [x for x in self.proxylist if ':' in x]
        if Checker.save_dead:
            Thread(target=self.save_dead, daemon=True).start()
        Thread(target=self.save_hits, daemon=True).start()
        Thread(target=self.save_trans, daemon=True).start()
        Thread(target=self.cpmcounter, daemon=True).start()
        pool = ThreadPool(processes=Checker.threads)
        system('cls')
        Thread(target=self.tite).start()
        print(sign)
        print(self.announcement)
        print('\nPlease wait for proxies to finish checking...')
        pool.imap(func=self.check_proxies, iterable=self.accounts)
        pool.close()
        pool.join()
        while True:
            if int(self.savelive.qsize() + self.savedead.qsize() + self.savedead.qsize()) == 0:
                print(f'\n{Fore.LIGHTGREEN_EX}Live proxies: {self.live}\n'
                      f'{Fore.LIGHTYELLOW_EX}Transparent proxies: {self.trasp}\n'
                      f'{Fore.LIGHTRED_EX}Dead proxies: {self.dead}\n'
                      f'{Fore.LIGHTRED_EX}\n[EXIT] You can now exit the program...')
                break

    def save_dead(self):
        while True:
            while self.savedead.qsize() != 0:
                with open(f'{self.folder}/Dead.txt', 'a', encoding='u8') as dead:
                    dead.write(f'{self.savedead.get()}\n')

    def save_hits(self):
        while True:
            while self.savelive.qsize() != 0:
                with open(f'{self.folder}/Live.txt', 'a', encoding='u8') as h:
                    h.write(f'{self.savelive.get()}\n')

    def save_trans(self):
        while True:
            while self.savetrans.qsize() != 0:
                with open(f'{self.folder}/Transparent.txt', 'a', encoding='u8') as z:
                    z.write(f'{self.savetrans.get()}\n')

    def check_proxies(self, proxy):
        proxy_dict = {}
        if proxy.count(':') == 3:
            spl = proxy.split(':')
            proxy = f'{spl[2]}:{spl[3]}@{spl[0]}:{spl[1]}'
        if self.checktype == 'http' or self.checktype == 'https':
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'https://{proxy}'
            }
        elif self.checktype == 'socks4' or self.checktype == 'socks5':
            proxy_dict = {
                'http': f'{self.checktype}://{proxy}',
                'https': f'{self.checktype}://{proxy}'
            }
        try:
            r = get(url=self.proxyjudge, proxies=proxy_dict, timeout=Checker.timeout).text
            if r.__contains__(self.myip):
                self.trasp += 1
                self.savetrans.put(proxy)
            else:
                self.live += 1
                self.savelive.put(proxy)
        except (ConnectionError, SocketError, SSLError, MaxRetryError, ProxyError):
            self.dead += 1
            if Checker.save_dead:
                self.savedead.put(proxy)
        except Exception as e:
            if Checker.debug:
                print(f'Error: {e}')

    def tite(self):
        while True:
            windll.kernel32.SetConsoleTitleW(
                f'CheckX-{self.version} | '
                f'Live: {self.live}'
                f' | Dead: {self.dead}'
                f' | Transparent {self.trasp}'
                f' | Left: {len(self.accounts) - (self.live + self.dead + self.trasp)}/{len(self.accounts)}'
                f' | CPM: {self.cpm}')
            sleep(0.01)

    def cpmcounter(self):
        while True:
            while (self.live + self.dead) >= 1:
                now = self.live + self.dead
                sleep(4)
                self.cpm = (self.live + self.dead - now) * 15


class Checker:
    version_check = bool(config['checker']['check_for_updates'])
    timeout = int(config['checker']['timeout']) / 1000
    threads = int(config['checker']['threads'])
    type = str(config['checker']['proxy_type']).lower()
    save_dead = bool(config['checker']['save_dead'])
    debug = bool(config['checker']['debugging'])


if __name__ == '__main__':
    Main()
