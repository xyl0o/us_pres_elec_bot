import os
from time import sleep
from datetime import datetime

import requests


api_endpoint = os.environ['ELECTION_API_ENDPOINT']


def parse_state(r):
    return {
        'name': r[0][0].strip(),
        'votes_cast': int(r[0][1]),
        'votes_all': int(r[0][2]),
        'votes_ratio': int(r[0][3])/100,
        'candidates': {
            f"{c[0]} {c[1]}".strip(): {
                'party': c[2].strip(),
                'votes': int(c[4]),
            }
            for c in r[1]
        }
    }


def parse_data(r):
    states_list = [parse_state(s) for num, s in r['P'].items()]
    return {
        s['name']: {
            k: v
            for k, v in s.items()
            if k != 'name'
        }
        for s in states_list}


def get_data():
    return requests.get(api_endpoint).json()


def filter_states(old, new, battlegrounds):
    for state in set(new.keys()).intersection(battlegrounds):
        if (new[state]['votes_cast'] - old[state]['votes_cast']) > 10:
            yield state


def textify_change(state, new, candidates, old=None):
    curr_cast = new['votes_cast']
    curr_all = new['votes_all']

    # Sort candidates list by current votes
    sorted_candidates = sorted(
        candidates,
        key=lambda c: new['candidates'][c]['votes'],
        reverse=True)

    txt = ""

    if old:
        txt += f"More votes are in for {state}.\n"

        for c in sorted_candidates:
            if (delta := old['candidates'][c]['votes'] - new['candidates'][c]['votes']) != 0:
                trend = "gained" if delta > 0 else "lost"
                txt += f"{c} {trend} {abs(delta):,} votes.\n"

        txt += "\n"

    txt += f"The current situation in {state}:\n"

    for c in sorted_candidates:
        votes = new['candidates'][c]['votes']
        txt += f"{c} has {votes:,} votes ({round(votes / curr_cast * 100, 2): 3.2f}%)\n"

    lead_delta = (
        new['candidates'][sorted_candidates[0]]['votes']
        - new['candidates'][sorted_candidates[1]]['votes'])

    txt += "\n"
    txt += f"{sorted_candidates[0]} is ahead of {sorted_candidates[1]} by {lead_delta:,} votes.\n"

    txt += "\n"
    txt += f"So far {curr_cast:,} votes have been counted ({curr_cast/curr_all * 100: 3.2f}%)\n"
    txt += f"This leaves about {int(round(curr_all - curr_cast, -2)):,} votes on the table.\n"

    return txt


if __name__ == '__main__':
    battlegrounds = {
        'Arizona',
        'Georgia',
        'Nevada',
        'North Carolina',
        'Pennsylvania',
    }

    candidates = ['Joe Biden', 'Donald Trump']

    old = parse_data(get_data())

    while True:
        new = parse_data(get_data())

        for state in filter_states(old, new, battlegrounds):

            txt = textify_change(
                state=state, old=old[state], new=new[state], candidates=candidates)

            print(txt)

            old[state] = new[state]

        sleep(30)