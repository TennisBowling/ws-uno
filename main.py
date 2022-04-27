import websockets
import random
import asyncio
import ujson
from typing import List


class CustomWsClientProtocol(websockets.WebSocketClientProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def recv() -> dict:
        return ujson.loads(await super().recv())
    
    async def send(data) -> None:
        await super().send(ujson.dumps(data))


class UnoCard:
    def __init__(self, color: str, number: int, is_wild: bool, is_plusfour: bool):
        self.color = color
        self.number = number
        self.is_wild = is_wild 
        self.is_plusfour = is_plusfour

    def __eq__(self, other):
        return (self.color == other.color and self.number == other.number) or (self.is_wild == other.is_wild) or (self.is_plusfour == other.is_plusfour)
    
def is_playable(one: UnoCard, two: UnoCard) -> bool:    # one is the card that just has been played
    return one.color == two.color or one.number == two.number or two.is_wild or two.is_plusfour


async def main():
    async with websockets.connect('ws://unoserver.com', create_protocol=CustomWsClientProtocol) as ws:
        while True:
            res = await ws.recv()
            if res['status'] == 'ready':
                break
        
        res = await ws.recv()
        playerid = res['id']


        deck: List[UnoCard] = []
        for rawcard in res['cards']:    # the cards recieved are a list of a list which indexes were 0: color, 1: number, 2: is_wild, 3: is_plusfour
            deck.append(UnoCard(color=rawcard[0], number=rawcard[1], is_wild=rawcard[2], is_plusfour=rawcard[3]))

        print(f'We are {playerid}')
        print(f'Our deck is {deck}')
        
        starter = await ws.recv()['starter']
        if starter:
            print('We are playing first')
        else:
            print('Opponent is playing first')
        
        
    