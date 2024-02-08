

jacob = 920797181034778655
dev_server_dev_channel = 1165858822183735316
allowed_channels = [dev_server_dev_channel]
mgr_channel = 1168943605205962912
mod_logs = 1169386959303626772
hockey_discord_server = 1165854570195472516
owner = 1165854743281799218
logs = 1168944556927103067
ticketLog = 1193387303381516319

color = 0xffffff
error_channel = 1166019404870463558
footer = "Bot created by @jzcob"


anahiem_ducks_emoji = "<:anaheimducks:1166050853879296030>"
arizona_coyotes_emoji = "<:arizonacoyotes:1166050965451968654>"
boston_bruins_emoji = "<:bostonbruins:1166051078714949692>"
buffalo_sabres_emoji = "<:buffalosabres:1166051476880240660>"
calgary_flames_emoji = "<:calgaryflames:1166051546337923112>"
carolina_hurricanes_emoji = "<:carolinahurricanes:1166051616483455087>"
chicago_blackhawks_emoji = "<:chicagoblackhawks:1178009419968151583>"
colorado_avalanche_emoji = "<:coloradoavalance:1178009564201877514>"
columbus_blue_jackets_emoji = "<:columbusbluejackets:1178009622821474426> "
dallas_stars_emoji = "<:dallasstars:1178009644661231616> "
detroit_red_wings_emoji = "<:detroitredwings:1178010979519438848>"
edmonton_oilers_emoji = "<:edmontonoilers:1178011001153654814> "
florida_panthers_emoji = "<:floridapanthers:1178011019340165281> "
los_angeles_kings_emoji = "<:losangeleskings:1178011041989414952>"
minnesota_wild_emoji = "<:minnesotawild:1178011065632698489>"
montreal_canadiens_emoji = "<:montrealcanadiens:1178011086792958043>"
nashville_predators_emoji = "<:nashvillepredators:1178011107785461860>"
new_jersey_devils_emoji = "<:newjersydevils:1178083568350679170>"
new_york_islanders_emoji = "<:newyorkislanders:1178083587552198758>"
new_york_rangers_emoji = "<:newyorkrangers:1178083606866952202>"
ottawa_senators_emoji = "<:ottawasenators:1178083784420245616>"
philadelphia_flyers_emoji = "<:philadelphiaflyers:1178083819887267930>"
pittsburgh_penguins_emoji = "<:pittsburghpenguins:1178085887968555128>"
san_jose_sharks_emoji = "<:sanjosesharks:1178085931861942363>"
seattle_kraken_emoji = "<:seattlekraken:1181274680955523112>"
st_louis_blues_emoji = "<:stlouisblues:1178085954368589825>"
tampa_bay_lightning_emoji = "<:tampabaylightning:1178085977189793802>"
toronto_maple_leafs_emoji = "<:torontomapleleafs:1178086004616339616>"
vancouver_canucks_emoji = "<:vancouvercanucks:1178086027353665626>"
vegas_golden_knights_emoji = "<:vegasgoldenknights:1178086044931989576>"
washington_capitals_emoji = "<:washingtoncapitals:1178086062518710413>"
winnipeg_jets_emoji = "<:winnipegjets:1178086107418722434>"
nhl_logo_emoji = "<:nhl:1165874790117150820>"

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