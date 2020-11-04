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


def textify_change(state_name, previous, current):
    prev_cast = previous['votes_cast']
    prev_all = previous['votes_all']
    prev_c = previous['candidates']

    curr_cast = current['votes_cast']
    curr_all = current['votes_all']
    curr_c = current['candidates']
    biden_ahead = (curr_c['Joe Biden']['votes'] > curr_c['Donald Trump']['votes'])

    candidate_delta = abs(curr_c['Joe Biden']['votes'] - curr_c['Donald Trump']['votes'])

    return f"""
A new vote count for {state_name}.

Biden gained {curr_c['Joe Biden']['votes'] - prev_c['Joe Biden']['votes']:,} votes.
Trump gained {curr_c['Donald Trump']['votes'] - prev_c['Donald Trump']['votes']:,} votes.

The current situation in {state_name} is as follows
Biden: {curr_c['Joe Biden']['votes']:,} votes ({curr_c['Joe Biden']['votes']/curr_cast * 100: 3.2f}%)
Trump: {curr_c['Donald Trump']['votes']:,} votes ({curr_c['Donald Trump']['votes']/curr_cast * 100: 3.2f}%)

{"Biden" if biden_ahead else "Trump"} is ahead of {"Trump" if biden_ahead else "Biden"} by {candidate_delta:,} votes.

votes casted: {curr_cast:,} / {curr_all:,} ({prev_cast/prev_all * 100: 3.2f}%)
"""


if __name__ == '__main__':

    previous = parse_data(get_data())

    while True:

        current = parse_data(get_data())
        changes = False

        for k in d.keys() & battlegrounds:
            if previous[k]['votes_cast'] != current[k]['votes_cast']:
                textify_change(previous[k], current[k])
                previous[k] = current[k]
                changes = True

        if not changes:
            print(f"no changes {datetime.now()}")

        sleep(60)