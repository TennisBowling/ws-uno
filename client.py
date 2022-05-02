import websockets
import asyncio
from ujson import loads, dumps
from typing import List, Tuple
import os
import aioconsole
from numpy.random import choice
from numpy import arange
import random


class UnoCard:
    def __init__(self, color: str, number: int, is_wild: bool, is_plusfour: bool):
        self.color = color
        self.number = number
        self.is_wild = is_wild 
        self.is_plusfour = is_plusfour

    #def __eq__(self, other):
    #    return (self.color == other.color and self.number == other.number) or (self.is_wild == other.is_wild) or (self.is_plusfour == other.is_plusfour)
    
    def __repr__(self):
        if self.is_wild:
            return 'wild'
        elif self.is_plusfour:
            return 'plus four'
        else:
            return f'{self.color} {self.number}'
    
def load_rawcard(rawcard: str) -> UnoCard:
    return UnoCard(color=rawcard[0], number=rawcard[1], is_wild=rawcard[2], is_plusfour=rawcard[3])

def is_playable(one: UnoCard, two: UnoCard) -> bool:    # one is the card that just has been played
    return one.color == two.color or one.number == two.number or two.is_wild or two.is_plusfour

def clear():
    os.system('cls' if os.name=='nt' else 'clear')

def skewed_rng() -> Tuple[bool, bool]:
    # we need to pick weather the card will be a wild or plus four, but they cannot be both.
    # there are 108 cards total in the deck, and there are four wilds and four plus fours, so we need to use
    # choice(arange(0, 2), p=[0.07, 0.93]) to skew the distribution
    wild = bool(choice(arange(0, 2), p=[0.97, 0.03]))
    plusfour = bool(choice(arange(0, 2), p=[0.97, 0.03]))
    if wild and plusfour:
        return skewed_rng()
    return (wild, plusfour)

async def play(opponent_card: UnoCard, opponent_amount: int, ourdeck: List[UnoCard]) -> UnoCard:
    clear()
    while True:
        playable_cards = [card for card in ourdeck if is_playable(opponent_card, card)]
        card = await aioconsole.ainput(f'Opponent played {opponent_card}, and has {opponent_amount} cards remaining.\nOur deck has {ourdeck}\nbut we can only play {playable_cards}, or type "pick" at anytime.\nWhat card do you want to play?\n')
        if card == 'pick':
            wild, plusfour = skewed_rng()
            ourdeck.append(UnoCard(choice(['red', 'blue', 'green', 'yellow']), random.randint(1, 9), wild, plusfour))
            print(f'We picked a {ourdeck[-1]}')
            return opponent_card
        try:
            ourdeck.remove(playable_cards[int(card) - 1])
            return playable_cards[int(card) - 1]
        except IndexError:
            print('Invalid card')

async def game_loop(ws, deck: List[UnoCard]):
    while True:
        res = loads(await ws.recv())
        if res['status'] == 'in-progress':
            card = await play(load_rawcard(res['played']), res['cards'], deck)
            # send card in format of [color, number, is_wild, is_plusfour]
            await ws.send(dumps({'played': [card.color, card.number, card.is_wild, card.is_plusfour], 'cards': len(deck)}))
        else:
            print(f'Game ended with {res["winner"]} winning')
            exit(0)

"""
the websocket connection will send events which are (in chronological order):
- when the game starts
- our deck, and the initial played card (dealt by the server)
- every time the opponent plays a card, the card they played, and the number of cards in their deck
"""

async def main():
    async with websockets.connect('ws://localhost:8765') as ws:
        while True:
            print('Waiting for game to start...')
            res = loads(await ws.recv())
            if res['status'] == 'ready':
                break
        
        res = loads(await ws.recv())


        deck: List[UnoCard] = []
        for rawcard in res['cards']:    # the cards recieved are a list of a list which indexes were 0: color, 1: number, 2: is_wild, 3: is_plusfour
            deck.append(load_rawcard(rawcard))

        print(f'Our deck is {deck}')
        
        starter = res['starter']
        if starter:
            print('We are playing first')
            await game_loop(ws, deck)
        else:
            print('Opponent is playing first')
            await game_loop(ws, deck)

asyncio.run(main())