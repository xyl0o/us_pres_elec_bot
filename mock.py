import json

from check import parse_data, get_data, textify_change

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

    for k in set(new.keys()).intersection(battlegrounds):
        if old[k]['votes_cast'] != new[k]['votes_cast']:
            print(textify_change(
                state_name=k,
                old=old[k],
                new=new[k],
                candidates=candidates))
