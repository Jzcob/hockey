jacob = 920797181034778655
dev_server_dev_channel = 1165858822183735316
suggestion_channel = 1323184650708979733
allowed_channels = [dev_server_dev_channel]
mgr_channel = 1168943605205962912
mod_logs = 1169386959303626772
hockey_discord_server = 1165854570195472516
owner = 1165854743281799218
admin = 1165854745177640990
logs = 1168944556927103067
ticketLog = 1193387303381516319

dev_mode = False

color = 0xffffff
error_channel = 1166019404870463558
footer = "Bot created by @jzcob"

command_log_bool = True
command_log = 1227078412699439104

anahiem_ducks_emoji = "<:anaheim_ducks:1271323054420787251>"
arizona_coyotes_emoji = "<:arizona_coytoes:1271323081226584067>"
boston_bruins_emoji = "<:boston_bruins:1271323100759326771>"
buffalo_sabres_emoji = "<:buffalo_sabers:1271323127456075786>"
calgary_flames_emoji = "<:calgary_flames:1271323213095501894>"
carolina_hurricanes_emoji = "<:carolina_hurricanes:1271323233592803338>"
chicago_blackhawks_emoji = "<:chicago_blackhawks:1271323252966297630>"
colorado_avalanche_emoji = "<:colorado_avalanche:1271323289138233385>"
columbus_blue_jackets_emoji = "<:columbus_blue_jackets:1271323307081338961>"
dallas_stars_emoji = "<:dallas_stars:1271323334772129852>"
detroit_red_wings_emoji = "<:detroit_red_wings:1271323353700892682>"
edmonton_oilers_emoji = "<:edmonton_oilers:1271323370348089410>"
florida_panthers_emoji = "<:florida_panthers:1271323392263327754>"
los_angeles_kings_emoji = "<:los_angeles_kings:1271323410449825844>"
minnesota_wild_emoji = "<:minnesota_wild:1271323479907762266>"
montreal_canadiens_emoji = "<:montreal_canadiens:1271323513562857564>"
nashville_predators_emoji = "<:nashville_predators:1271323534215614495>"
new_jersey_devils_emoji = "<:new_jersy_devils:1271323550921265152>"
new_york_islanders_emoji = "<:new_york_islanders:1271323580688240788>"
new_york_rangers_emoji = "<:new_york_rangers:1271323605430698066>"
ottawa_senators_emoji = "<:ottawa_senators:1271323626569994353>"
philadelphia_flyers_emoji = "<:philadelphia_flyers:1271323653811998800>"
pittsburgh_penguins_emoji = "<:pittsburgh_penguins:1271323675223785535>"
san_jose_sharks_emoji = "<:san_jose_sharks:1271323692579815464>"
seattle_kraken_emoji = "<:seattle_kraken:1271323734497824869>"
st_louis_blues_emoji = "<:st_louis_blues:1271323767125049476>"
tampa_bay_lightning_emoji = "<:tampa_bay_lighting:1271323790541848607>"
toronto_maple_leafs_emoji = "<:toronto_maple_leafs:1271323811220033578>"
utah_hockey_club_emoji = "<:utah_hockey_club:1271323829347815444>" 
vancouver_canucks_emoji = "<:vancouver_canucks:1271323847454363829>"
vegas_golden_knights_emoji = "<:vegas_golden_knights:1271323863237660683>"
washington_capitals_emoji = "<:washington_capitals:1271323877888229491>"
winnipeg_jets_emoji = "<:winnipegg_jets:1271323895177285743>"
nhl_logo_emoji = "<:nhl:1271324226560725022>"

bruins_servers = [hockey_discord_server, 1220512663998693467, 213656921096454145, 1308631989389230161]

premium_users = []
premium_guilds = []
premium_users.append(jacob)
premium_guilds.append(hockey_discord_server)
from discord.ext import tasks
from main import bot
@tasks.loop(minutes=10)
async def update_premium():
    async for entitlement in bot.entitlements:
        if entitlement.sku_id == 1:
            premium_users.append(entitlement.user_id)
        elif entitlement.sku_id == 2:
            premium_guilds.append(entitlement.guild_id)
