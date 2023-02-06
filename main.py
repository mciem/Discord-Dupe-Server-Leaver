from pystyle import Colors
from tls_client import Session
from json import loads
from random import choice
from time import sleep
from threading import Thread

class Console:
    def error(txt: str) -> None:
        print(Colors.red + "[" + Colors.white + "!" + Colors.red + "] " + Colors.white + txt)

    def debug(txt: str) -> None:
        print(Colors.blue + "[" + Colors.white + "^" + Colors.blue + "] " + Colors.white + txt)

    def input(txt: str) -> str:
        print(Colors.yellow + "[" + Colors.white + ">" + Colors.yellow + "] " + Colors.white + txt, end="")
        return input("")

class Client:
    def __init__(self, proxy: str) -> None:
        self.headers = {
			"accept":             "*/*",
			"accept-language":    "en-US;q=0.8,en;q=0.7",
			"content-type":       "application/json",
			"origin":             "https://discord.com",
			"sec-ch-ua":          '"Chromium";v="108", "Google Chrome";v="108", "Not;A=Brand";v="99"',
			"sec-ch-ua-mobile":   "?0",
			"sec-ch-ua-platform": '"Windows"',
			"sec-fetch-dest":     "empty",
			"sec-fetch-mode":     "cors",
			"sec-fetch-site":     "same-origin",
			"user-agent":         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        }
        self.session = Session(client_identifier="chrome_108")
        self.proxy = "http://"+proxy

        self.session.get("https://discord.com", headers=self.headers, proxy=self.proxy )
        self.headers["cookie"] = "; ".join(f"{k}={v}" for k,v in self.session.cookies.items())

class Discord:
    def __init__(self, token: str, proxy: str) -> None:
        client = Client(proxy)
        
        self.session = client.session
        self.proxy = client.proxy
        self.proxy_raw = proxy
        self.headers = client.headers
        self.headers["authorization"] = token
    
    def getGuilds(self):
        g = []
        url = "https://discord.com/api/v9/users/@me/guilds"

        resp = self.session.get(url, headers=self.headers)
        if resp.status_code != 200:
            return []

        js = loads(resp.text)
        for x in js:
            g.append(x["id"])
        return g
    
    def leaveGuild(self, gID: str) -> str:
        url = "https://discord.com/api/v9/users/@me/guilds/" + gID
        payload = '{"lurking": false}'


        resp = self.session.delete(url,data=payload,headers=self.headers)
        if resp.status_code == 204:
            return "SUCCESS"
        
        return "FAILED"

class Duper:
    def __init__(self):
        Console.input("Press enter to start...")
        self.proxies = open("data/proxies.txt", "r").read().splitlines()
        
        self.tokens = open("data/tokens.txt", "r").read().splitlines()

        self.guilds = {} # {ID: [token1,token2]}
        self.clients = {} # {token: Discord()}

        self.getAllGuilds()
        self.checkForDupes()
    
    def get(self, token: str):
        try:
            proxy = choice(self.proxies)

            dc = Discord(token=token,proxy=proxy)
            self.clients[token] = dc

            g = dc.getGuilds()

            for guild in g:
                if self.guilds.get(guild):
                    self.guilds[guild].append(token)
                else:
                    self.guilds[guild] = [token]
                
            Console.debug(f"Obtained {len(g)} guild ids from: " + token[:32] + "...")
        except Exception as e:
            Console.error(str(e) + " retrying...")
            self.get(token)

    def getAllGuilds(self):
        threads = []
        for token in self.tokens:
            t = Thread(target=self.get, args=(token,))
            threads.append(t)
        
        for x in threads:
            x.start()
        
        for x in threads:
            x.join()
            
    
    def checkForDupes(self):
        for ID, tokens in self.guilds.items():       
            if len(tokens) > 1:
                ID = str(ID)
                tkn = choice(tokens)
                tokens.remove(tkn)
                Console.debug(f"Detected: {len(tokens)} duplicates in: {ID}")
                for token in tokens:
                    if self.clients[token].leaveGuild(ID) == "SUCCESS":
                        Console.debug(f"{token[:32]}.. has left: {ID}")
            else:
                Console.debug(f"No duplcates found in: {ID}")

Duper()
