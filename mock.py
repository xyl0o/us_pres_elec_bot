import json

from check import parse_data, get_data, textify_change, filter_states


if __name__ == '__main__':

    battlegrounds = {
        'Alaska',
        'Michigan',
        'Wisconsin',
        'Arizona',
        'Georgia',
        'Nevada',
        'North Carolina',
        'Pennsylvania',
    }

    candidates = ['Joe Biden', 'Donald Trump']

    with open("old.json", "r") as f_old:
        old = parse_data(json.loads(f_old.read()))

    with open("new.json", "r") as f_new:
        new = parse_data(json.loads(f_new.read()))

    for state in filter_states(old, new, battlegrounds):

        txt = textify_change(
            state=state, old=old[state], new=new[state], candidates=candidates)

        print(txt)

        old[state] = new[state]