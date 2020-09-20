import discord
from config import DISCORD_TOKEN, RIOT_KEY

import requests
import json


client = discord.Client()
PREFIX = '!'

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(f'{PREFIX}pdl'):
        summoner_name = 'tsctsctsctsc'
        server = 'NA'

        args = message.content.split(maxsplit=1)
        if len(args) != 1:
            summoner_name = args[1]
            server = 'BR'

        league_colors = {
            'IRON': 0x636363,
            'BRONZE': 0xb8840d,
            'SILVER': 0xb5b5b5,
            'GOLD': 0xe6d200,
            'PLATINUM': 0x00b084,
            'DIAMOND': 0x40d9ed,
            'MASTER': 0x883091,
            'GRANDMASTER': 0xcf2746,
            'CHALLENGER': 0xebede4
        }

        league_info = get_league_info(summoner_name, server);

        if league_info == None:
            await message.channel.send(f'Deu algum erro na busca do jogador {summoner_name} no server {server}')
            return
        
        if not bool(league_info):
            await message.channel.send(f'O jogador {summoner_name} não tem dados ranqueados disponíveis')

        embed = discord.Embed(title=summoner_name, color=league_colors[league_info['tier']])
        embed.add_field(name='Elo', value=f'{league_info["tier"].title()} {league_info["rank"]}')
        embed.add_field(name='LP', value=f'{league_info["lp"]}')
        embed.add_field(name='Win Rate', value=f'{league_info["win_ratio"]}%', inline=False)

        await message.channel.send(embed=embed)


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
        
        return {
            'tier': league_info['tier'],
            'rank': league_info['rank'],
            'lp': league_info['leaguePoints'],
            'win_ratio': int(100*league_info['wins']/(league_info['wins'] + league_info['losses']))
        }
    except:
        print('Error')
        return dict()


def main():
    client.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()