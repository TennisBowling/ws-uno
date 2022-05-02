from numpy.random import choice
from numpy import arange
import websockets
from ujson import loads, dumps
import asyncio
import random
from typing import List, Tuple

"""
server.py
we need to send a message to the clients:
- when the game starts
- their deck, and the initial played card (set by us), and should all be random
- every time a player plays, the card they played, and the number of cards in their deck (send to the other player)
"""    
    
conns: List[websockets.WebSocketServerProtocol] = []
async def send_to_all(data):
    for conn in conns:
        await conn.send(dumps(data))

def skewed_rng() -> Tuple[bool, bool]:
    # we need to pick weather the card will be a wild or plus four, but they cannot be both.
    # there are 108 cards total in the deck, and there are four wilds and four plus fours, so we need to use
    # choice(arange(0, 2), p=[0.07, 0.93]) to skew the distribution
    wild = bool(choice(arange(0, 2), p=[0.97, 0.03]))
    plusfour = bool(choice(arange(0, 2), p=[0.97, 0.03]))
    if wild and plusfour:
        return skewed_rng()
    return (wild, plusfour)

def starter_rng() -> Tuple[bool, bool]:
    one = bool(random.randint(0, 1))
    two = bool(random.randint(0, 1))
    if one and two:
        return starter_rng()
    return (one, two)

def make_random_deck():
    ret = []
    for _ in range(7):
        # card must be either wild or plus four, not both
        wild, plusfour = skewed_rng()
        ret.append([choice(['red', 'blue', 'green', 'yellow']), random.randint(1, 9), wild, plusfour])
    return ret

async def game_loop(ws: websockets.WebSocketServerProtocol):
    conns.append(ws)
    print(ws.remote_address)
    if len(conns) == 2:
        await send_to_all({'status': 'ready'})
        # generate 7 random cards and send card in format of [color, number, is_wild, is_plusfour]
        starter = starter_rng()
        p1 = conns[0] if starter[0] else conns[1]
        p2 = conns[1] if starter[0] else conns[0]

        await conns[0].send(dumps({'starter': starter[0], 'cards': make_random_deck()}))
        await conns[1].send(dumps({'starter': starter[1], 'cards': make_random_deck()}))

        # now that the game has started, we need to send the initial played card (which is random)
        # and the number of cards in the other player's deck
        await p1.send(dumps({'played': [choice(['red', 'blue', 'green', 'yellow']), random.randint(1, 9), False, False], 'cards': 7, 'status': 'in-progress'}))

        # send back and forth between the two players
        while True:
            data = loads(await p1.recv())
            if data['cards'] == 0:
                await send_to_all({'status': 'game-over', 'winner': p1.remote_address})
            await p2.send(dumps({'played': data['played'], 'cards': data['cards'], 'status': 'in-progress'}))
            data = loads(await p2.recv())
            if data['cards'] == 0:
                await send_to_all({'status': 'game-over', 'winner': p2.remote_address})
            await p1.send(dumps({'played': data['played'], 'cards': data['cards'], 'status': 'in-progress'}))
    else:
        await asyncio.Future()




async def main():
    async with websockets.serve(game_loop, host='localhost', port=8765) as server:
        await asyncio.Future()

asyncio.run(main())