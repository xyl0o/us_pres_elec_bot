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
        if abs(new[state]['votes_cast'] - old[state]['votes_cast']) > 10:
            yield state


def textify_change(state, new, candidates, old=None):
    curr_cast = new['votes_cast']
    curr_all = new['votes_all']

    # Sort candidates list by current votes
    sorted_candidates = sorted(
        candidates,
        key=lambda c: new['candidates'][c]['votes'],
        reverse=True)

    lead_delta = abs(
        new['candidates'][sorted_candidates[0]]['votes']
        - new['candidates'][sorted_candidates[1]]['votes'])

    open_votes = curr_all - curr_cast

    txt = ""

    if old:
        txt += f"More votes in <strong>{state}</strong>.\n"
        txt += f"{sorted_candidates[0]} is now ahead of {sorted_candidates[1]} by {lead_delta:,} votes."

        txt += "\n\n"
        for c in sorted_candidates:
            if (delta := new['candidates'][c]['votes'] - old['candidates'][c]['votes']) != 0:
                trend = "gained" if delta > 0 else "lost"
                txt += f"{c} {trend} {abs(delta):,} votes.\n"
    else:
        # txt += f"<strong>{state}</strong>:\n"
        txt += f"<pre>{state}</pre>\n"

        if open_votes < lead_delta:
            txt += f"{sorted_candidates[0]} won this state by a {lead_delta:,} vote margin.\n\n"
        else:
            txt += f"{sorted_candidates[0]} is ahead of {sorted_candidates[1]} by {lead_delta:,} votes.\n\n"

        for c in sorted_candidates:
            votes = new['candidates'][c]['votes']
            txt += f"{c} has {votes:,} votes ({round(votes / curr_cast * 100, 2): 3.2f}%)\n"

        if open_votes >= lead_delta:
            txt += "\n"
            txt += f"{curr_cast:,} votes have been counted so far (roughly {round(curr_cast/curr_all * 100, 1): 3.1f}%)."

    return txt
