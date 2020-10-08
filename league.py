from config import RIOT_KEY

import requests
import json
import os


CHAMP_FILE = 'champion.json'
CHAMP_INDEX = 'champion_ids.json'

current_patch = get_latest_patch()


def get_league_info(summoner_name='tsctsctsctsc', server='NA', queue='RANKED_SOLO_5x5'):

    headers = {
        "User-Agent": "EloTracker/0.1 personal discord bot",
        'X-Riot-Token': RIOT_KEY
    }
    
    server_prefix = ['br1', 'na1'][server == 'NA']

    client_req_url = f'https://{server_prefix}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}'
    client_id_request = requests.get(client_req_url, headers=headers)

    if client_id_request.status_code != 200: return None
    client_id = client_id_request.json()['id']

    league_req_url = f'https://{server_prefix}.api.riotgames.com/lol/league/v4/entries/by-summoner/{client_id}'
    league_request = requests.get(league_req_url, headers=headers)

    try:
        league_info = None
        for i, queue_type_info in enumerate(league_request.json()):
            if queue_type_info['queueType'] == queue:
                league_info = league_request.json()[i]
        
        player_data = {
            'tier': league_info['tier'],
            'rank': league_info['rank'],
            'lp': league_info['leaguePoints'],
            'win_ratio': int(100*league_info['wins']/(league_info['wins'] + league_info['losses'])),
            'streak': league_info['hotStreak']
        }
        if 'miniSeries' in league_info:
            player_data['promos'] = {
                'best_of': len(league_info['miniSeries']['progress']),
                'wins': league_info['miniSeries']['wins'],
                'losses': league_info['miniSeries']['losses']
            }
        return player_data

    except:
        print('Error')
        return dict()


def create_champion_index():
    with open(CHAMP_FILE) as f:
        champ_data = json.load(f)['data']

        ids = {}
        for champ in champ_data:
            ids[champ_data[champ]['key']] = champ

        with open(CHAMP_INDEX, 'w') as index:
            json.dump(ids, index)


def get_champion_data(patch):
    req_url = f'http://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/champion.json'
    champ_data_req = requests.get(req_url)
    
    if champ_data_req.status_code != 200:
        return 0

    with open(CHAMP_FILE, 'w') as f:
        json.dump(champ_data_req.json(), f)
        return 1


def get_latest_patch():
    req = requests.get('https://ddragon.leagueoflegends.com/api/versions.json')

    if req.status_code != 200:
        return None
        
    return req.json()[0]


def check_new_patch():

    if not os.path.exists(CHAMP_FILE):
        print(f'Local files not found and latest patch is {current_patch}. Updating files...')
        get_champion_data(current_patch)
        create_champion_index()
        print(f'Done updating {CHAMP_FILE} and {CHAMP_INDEX}')


    with open(CHAMP_FILE) as f:
        champions_patch = json.load(f)['version']
        
        if champions_patch != current_patch:
            print(f'Local files are from patch {champions_patch} and latest patch is {current_patch}. Updating files...')
            get_champion_data(current_patch)
            create_champion_index()
            print(f'Done updating {CHAMP_FILE} and {CHAMP_INDEX}')


def get_champ_icon_url(champion):
    
    retries = 0
    while current_patch == None and retries < 3:
        global current_patch = get_latest_patch()
        retries += 1

    return f'http://ddragon.leagueoflegends.com/cdn/{current_patch}/img/champion/{champion}.png'



if __name__ == '__main__':
    check_new_patch()