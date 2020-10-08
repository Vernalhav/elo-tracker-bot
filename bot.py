import discord
import league
from config import DISCORD_TOKEN

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

        await pdl_command(message, summoner_name, server)


async def pdl_command(message, summoner_name, server):
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

    league_info = league.get_league_info(summoner_name, server)

    if league_info == None:
        await message.channel.send(f'Deu algum erro na busca do jogador {summoner_name} no server {server}')
        return
    
    if not bool(league_info):
        await message.channel.send(f'O jogador {summoner_name} não tem dados ranqueados disponíveis')
        return

    last_match = league.get_last_match(summoner_name, server)

    embed = discord.Embed(title=summoner_name, color=league_colors[league_info['tier']])
    embed.add_field(name='Elo', value=f'{league_info["tier"].title()} {league_info["rank"]}')
    embed.add_field(name='LP', value=f'{league_info["lp"]}')
    if 'promos' in league_info:
        promos = league_info['promos']
        embed.add_field(name=f'MD{promos["best_of"]}', value=f'{promos["wins"]}W {promos["losses"]}L')

    embed.add_field(name='Win Rate', value=f'{league_info["win_ratio"]}%', inline=False)

    embed.add_field(name='Last match', value=['Lose', 'Win'][last_match['win']])
    embed.add_field(name=last_match['champion'], value=last_match['KDA'])
    embed.add_field(name='Time', value=last_match['elapsedTime'])
    
    embed.set_thumbnail(url=last_match['championIconURL'])

    sent_message = await message.channel.send(embed=embed)
    if league_info['streak']:
        await sent_message.add_reaction('🐦')
        await sent_message.add_reaction('🔥')


def main():
    client.run(DISCORD_TOKEN)


if __name__ == '__main__':
    main()