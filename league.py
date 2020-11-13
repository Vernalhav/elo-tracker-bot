from config import RIOT_KEY

import requests
import logging
import json
import sys
import os


CHAMP_FILE = os.path.join(sys.path[0], 'champion.json')
CHAMP_INDEX = os.path.join(sys.path[0], 'champion_ids.json')

queue_ids = {
    'RANKED_SOLO_5x5': 420,
    'RANKED_FLEX_SR': 440
}

server_prefixes = {
    'NA': 'na1',
    'BR': 'br1'
}

headers = {
    "User-Agent": "EloTracker/0.1 personal discord bot",
    'X-Riot-Token': RIOT_KEY
}

summoner_ids = {}


def get_league_info(summoner_name='tsctsctsctsc', server='NA', queue='RANKED_SOLO_5x5'):

    server_prefix = server_prefixes[server]

    if summoner_name not in summoner_ids:
        client_req_url = f'https://{server_prefix}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}'
        client_id_request = requests.get(client_req_url, headers=headers)

        if client_id_request.status_code != 200:
            return None
        
        client_id = client_id_request.json()['id']
        account_id = client_id_request.json()['accountId']
        summoner_ids[summoner_name] = {'clientId': client_id, 'accountId': account_id}

    client_id = summoner_ids[summoner_name]['clientId']

    league_req_url = f'https://{server_prefix}.api.riotgames.com/lol/league/v4/entries/by-summoner/{client_id}'
    league_request = requests.get(league_req_url, headers=headers)

    try:
        league_info = None
        for queue_type_info in league_request.json():
            if queue_type_info['queueType'] == queue:
                league_info = queue_type_info
        
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
        logger.info(f'Local files not found and latest patch is {current_patch}. Updating files...')
        get_champion_data(current_patch)
        create_champion_index()
        logger.info(f'Done updating {CHAMP_FILE} and {CHAMP_INDEX}')


    with open(CHAMP_FILE) as f:
        champions_patch = json.load(f)['version']
        
        if champions_patch != current_patch:
            logger.info(f'Local files are from patch {champions_patch} and latest patch is {current_patch}. Updating files...')
            get_champion_data(current_patch)
            create_champion_index()
            logger.info(f'Done updating champion.json and champion_ids.json')


def get_champ_icon_url(champion, skin=0):
    
    global current_patch
    retries = 0
    while current_patch == None and retries < 3:
        current_patch = get_latest_patch()
        retries += 1

    return f'http://ddragon.leagueoflegends.com/cdn/{current_patch}/img/champion/{champion}.png'


def get_item_icon_url(item):

    global current_patch
    retries = 0
    while current_patch == None and retries < 3:
        current_patch = get_latest_patch()
        retries += 1

    return f'http://ddragon.leagueoflegends.com/cdn/{current_patch}/img/item/{item}.png'


def get_champion_name(champion_id):
    with open(CHAMP_INDEX) as f:
        return json.load(f)[str(champion_id)]
    return None


def get_last_match(summoner_name, server='NA', queue='RANKED_SOLO_5x5'):

    server_prefix = server_prefixes[server]

    if summoner_name not in summoner_ids:
        client_req_url = f'https://{server_prefix}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}'
        client_id_request = requests.get(client_req_url, headers=headers)

        if client_id_request.status_code != 200:
            raise Exception()
        
        client_id = client_id_request.json()['id']
        account_id = client_id_request.json()['accountId']
        summoner_ids[summoner_name] = {'clientId': client_id, 'accountId': account_id}

    account_id = summoner_ids[summoner_name]['accountId']

    payload = {'queue': queue_ids[queue], 'endIndex': 1, 'beginIndex': 0}
    last_match_url = f'https://{server_prefix}.api.riotgames.com/lol/match/v4/matchlists/by-account/{account_id}'
    last_match_req = requests.get(last_match_url, params=payload, headers=headers)

    if last_match_req.status_code != 200:
        raise Exception(last_match_req.status_code)

    last_match_id = last_match_req.json()['matches'][0]['gameId']
    
    match_data_url = f'https://{server_prefix}.api.riotgames.com/lol/match/v4/matches/{last_match_id}'
    match_data_req = requests.get(match_data_url, headers=headers)

    if match_data_req.status_code != 200:
        raise Exception()

    match_data = match_data_req.json()

    summoner_index = -1
    for summoner in match_data['participantIdentities']:
        if summoner['player']['summonerName'].lower() == summoner_name:
            summoner_index = summoner['participantId']
            break    

    summoner_stats = None
    for participant in match_data['participants']:
        if participant['participantId'] == summoner_index:
            summoner_stats = participant
            break

    KDA = f'{summoner_stats["stats"]["kills"]}/{summoner_stats["stats"]["deaths"]}/{summoner_stats["stats"]["assists"]}'
    win = summoner_stats['stats']['win']
    champion = get_champion_name(summoner_stats['championId'])
    champ_icon = get_champ_icon_url(champion)
    elapsed_time = str(match_data['gameDuration']//60) + ' min'
    
    item_ids = [summoner_stats['stats'][f'item{i}'] for i in range(6)]
    item_urls = [ get_item_icon_url(item_id) for item_id in item_ids[::-1] ]

    print(champ_icon)
    return {
        'KDA': KDA,
        'win': win,
        'elapsedTime': elapsed_time,
        'champion': champion,
        'championIconURL': champ_icon,
        'items': item_urls
    }


logfile = 'bot_log.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fp = logging.FileHandler(filename=logfile, mode='w')
logger.addHandler(fp)

current_patch = get_latest_patch()
check_new_patch()
logger.info(f'league.py started. Latest patch is {current_patch}')