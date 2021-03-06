import discord
# import pprint
from discord.ext import commands
from cogs.utils import checks
import aiohttp
from .utils.dataIO import dataIO
import os
import urllib.parse
from __main__ import send_cmd_help
from datetime import datetime, timezone

# Beer: https://untappd.com/beer/<bid>
# Brewery: https://untappd.com/brewery/<bid>
# Checkin: https://untappd.com/c/<checkin>
# prefix = ctx.prefix


class Untappd:
    """Untappd cog that lets the bot look up beer
    information from untappd.com!"""

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json("data/untappd/settings.json")
        if "max_items_in_list" not in self.settings:
            self.settings["max_items_in_list"] = 5
        if "supporter_emoji" not in self.settings:
            self.settings["supporter_emoji"] = ":moneybag:"
        if "moderator_emoji" not in self.settings:
            self.settings["moderator_emoji"] = ":crown:"
        self.session = aiohttp.ClientSession()
        self.channels = {}
        self.emoji = {
                1: "1⃣",
                2: "2⃣",
                3: "3⃣",
                4: "4⃣",
                5: "5⃣",
                6: "6⃣",
                7: "7⃣",
                8: "8⃣",
                9: "9⃣",
                10: "🔟",
                "beers": "🍻",
                "beer": "🍺",
                "comments": "💬",
                "right": "➡",
                "left": "⬅"
        }

    # invaild syntax?
    @commands.group(no_pm=False, invoke_without_command=False,
                    pass_context=True)
    async def groupdrink(self, ctx):
        """Settings for a drinking project"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @groupdrink.command(no_pm=True, pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def sheet_url(self, ctx, url):
        """The published web app URL that accepts GETs and POSTs"""
        try:
            server = ctx.message.server.id
            if server not in self.settings:
                self.settings[server] = {}
            is_pm = False
        except KeyError:
            is_pm = True

        if is_pm:
            await self.bot.say("I cannot set this in PM because it's"
                               " a per-server value")
        else:
            self.settings[server]["project_url"] = url
            dataIO.save_json("data/untappd/settings.json", self.settings)
            await self.bot.say("The project endpoint URL has been set")

    @groupdrink.command(no_pm=True, pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def finish(self, ctx):
        """The published web app URL that accepts GETs and POSTs"""
        try:
            server = ctx.message.server.id
            if server not in self.settings:
                self.settings[server] = {}
            is_pm = False
        except KeyError:
            is_pm = True

        if is_pm:
            await self.bot.say("I cannot set this in PM because it's"
                               " a per-server value")
        else:
            self.settings[server]["project_url"] = ""
            dataIO.save_json("data/untappd/settings.json", self.settings)
            await self.bot.say("The drinking project has been temporarily"
                               " suspended.")

    @commands.group(no_pm=False, invoke_without_command=False,
                    pass_context=True)
    async def untappd(self, ctx):
        """Explicit Untappd things"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @untappd.command(no_pm=True, pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def list_size(self, ctx, new_size: int):
        """The length of lists of resultsm specific to a server now"""
        is_pm = True
        try:
            server = ctx.message.server.id
            if server not in self.settings:
                self.settings[server] = {}
            is_pm = False
        except KeyError:
            is_pm = True
        new_size += 0
        # The true maximum size is 10 because there's that many emoji
        if new_size > 10:
            new_size = 10
            await self.bot.say("Reducing the maximum size to "
                               "10 due to emoji constraints")
        if is_pm:
            self.settings["max_items_in_list"] = new_size
        else:
            self.settings[server]["max_items_in_list"] = new_size
        dataIO.save_json("data/untappd/settings.json", self.settings)
        await self.bot.say("Maximum list size is now {!s}".format(new_size))

    @untappd.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def supporter_emoji(self, emoji: str):
        """The moji to use for supporters"""
        self.settings["supporter_emoji"] = str(emoji)
        dataIO.save_json("data/untappd/settings.json", self.settings)
        await self.bot.say("Profiles of supporters will now display ("
                           + str(emoji) + ")")

    @untappd.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def moderator_emoji(self, emoji: str):
        """The emoji to use for super users"""
        self.settings["moderator_emoji"] = str(emoji)
        dataIO.save_json("data/untappd/settings.json", self.settings)
        await self.bot.say("Profiles of super users will now display ("
                           + str(emoji) + ")")

    @untappd.command(pass_context=True, no_pm=True)
    async def setnick(self, ctx, keywords):
        """Set your untappd user name to use for future commands"""
        # TODO: Replace future commands with the commands
        if not keywords:
            await send_cmd_help(ctx)
        if (ctx.message.server):
            server = ctx.message.server.id
            if server not in self.settings:
                self.settings[server] = {}
            author = ctx.message.author.id
            if author not in self.settings[server]:
                self.settings[server][author] = {}
            self.settings[server][author]["nick"] = keywords
            await self.bot.say("When you look yourself up on untappd"
                               " I will use `" + keywords + "`")
            dataIO.save_json("data/untappd/settings.json", self.settings)
        else:
            await self.bot.say("I was unable to set that for this server")
            # print("Channel type: {!s}".format(ctx.message.channel.type))
            # print("Guild: {!s}".format(ctx.message.server))

    @untappd.command(pass_context=True, no_pm=False)
    async def authme(self, ctx):
        """Starts the authorization process for a user"""
        # TODO: Check if already authorized and confirm to reauth
        auth_url = ("https://untappd.com/oauth/authenticate/?client_id="
                    "{!s}&response_type=token&redirect_url={!s}").format(
                        self.settings["client_id"],
                        "https://aardwolf.github.io/tokenrevealer.html"
                    )
        auth_string = ("Please authenticate with untappd then follow the"
                       " instructions on [this page]"
                       "({!s}) using the proper prefix").format(auth_url)
        embed = embedme(auth_string, title="Authorization")
        disclaimer = ("Following this link and providing the resulting "
                      "token to the bot will allow it to act as you. "
                      "Currently that involves some lookups and all toasts."
                      " Permission can be revoked from the untappd website "
                      "and with the `unauthme` command")
        await self.bot.whisper(disclaimer, embed=embed)

    @untappd.command(pass_context=True, no_pm=False, name="auth-token")
    async def auth_token(self, ctx, keyword):
        """Finishes the authorization process"""
        if not keyword:
            await send_cmd_help(ctx)
        author = ctx.message.author.id
        if author not in self.settings:
            self.settings[author] = {}
        self.settings[author]["token"] = keyword
        try:
            await self.bot.delete_message(ctx.message)
        except BaseException:
            pass
        dataIO.save_json("data/untappd/settings.json", self.settings)
        await self.bot.whisper("Token saved, thank you")

    @untappd.command(pass_context=True, no_pm=False)
    async def unauthme(self, ctx):
        """Removes the authorization token for a user"""
        # TODO: Check if already authorized and confirm to reauth
        author = ctx.message.author.id
        response = ""
        if author in self.settings:
            self.settings[author].pop("token", None)
            response = "Authorization removed"
        else:
            response = "It doesn't look like you were authorized before"
        dataIO.save_json("data/untappd/settings.json", self.settings)
        await self.bot.say(response)

    @untappd.command(pass_context=True, no_pm=False)
    async def friend(self, ctx, profile: str = None):
        """Accepts existing friend requests from user specified or
        sends a friend request to the user specified"""

        keys = getAuth(ctx)
        if "access_token" not in keys:
            await self.bot.say("You must first authorize me to act as you"
                               " using `untappd authme`")
            return

        if ctx.message.server:
            guild = str(ctx.message.server.id)
        else:
            guild = 0

        if not check_credentials(self.settings):
            await self.bot.say("The owner has not set the API information "
                               "and should use the `untappd_apikey` command")
            return

        if ctx.message.mentions:
            # If user has set a nickname, use that - but only if it's not a PM
            if ctx.message.server:
                user = ctx.message.mentions[0]
                try:
                    profile = self.settings[guild][user.id]["nick"]
                except KeyError:
                    profile = user.display_name

        if not profile:
            await self.bot.say("Friend who? Give me a name!")
            return
        await self.bot.send_typing(ctx.message.channel)
        qstr = urllib.parse.urlencode(keys)
        # This will be needed several times
        # First get the UID for the profile
        uid = 0
        url = ("https://api.untappd.com/v4/user/info/{!s}?{!s}"
               ).format(profile, qstr)
        j = await get_data_from_untappd(self, ctx, url)
        if "meta" in j:
            if int(j["meta"]["code"]) == 200:
                if "user" in j['response']:
                    uid = j['response']['user']['uid']
                else:
                    await self.bot.say("Could not look up that user")
                    return
            else:
                await self.bot.say(
                    ("I was unable to look up {!s}: {!s} / {!s}").format(
                        profile, j["meta"]["code"], j["meta"]["error_detail"]
                    ))
                return
        if not uid:
            await self.bot.say("Sorry, I couldn't get a uid for " + profile)
            return
        # Step 2: Accept any pending requests
        url = ("https://api.untappd.com/v4/friend/accept/{!s}?{!s}"
               ).format(uid, qstr)
        j = await get_data_from_untappd(self, ctx, url)
        if "meta" in j:
            if int(j["meta"]["code"]) == 200:
                # This is probably the case where it worked!
                if "target_user" in j['response']:
                    response_str = (
                        "You accepted a friend request from {!s}!"
                        " Now you can toast them and stalk them better."
                        ).format(j['response']['target_user']['user_name'])
                    await self.bot.say(response_str)
                else:
                    response_str = "I think you accepted a request "
                    response_str += "but I didn't get the answer I expected"
                    await self.bot.say(response_str)
                return
        # Send a request. Even if they're already friends
        url = ("https://api.untappd.com/v4/friend/request/{!s}?{!s}"
               ).format(uid, qstr)
        j = await get_data_from_untappd(self, ctx, url)
        if "meta" in j:
            if int(j["meta"]["code"]) == 200:
                response_str = ""
                if "target_user" in j['response']:
                    response_str = (
                        "You sent a request to {!s}. The ball is in "
                        "their court now."
                    ).format(j['response']['target_user']['user_name'])
                else:
                    response_str = (
                        "I think you sent a request but I "
                        "didn't get the response I expected: {!s} / {!s}"
                        ).format(
                            j["meta"]["code"], j["meta"]["error_detail"]
                        )
                await self.bot.say(response_str)
            else:
                if "meta" in j:
                    response_str = (
                        "I got an error sending a request to that person. "
                        "I blame you for that error. (Specifically: {!s})"
                    ).format(j["meta"]["error_detail"])
                else:
                    response_str = "Something went horribly wrong."
                await self.bot.say(response_str)
                # print("{!s}".format(j))

    @commands.command(pass_context=True, no_pm=False)
    async def wishlist(self, ctx, *keywords):
        """Requires that you've authorized the bot.
        Adds a beer to or removes a beer from your wishlist.
        If you privde a beer id, that's used.
        Otherwise it's the first search result
        or the last beer shared in the channel"""

        me = self.bot
        beerid = 0
        if not check_credentials(self.settings):
            await self.bot.say("The owner has not set the API information "
                               "and should use the `untappd_apikey` command")
            return

        keys = getAuth(ctx)
        if "access_token" not in keys:
            await self.bot.say("You must first authorize me to act as you"
                               " using `untappd authme`")
            return

        if keywords:
            keywords = " ".join(keywords)
        else:
            channel = ctx.message.channel.id
            if channel in self.channels:
                if self.channels[channel]:
                    if "beer" in self.channels[channel]:
                        beerid = self.channels[channel]["beer"]
            if not beerid:
                await self.bot.send_cmd_help(ctx)
                return

        await self.bot.send_typing(ctx.message.channel)
        if not beerid and keywords.isdigit():
            beer = await get_beer_by_id(self, ctx, keywords)
            if isinstance(beer, str):
                await self.bot.say("Wishlist add failed - {!s}".
                                   format(beer))
                return
            beerid = keywords
        elif not beerid:
            beers = await searchBeer(self, ctx, keywords, limit=1)
            if isinstance(beers["items"], list) and len(beers["items"]) > 0:
                beerid = beers["items"][0]["beer"]["bid"]
            else:
                await self.bot.say("I'm afraid `{!s}` was not found".format(
                    keywords
                ))

        if beerid:
            # Attempt to add to the wishlist
            if "access_token" not in keys:
                return("You have not authorized the bot to act as you, use"
                       "`untappd authme` to start the process")

            keys["bid"] = beerid
            qstr = urllib.parse.urlencode(keys)
            url = ("https://api.untappd.com/v4/user/wishlist/add?{!s}"
                   ).format(qstr)
            # print("Using URL: {!s}".format(url))

            j = await get_data_from_untappd(self, ctx, url)
            if "meta" in j:
                if int(j["meta"]["code"]) == 200:
                    beer = j['response']['beer']['beer']
                    beer['brewery'] = j['response']['beer']['brewery']
                    embed = beer_to_embed(beer)
                    await me.say("Beer added to wishlist", embed=embed)
                    return
                elif int(j["meta"]["code"]) == 500:
                    url = ("https://api.untappd.com/v4/user/wishlist/"
                           "delete?{!s}").format(qstr)
                    j = await get_data_from_untappd(self, ctx, url)
                    if "meta" in j:
                        if int(j["meta"]["code"]) == 200:
                            beer = j['response']['beer']['beer']
                            beer['brewery'] = j['response']['beer']['brewery']
                            embed = beer_to_embed(beer)
                            await me.say("Beer removed from wishlist",
                                         embed=embed)
                        else:
                            print("That didn't quite work with '" + url + "'")
                            await me.say("I tried adding it, I tried removing"
                                         "it. Nothing I tried worked")
                else:
                    await me.say("Weird, got code {!s}".
                                 format(j["meta"]["code"]))
        else:
            await me.say("I was unable to find such a beer, sorry")

    @commands.command(pass_context=True, no_pm=False)
    async def haveihad(self, ctx, *keywords):
        """Lookup a beer to see if you've had it
        Requires that you've authenticated the bot to act as you"""

        resultStr = ""
        if not check_credentials(self.settings):
            await self.bot.say("The owner has not set the API information "
                               "and should use the `untappd_apikey` command")
            return

        keys = getAuth(ctx)
        if "access_token" not in keys:
            await self.bot.say("You must first authorize me to act as you"
                               " using `untappd authme`")
            return

        if keywords:
            keywords = " ".join(keywords)
        else:
            await self.bot.send_cmd_help(ctx)
            return

        set_beer_id = False
        await self.bot.send_typing(ctx.message.channel)
        if keywords.isdigit():
            beerid = keywords
        else:
            beers = await searchBeer(self, ctx, keywords, limit=1)
            if isinstance(beers, str):
                await self.bot.say(
                    ("Lookup of `{!s}` didn't result in a beer list: {!s}").
                    format(keywords, beers)
                    )
                return
            elif isinstance(beers["items"], list) and len(beers["items"]) > 0:
                beerid = beers["items"][0]["beer"]["bid"]
                set_beer_id = True
            else:
                await self.bot.say(("Lookup of `{!s}` failed. So no, "
                                    "you haven't"
                                    ).format(keywords))
                return

        if beerid:
            beer = await get_beer_by_id(self, ctx, beerid)
            if isinstance(beer, str):
                await self.bot.say(beer)
                return
            if beer["stats"]["user_count"]:
                resultStr += ("You have had '**{!s}**' by **{!s}** {!s} "
                              "time{!s}").format(
                                  beer["beer_name"],
                                  beer["brewery"]["brewery_name"],
                                  beer["stats"]["user_count"],
                                  add_s(beer["stats"]["user_count"])
                              )
                if beer["auth_rating"]:
                    resultStr += " and you gave it {!s} cap{!s}.".format(
                        beer["auth_rating"],
                        add_s(beer["auth_rating"])
                    )
                if set_beer_id:
                    resultStr += " `{!s}findbeer {!s}` to see details.".format(
                        ctx.prefix,
                        beerid
                    )
            else:
                resultStr += ("You have never had '**{!s}**' by **{!s}**"
                              ).format(
                                  beer["beer_name"],
                                  beer["brewery"]["brewery_name"]
                              )
                if beer["stats"]["total_user_count"]:
                    resultStr += (" but {!s} other people have.").format(
                        human_number(beer["stats"]["total_user_count"])
                    )
                if set_beer_id:
                    resultStr += " `{!s}findbeer {!s}` to see details.".format(
                        ctx.prefix,
                        beerid
                    )
        else:
            await self.bot.send_cmd_help(ctx)
            return

        if resultStr:
            await self.bot.say(resultStr)
        else:
            await self.bot.say("You may not have provided a beer ID")

    @commands.command(pass_context=True, no_pm=False)
    async def findbeer(self, ctx, *keywords):
        """Search Untappd.com for a beer. Provide a number and it'll
        look up that beer"""
        embed = False
        beer_list = []
        resultStr = ""
        list_limit = list_size(self, ctx.message.server)

        if not check_credentials(self.settings):
            await self.bot.say("The owner has not set the API information "
                               "and should use the `untappd_apikey` command")
            return

        if keywords:
            keywords = "+".join(keywords)
        else:
            await self.bot.send_cmd_help(ctx)
            return

        await self.bot.send_typing(ctx.message.channel)
        if keywords.isdigit():
            embed = await lookupBeer(self, ctx, keywords, list_size=1)
            # await self.bot.say( embed=embed)
        else:
            results = await searchBeer_to_embed(self, ctx, keywords,
                                                limit=list_limit)
            if isinstance(results, dict):
                embed = results["embed"]
                if "beer_list" in results:
                    beer_list = results["beer_list"]
            else:
                embed = results
            # await self.bot.say(resultStr, embed=embed)

        if isinstance(embed, str):
            message = await self.bot.say(embed)
        elif embed:
            message = await self.bot.say(resultStr, embed=embed)
        else:
            message = await self.bot.say(resultStr)

        if (len(beer_list) > 1):
            await embed_menu(self, ctx, beer_list, message, 30)

    @commands.command(pass_context=True, no_pm=False)
    async def findbeer1(self, ctx, *keywords):
        embed = False
        resultStr = ""
        await self.bot.send_typing(ctx.message.channel)
        results = await searchBeer_to_embed(self, ctx, " ".join(keywords),
                                            limit=1)
        if isinstance(results, dict):
            embed = results["embed"]
            await self.bot.say(resultStr, embed=embed)
        else:
            await self.bot.say(resultStr, embed=results)

    @commands.command(pass_context=True)
    async def lastbeer(self, ctx, profile: str = None):
        """Displays details for the last beer a person had"""

        embed = False
        resultStr = ""
        author = ctx.message.author
        if ctx.message.server:
            guild = str(ctx.message.server.id)
        else:
            guild = 0

        if not check_credentials(self.settings):
            await self.bot.say("The owner has not set the API information "
                               "and should use the `untappd_apikey` command")
            return

#        await self.bot.say("I got a user " + profile)
        if ctx.message.mentions:
            # If user has set a nickname, use that - but only if it's not a PM
            if ctx.message.server:
                user = ctx.message.mentions[0]
                # print("looking up {!s}".format(user.id))
                try:
                    profile = self.settings[guild][user.id]["nick"]
                except KeyError:
                    profile = user.display_name

        if not profile:
            try:
                profile = self.settings[guild][author.id]["nick"]
            except KeyError:
                profile = author.display_name

        await self.bot.send_typing(ctx.message.channel)
        results = await getCheckins(self, ctx, profile=profile, count=1)
        if (isinstance(results, dict)) and ("embed" in results):
            embed = results["embed"]
            await self.bot.say(resultStr, embed=embed)
        else:
            await self.bot.say(results)
        return

    @commands.command(pass_context=True, no_pm=False)
    async def profile(self, ctx, profile: str = None):
        """Search for a user's information by providing their profile name,
        discord mentions OK"""

        embed = False
        beer_list = []
        resultStr = ""
        author = ctx.message.author
        if ctx.message.server:
            guild = str(ctx.message.server.id)
        else:
            guild = 0

        if not check_credentials(self.settings):
            await self.bot.say("The owner has not set the API information "
                               "and should use the `untappd_apikey` command")
            return

        if ctx.message.mentions:
            # If user has set a nickname, use that - but only if it's not a PM
            if ctx.message.server:
                user = ctx.message.mentions[0]
                try:
                    profile = self.settings[guild][user.id]["nick"]
                except KeyError:
                    profile = user.display_name

        if not profile:
            try:
                profile = self.settings[guild][author.id]["nick"]
            except KeyError:
                profile = None
        if not profile:
            profile = author.display_name
            print("Using '{}'".format(profile))
        await self.bot.send_typing(ctx.message.channel)
        results = await profileLookup(self, ctx, profile,
                                      limit=list_size(self,
                                                      ctx.message.server))
        if isinstance(results, dict):
            if "embed" in results:
                embed = results["embed"]
            if "beer_list" in results:
                beer_list = results["beer_list"]
        else:
            resultStr = results
        if embed:
            message = await self.bot.say(resultStr, embed=embed)
        else:
            message = await self.bot.say(resultStr)
        if len(beer_list) > 1:
            await embed_menu(self, ctx, beer_list, message, 30, type="checkin")
        return

    @untappd.command(pass_context=True, no_pm=False)
    @checks.is_owner()
    async def untappd_apikey(self, ctx, *keywords):
        """Sets the id and secret that you got from applying for
            an untappd api"""
        if len(keywords) == 2:
            self.settings["client_id"] = keywords[0]
            self.settings["client_secret"] = keywords[1]
            self.settings["CONFIG"] = True
            dataIO.save_json("data/untappd/settings.json", self.settings)
            await self.bot.say("API set")
        else:
            await self.bot.say("I am expecting two words, the id and "
                               "the secret only")

    @commands.command(pass_context=True, no_pm=False)
    async def toast(self, ctx, *keywords):
        """Toasts a checkin by number, if you're friends"""

        author = ctx.message.author
        auth_token = None
        checkin = 0

        if not check_credentials(self.settings):
            await self.bot.say("The owner has not set the API information "
                               "and should use the `untappd_apikey` command")
            return

        if author.id in self.settings:
            if "token" in self.settings[author.id]:
                auth_token = self.settings[author.id]["token"]

        if not auth_token:
            await self.bot.say(("Unable to toast until you have "
                                "authenticated me using `untappd authme`"))
            return

        for word in keywords:
            # print("Checking " + word)
            if word.isdigit():
                checkin = int(word)

        if not checkin:
            channel = ctx.message.channel.id
            if channel in self.channels:
                if self.channels[channel]:
                    if "checkin" in self.channels[channel]:
                        checkin = self.channels[channel]["checkin"]

        if not checkin:
            await self.bot.say("I haven't seen a checkin for this channel "
                               "since my last start. You'll have to tell me "
                               "which to toast.")
            return

        embed = await toastIt(self, ctx, checkin=checkin,
                              auth_token=auth_token)
        if isinstance(embed, str):
            await self.bot.say(embed)
        else:
            await self.bot.say("", embed=embed)

    @commands.command(pass_context=True, no_pm=False)
    async def checkin(self, ctx, *keywords):
        """Returns a single checkin by number"""

        author = ctx.message.author
        auth_token = None
        checkin = 0

        if not check_credentials(self.settings):
            await self.bot.say("The owner has not set the API information "
                               "and should use the `untappd_apikey` command")
            return

        if author.id in self.settings:
            if "token" in self.settings[author.id]:
                auth_token = self.settings[author.id]["token"]

        for word in keywords:
            # print("Checking " + word)
            if word.isdigit():
                checkin = int(word)

        if not checkin:
            await self.bot.say("A checkin ID number is required")
            return

        await self.bot.send_typing(ctx.message.channel)
        embed = await getCheckin(self, ctx, checkin=checkin,
                                 auth_token=auth_token)
        if isinstance(embed, str):
            await self.bot.say(embed)
        else:
            await self.bot.say("", embed=embed)

    @commands.command(pass_context=True, no_pm=False)
    async def checkins(self, ctx, *keywords):
        """Returns a list of checkins"""

        embed = None
        profile = ""
        startnum = 0
        author = ctx.message.author
        if ctx.message.server:
            guild = str(ctx.message.server.id)
        else:
            guild = 0
        checkin_list = []
        resultStr = ""
        countnum = list_size(self, server=ctx.message.server)
        # determine if a profile or number was given
        if not check_credentials(self.settings):
            await self.bot.say("The owner has not set the API information "
                               "and should use the `untappd_apikey` command")
            return

        # If a keyword was provided and it's all digits then look up that one
        # Looks like there is no way to look up by id alone

        if ctx.message.mentions:
            # If user has set a nickname, use that - but only if it's not a PM
            if ctx.message.server:
                user = ctx.message.mentions[0]
                try:
                    profile = self.settings[guild][user.id]["nick"]
                except KeyError:
                    profile = user.display_name

        # The way the API works you can provide a checkin number and limit
        for word in keywords:
            # print("Checking " + word)
            if word.isdigit():
                startnum = int(word)
                countnum = 1
            elif not profile:
                profile = word
        if not profile:
            try:
                profile = self.settings[guild][author.id]["nick"]
            except KeyError:
                profile = None
        if not profile:
            profile = author.display_name

        if countnum > 50:
            countnum = 50
        if countnum < 1:
            countnum = 1
        # print(dir(ctx.message.content))
        # print(dir(ctx.command))
        # print("{!s}".format(ctx.command.invoke))
        # if ctx.command.name == "lastbeer":
        #     countnum = 1

        await self.bot.send_typing(ctx.message.channel)
        results = await getCheckins(self, ctx, profile=profile,
                                    start=startnum, count=countnum)
        if isinstance(results, dict):
            if "embed" in results:
                embed = results["embed"]
            if "list" in results:
                checkin_list = results["list"]
        else:
            resultStr = results
        if embed:
            message = await self.bot.say(resultStr, embed=embed)
        else:
            message = await self.bot.say(resultStr)
        if len(checkin_list) > 1:
            await embed_menu(self, ctx, checkin_list, message, 30,
                             type="checkin")
        return

    @commands.command(pass_context=True, no_pm=False)
    async def ifound(self, ctx, *keywords):
        """Add a found beer to the spreadsheet. Beer id or search"""

        author = ctx.message.author
        if ctx.message.server:
            guild = str(ctx.message.server.id)
            if "project_url" in self.settings[guild]:
                url = self.settings[guild]["project_url"]
            try:
                profile = self.settings[guild][author.id]["nick"]
            except KeyError:
                profile = author.display_name
        else:
            profile = author.display_name

        if keywords:
            keywords = " ".join(keywords)
        else:
            await self.bot.send_cmd_help(ctx)
            return

        await self.bot.send_typing(ctx.message.channel)
        if keywords.isdigit():
            beerid = keywords
        else:
            beers = await searchBeer(self, ctx, keywords, limit=1)
            if isinstance(beers, str):
                await self.bot.say(
                    ("Lookup of `{!s}` didn't result in a beer list: {!s}").
                    format(keywords, beers)
                    )
                return
            elif isinstance(beers["items"], list) and len(beers["items"]) > 0:
                beerid = beers["items"][0]["beer"]["bid"]
            else:
                await self.bot.say(("Lookup of `{!s}` failed. So no, "
                                    "you haven't"
                                    ).format(keywords))
                return

        if beerid:
            beer = await get_beer_by_id(self, ctx, beerid)
            if isinstance(beer, str):
                await self.bot.say(beer)
                return

        if not url:
            await self.bot.say("Looks like there are no projects right now")
            return
        beer = await get_beer_by_id(self, ctx, beerid)
        if (isinstance(beer, str)):
            # This happens in error situations
            await self.bot.say(beer)
            return
        keys = {
            "bid": beerid,
            "username": profile,
            "beer_name": "{!s} from {!s}".format(
                beer["beer_name"], beer["brewery"]["brewery_name"]
                )
        }
        qstr = urllib.parse.urlencode(keys)
        url += "?{!s}".format(qstr)
        async with self.session.get(url) as resp:
            if resp.status == 200:
                j = await resp.json()
            else:
                return "Query failed with code " + str(resp.status)

            if j['result'] == "success":
                embed = await lookupBeer(self, ctx, beerid)
                if not embed:
                    await self.bot.say("{!s} added!".format(keys["beer_name"]))
                else:
                    await self.bot.say("{!s} added!".format(keys["beer_name"]),
                                       embed=embed)
            else:
                await self.bot.say("Something went wrong adding the beer")

    @commands.command(pass_context=True, no_pm=False)
    async def ddp(self, ctx, checkin_id: int = 0):
        """Add a checkin to the spreadsheet. Defaults to last one"""

        author = ctx.message.author
        url = ""
        if ctx.message.server:
            guild = str(ctx.message.server.id)
            if "project_url" in self.settings[guild]:
                url = self.settings[guild]["project_url"]
            try:
                profile = self.settings[guild][author.id]["nick"]
            except KeyError:
                profile = author.display_name
        else:
            profile = author.display_name

        auth_token = None
        if author.id in self.settings:
            if "token" in self.settings[author.id]:
                auth_token = self.settings[author.id]["token"]

        await self.bot.send_typing(ctx.message.channel)
        if not url:
            await self.bot.say("Looks like there are no projects right now")
            return

        # Get the information needed for the form, starting with checkin id
        # checkin id	style	beer id	beer name	avg rating
        # brewery id	brewery	username	rating	comment
        if not checkin_id or checkin_id <= 0:
            checkin_url = (
                "https://api.untappd.com/v4/user/checkins/{!s}".format(
                    profile))
            keys = dict()
            keys["client_id"] = self.settings["client_id"]
            if auth_token:
                keys["access_token"] = auth_token
                # print("Doing an authorized lookup")
            else:
                keys["client_secret"] = self.settings["client_secret"]
            keys["limit"] = 1
            qstr = urllib.parse.urlencode(keys)
            checkin_url += "?{!s}".format(qstr)
            j = await get_data_from_untappd(self, ctx, checkin_url)
            if j["meta"]["code"] != 200:
                # print("Lookup failed for url: "+url)
                await self.bot.say("Lookup failed with {!s} - {!s}").format(
                    j["meta"]["code"],
                    j["meta"]["error_detail"]
                    )
                return

            if isinstance(j["response"]["checkins"]["items"], list):
                checkin = j["response"]["checkins"]["items"][0]
            else:
                await self.bot.say("Things seem to work but I did not get"
                                   "a list of checkins")
                return
        else:
            # The case where a checkin id was provided
            keys = dict()
            keys["client_id"] = self.settings["client_id"]
            if auth_token:
                keys["access_token"] = auth_token
                # print("Doing an authorized lookup")
            else:
                keys["client_secret"] = self.settings["client_secret"]
            qstr = urllib.parse.urlencode(keys)
            checkin_url = ("https://api.untappd.com/v4/checkin/view/"
                           "{!s}?{!s}").format(
                checkin_id, qstr
            )

            j = await get_data_from_untappd(self, ctx, checkin_url)
            if j["meta"]["code"] != 200:
                # print("Lookup failed for url: "+url)
                await self.bot.say("Lookup failed with {!s} - {!s}").format(
                    j["meta"]["code"],
                    j["meta"]["error_detail"])
                return

            checkin = j["response"]["checkin"]

        checkin_id = checkin["checkin_id"]
        style = checkin["beer"]["beer_style"]
        beer_id = checkin["beer"]["bid"]
        beer_name = checkin["beer"]["beer_name"]
        brewery_id = checkin["brewery"]["brewery_id"]
        brewery = checkin["brewery"]["brewery_name"]
        username = checkin["user"]["user_name"]
        rating = checkin["rating_score"]
        comment = checkin["checkin_comment"]
        checkin_date = checkin["created_at"]

        beer = await get_beer_by_id(self, ctx, beer_id)
        avg_rating = beer["rating_score"]
        total_checkins = beer["stats"]["total_user_count"]

        payload = {
            "action": "drank",
            "checkin": checkin_id,
            "style": style,
            "bid": beer_id,
            "beer_name": beer_name,
            "brewery_id": brewery_id,
            "brewery": brewery,
            "username": username,
            "rating": rating,
            "avg_rating": avg_rating,
            "total_checkins": total_checkins,
            "checkin_date": checkin_date,
            "comment": comment
        }
        async with self.session.post(url, data=payload) as resp:
            if resp.status == 200:
                j = await resp.json()
            else:
                return "Query failed with code " + str(resp.status)

            if j['result'] == "success":
                embed = await getCheckin(self, ctx,
                                         checkin=checkin_id,
                                         auth_token=auth_token)
                if embed:
                    await self.bot.say("Checkin {!s} added!"
                                       .format(checkin_id),
                                       embed=embed)
                else:
                    await self.bot.say("Checkin {!s} added!"
                                       .format(checkin_id))
            else:
                await self.bot.say("Something went wrong adding the checkin")

    @commands.command(pass_context=True, no_pm=True)
    async def undrank(self, ctx, checkin_id: int):
        """Removes a checkin from the spreadsheet. Use ddp to add it back"""

        if ctx.message.server:
            guild = str(ctx.message.server.id)
            if "project_url" in self.settings[guild]:
                url = self.settings[guild]["project_url"]
        else:
            await self.bot.say("This does not work in PM")

        await self.bot.send_typing(ctx.message.channel)
        if not url:
            await self.bot.say("Looks like there are no projects right now")
            return

        payload = {
            "action": "undrank",
            "checkin": checkin_id,
        }
        async with self.session.post(url, data=payload) as resp:
            if resp.status == 200:
                j = await resp.json()
            else:
                return "Query failed with code " + str(resp.status)

            if j['result'] == "success":
                await self.bot.say(("Checkin {!s} removed from the scoreboard"
                                    " if it existed").format(checkin_id)
                                   )
            else:
                await self.bot.say("Something went wrong adding the checkin")
                print(j)


def check_folders():
    if not os.path.exists("data/untappd"):
        print("Creating untappd folder")
        os.makedirs("data/untappd")


def check_files():
    f = "data/untappd/settings.json"
    data = {"CONFIG": False,
            "max_items_in_list": 5,
            "supporter_emoji": ":moneybag:",
            "moderator_emoji": ":crown:"
            }
    if not dataIO.is_valid_json(f):
        dataIO.save_json(f, data)
    else:
        temp_settings = dataIO.load_json("data/untappd/settings.json")
        modified = False
        if "client_id" in temp_settings:
            temp_settings["CONFIG"] = True
            modified = True
        if "max_items_in_list" not in temp_settings:
            temp_settings["max_items_in_list"] = 5
            modified = True

        if modified:
            dataIO.save_json(f, temp_settings)


def check_credentials(settings):
    """Confirms bot owner set credentials"""
    if "client_id" not in settings:
        return False

    if "client_secret" not in settings:
        return False

    return True


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Untappd(bot))


def getAuth(ctx):
    """Returns auth dictionary given a context"""

    keys = {}
    # settings = ctx.bot.cogs['Untappd'].settings
    settings = ctx.cog.settings
    author = ctx.message.author
    keys["client_id"] = settings["client_id"]
    if author.id in settings:
        if "token" in settings[author.id]:
            keys["access_token"] = settings[author.id]["token"]

    if "access_token" not in keys:
        keys["client_secret"] = settings["client_secret"]
    return keys


async def get_beer_by_id(self, ctx, beerid):
    """Use the untappd API to return a beer dict for a beer id"""

    keys = getAuth(ctx)
    qstr = urllib.parse.urlencode(keys)
    url = "https://api.untappd.com/v4/beer/info/{!s}?{!s}".format(
        beerid, qstr
    )
    resp = await get_data_from_untappd(self, ctx, url)
    if resp['meta']['code'] == 200:
        return resp['response']['beer']
    else:
        return ("Query failed with code {!s}: {!s}").format(
            resp['meta']['code'],
            resp['meta']['error_detail']
        )


async def lookupBeer(self, ctx, beerid: int, rating=None, list_size=5):
    """Look up a beer by id, returns an embed"""

    beer = await get_beer_by_id(self, ctx, beerid)
    if not beer:
        return embedme("Problem looking up a beer by id")
    elif isinstance(beer, str):
        return embedme(beer)
    embed = beer_to_embed(beer)
    channel = ctx.message.channel.id
    if channel not in self.channels:
        self.channels[channel] = {}
    self.channels[channel]["beer"] = beer["bid"]
    return embed


def beer_to_embed(beer, rating=None, list_size=5):
    """Takes a beer json respons object and returns an embed"""
    if 'bid' not in beer:
        return embedme("No bid, didn't look like a beer")
    beerid = beer['bid']
    beer_url = "https://untappd.com/b/{}/{!s}".format(
        beer['beer_slug'],
        beer['bid'])
    brewery_url = "https://untappd.com/brewery/{!s}".format(
        beer['brewery']['brewery_id'])
    beer_title = beer['beer_name']
    if 'created_at' in beer:
        beerTS = datetime.strptime(beer["created_at"],
                                   "%a, %d %b %Y %H:%M:%S %z")
    else:
        beerTS = datetime.now(timezone.utc)
    embed = discord.Embed(title=beer_title,
                          description=beer['beer_description'][:2048],
                          url=beer_url,
                          timestamp=beerTS)
    embed.set_author(name=beer['brewery']['brewery_name'],
                     url=brewery_url,
                     icon_url=beer['brewery']['brewery_label'])
    embed.add_field(name="Brewery Home",
                    value=brewery_location(beer['brewery']))
    embed.add_field(name="Style", value=beer['beer_style'],
                    inline=True)
    try:
        rating_str = "{!s} Caps ({})".format(
            round(beer['rating_score'], 2),
            human_number(beer['rating_count']))
    except Exception:
        rating_str = "Unknown"
    rating_title = "Rating"
    if beer["auth_rating"]:
        rating_title += " ({!s})".format(beer["auth_rating"])
    embed.add_field(name=rating_title, value=rating_str, inline=True)
    embed.add_field(name="ABV", value=beer['beer_abv'], inline=True)
    embed.add_field(name="IBU", value=beer['beer_ibu'], inline=True)
    if rating:
        embed.add_field(name="Checkin Rating",
                        value=str(rating),
                        inline=True)
    embed.set_thumbnail(url=beer['beer_label'])
    if 'stats' in beer:
        stats_str = "{!s} checkins from {!s} users".format(
            human_number(beer["stats"]["total_count"]),
            human_number(beer["stats"]["total_user_count"])
        )
        if beer["stats"]["monthly_count"]:
            stats_str += " ({!s} this month)".format(
                human_number(beer["stats"]["monthly_count"])
            )
        stats_title = "Stats"
        if beer["stats"]["user_count"]:
            stats_title += " (You: {!s})".format(
                human_number(beer["stats"]["user_count"])
            )
        embed.add_field(name=stats_title, value=stats_str, inline=True)
    last_seen = "Never"
    if 'checkins' in beer:
        if beer["checkins"]["count"]:
            last_seen = time_ago(beer["checkins"]["items"][0]["created_at"],
                                 long=True)
        embed.add_field(name="Last Seen", value=last_seen, inline=True)

    footer_str = "Beer {!s} ".format(beerid)
    prod_str = ""
    if not beer["is_in_production"]:
        prod_str = "Not in production"
    footer_str = footer_str + prod_str
    embed.set_footer(text=footer_str)

    if "collaborations_with" in beer:
        collabStr = ""
        collabs = beer['collaborations_with']['items']
        for collab in collabs:
            collabStr += "[" + collab['brewery']['brewery_name']
            collabStr += "](https://untappd.com/brewery/"
            collabStr += str(collab['brewery']['brewery_id']) + ")\n"
        embed.add_field(name="Collaboration with", value=collabStr)
    return embed


async def toastIt(self, ctx, checkin: int, auth_token: str = None):
    """Toast a specific checkin"""

    keys = getAuth(ctx)
    # keys["client_id"] = self.settings["client_id"]
    # keys["access_token"] = auth_token
    if "access_token" not in keys:
        return("You have not authorized the bot to act as you, use"
               "`untappd authme` to start the process")

    qstr = urllib.parse.urlencode(keys)
    url = ("https://api.untappd.com/v4/checkin/toast/{!s}?{!s}").format(
        checkin, qstr
    )
    # print("Using URL: {!s}".format(url))

    resp = await get_data_from_untappd(self, ctx, url)
    if resp['meta']['code'] == 500:
        return ("Toast failed, probably because you "
                "aren't friends with this person. Fix this by using "
                "`untappd friend <person>`")
    elif resp["meta"]["code"] == 200:
        if "result" in resp["response"]:
            if resp["response"]["result"] == "success":
                if resp["response"]["like_type"] == "toast":
                    return "Toasted {!s}!".format(checkin)
                elif resp["response"]["like_type"] == "un-toast":
                    return "Toast rescinded from {!s}!".format(checkin)
        else:
            return "Toast failed for some reason"
    else:
        # print("Lookup failed for url: "+url)
        return ("Toast failed with {!s} - {!s}").format(
            resp["meta"]["code"],
            resp["meta"]["error_detail"])


async def getCheckin(self, ctx, checkin: int, auth_token: str = None):
    """Look up a specific checkin"""

    keys = dict()
    keys["client_id"] = self.settings["client_id"]
    if auth_token:
        keys["access_token"] = auth_token
        # print("Doing an authorized lookup")
    else:
        keys["client_secret"] = self.settings["client_secret"]
    qstr = urllib.parse.urlencode(keys)
    url = ("https://api.untappd.com/v4/checkin/view/{!s}?{!s}").format(
        checkin, qstr
    )

    resp = await get_data_from_untappd(self, ctx, url)
    if resp['meta']['code'] != 200:
        # print("Lookup failed for url: "+url)
        return ("Lookup failed with {!s} - {!s}").format(
            resp["meta"]["code"],
            resp["meta"]["error_detail"])

    if "response" in resp:
        if "checkin" in resp["response"]:
            user_checkin = resp["response"]["checkin"]
            return await checkin_to_embed(self, ctx, user_checkin)
    return embedme("Unplanned for error looking up checkin")


async def getCheckins(self, ctx, profile: str = None,
                      start: int = None, count: int = 0):
    """Given some information get checkins of a user"""
    # Sanitize our inputs
    if ctx.message.server:
        guild = str(ctx.message.server.id)
    else:
        guild = 0
    embed = None
    checkinList = []
    if not profile:
        return "No profile was provided or calculated"
    if not count:
        try:
            count = self.settings[guild]["max_items_in_list"]
        except KeyError:
            count = self.settings["max_items_in_list"]

    keys = getAuth(ctx)
    if count:
        keys["limit"] = count
    if start:
        keys["max_id"] = start
    keys["client_id"] = self.settings["client_id"]
    qstr = urllib.parse.urlencode(keys)
    url = ("https://api.untappd.com/v4/user/checkins/{!s}?{!s}").format(
        profile, qstr
    )
    # print("Looking up: {!s}".format(url))
    resp = await get_data_from_untappd(self, ctx, url)
    if resp["meta"]["code"] != 200:
        # print("Lookup failed for url: "+url)
        return ("Lookup failed with {!s} - {!s}").format(
            resp["meta"]["code"],
            resp["meta"]["error_detail"]
            )

    if resp["response"]["checkins"]["count"] == 1:
        embed = await checkin_to_embed(
            self, ctx, resp["response"]["checkins"]["items"][0])
    elif resp["response"]["checkins"]["count"] > 1:
        checkins = resp["response"]["checkins"]["items"]
        checkinStr = checkins_to_string(self, count, checkins)
        checkinList = checkins
        embed = discord.Embed(title=profile, description=checkinStr[:2048])

    result = dict()
    result["embed"] = embed
    if checkinList:
        result["list"] = checkinList
    return result


async def searchBeer(self, ctx, query, limit=None, rating=None):
    """Given a query string and some other
    information returns an embed of results"""

    keys = getAuth(ctx)
    keys["q"] = query
    keys["limit"] = limit
    qstr = urllib.parse.urlencode(keys)

    url = "https://api.untappd.com/v4/search/beer?%s" % qstr
#    print(url)
    resp = await get_data_from_untappd(self, ctx, url)
    if resp["meta"]["code"] == 200:
        return resp['response']['beers']
    else:
        return ("Search for `{!s}` resulted in {!s}: {!s}".
                format(query, resp["meta"]["code"],
                       resp["meta"]["error_detail"]))


async def searchBeer_to_embed(self, ctx, query, limit=None, rating=None):
    """Searches for a beer and returns an embed"""
    beers = await searchBeer(self, ctx, query, limit, rating)
    if isinstance(beers, str):
        # I'm not sure what happens when a naked embed gets returned.
        # return embedme(beers)
        return beers

    returnStr = ""
    list_limit = limit or list_size(ctx.cog, None)
    resultStr = "Your search returned {!s} beers:\n".format(
        beers["count"]
    )
    beer_list = []
    if beers['count'] == 1:
        return await lookupBeer(
            ctx.cog, ctx,
            beers['items'][0]['beer']['bid'],
            list_size=limit)
    elif beers['count'] > 1:
        firstnum = 1

        beers = beers['items']
        for num, beer in zip(range(list_limit),
                             beers):
            resultStr += ctx.cog.emoji[num+1] + " "
            resultStr += str(beer['beer']['bid']) + ". ["
            resultStr += beer['beer']['beer_name'] + "]"
            resultStr += "(" + "https://untappd.com/beer/"
            resultStr += str(beer['beer']['bid']) + ") "
            brewery = ("by *[{!s}](https://untappd.com/w/"
                       "{!s}/{!s})*").format(
                        beer['brewery']['brewery_name'],
                        beer['brewery']['brewery_slug'],
                        beer['brewery']['brewery_id'])
            resultStr += brewery
            if beer['beer']['auth_rating']:
                resultStr += " ({!s})".format(
                    beer['beer']['auth_rating']
                )
            elif beer['have_had']:
                resultStr += " (\\*)"
            resultStr += "\n"
            beer_list.append(beer['beer']['bid'])
            if firstnum == 1:
                firstnum = beer['beer']['bid']

        resultStr += "Look up a beer with `findbeer "
        resultStr += str(firstnum) + "`"
    else:
        returnStr += "no beers"
        # print(json.dumps(j, indent=4))

    embed = discord.Embed(title=returnStr, description=resultStr[:2048])
    result = dict()
    result["embed"] = embed
    if beer_list:
        result["beer_list"] = beer_list
    return (result)


async def profileLookup(self, ctx, profile, limit=5):
    """Looks up a profile in untappd by username"""
    query = urllib.parse.quote_plus(profile)
    embed = False
    beerList = []
    api_key = "client_id={}&client_secret={}".format(
        self.settings["client_id"],
        self.settings["client_secret"])

    url = "https://api.untappd.com/v4/user/info/" + query + "?" + api_key
    # print("Profile URL: " + url) #TODO: Add debug setting

    # TODO: Honor is_private flag on private profiles.

    resp = await get_data_from_untappd(self, ctx, url)
    if resp["meta"]["code"] == 400:
        return "The profile '{!s}' does not exist".format(profile)
    elif resp['meta']['code'] == 200:
        (embed, beerList) = user_to_embed(self, resp['response']['user'],
                                          limit)
    else:
        return "Profile query failed with code {!s} - {!s}".format(
            resp["meta"]["code"], resp["meta"]["error_detail"])

    result = dict()
    result["embed"] = embed
    if beerList:
        result["beer_list"] = beerList
    return result


def user_to_embed(self, user, limit=5):
    """Takes the user portion of a json response and returns an embed \
and a checkin list"""
    beerList = []
    if 'checkins' in user:
        recentStr = checkins_to_string(self, limit,
                                       user['checkins']['items'])
        beerList = user['checkins']['items']
    name_str = user['user_name']
    flair_str = ""
    if user['is_supporter']:
        flair_str += self.settings["supporter_emoji"]
    if user['is_moderator']:
        flair_str += self.settings["moderator_emoji"]
    embed = discord.Embed(title=name_str,
                          description=recentStr[:2048]
                          or "No recent beers visible",
                          url=user['untappd_url'])
    embed.add_field(
        name="Checkins",
        value=str(user['stats']['total_checkins']),
        inline=True)
    embed.add_field(
        name="Uniques",
        value=str(user['stats']['total_beers']),
        inline=True)
    embed.add_field(
        name="Badges",
        value=str(user['stats']['total_badges']),
        inline=True)
    if (("bio" in user)
            and (user['bio'])):
        embed.add_field(name="Bio",
                        value=user['bio'][:1024],
                        inline=False)
    if user['location']:
        embed.add_field(name="Location",
                        value=user['location'],
                        inline=True)
    if flair_str:
        embed.add_field(name="Flair",
                        value=flair_str,
                        inline=True)
    embed.set_thumbnail(url=user['user_avatar'])
    return (embed, beerList)


async def embed_menu(self, ctx, beer_list: list, message, timeout: int = 30,
                     type: str = "beer", paging: bool = False):
    """Says the message with the embed and adds menu for reactions"""
    emoji = []
    limit = list_size(self, ctx.message.server)

    if not message:
        await self.bot.say("I didn't get a handle to an existing message.")
        return

    for num, beer in zip(range(1, limit+1), beer_list):
        emoji.append(self.emoji[num])
        await self.bot.add_reaction(message, self.emoji[num])

    react = await self.bot.wait_for_reaction(
        message=message, timeout=timeout, emoji=emoji, user=ctx.message.author)
    if react is None:
        try:
            try:
                await self.bot.clear_reactions(message)
            except discord.Forbidden:
                for e in emoji:
                    await self.bot.remove_reaction(message, e, self.bot.user)
        except discord.Forbidden:
            pass
        return None
    reacts = {v: k for k, v in self.emoji.items()}
    react = reacts[react.reaction.emoji]
    react -= 1
    if len(beer_list) > react:
        if type == "beer":
            new_embed = await lookupBeer(self, ctx,
                                         beer_list[react], list_size=1)
        elif type == "checkin":
            new_embed = await checkin_to_embed(self, ctx, beer_list[react])
        await self.bot.say(embed=new_embed)
        try:
            try:
                await self.bot.clear_reactions(message)
            except discord.Forbidden:
                for e in emoji:
                    await self.bot.remove_reaction(message, e, self.bot.user)
        except discord.Forbidden:
            pass


def checkins_to_string(self, count: int, checkins: list):
    """Takes a list of checkins and returns a string"""
    checkinStr = ("**checkin** - **beerID** - **beer (caps)**\n\t**brewery**"
                  " - **badges** - **when**\n")
    for num, checkin in zip(range(count), checkins):
        checkinStr += ("{!s}{!s} - {!s} - "
                       "[{!s}](https://untappd.com/beer/{!s})"
                       " ({!s})\n by [{!s}]"
                       "(https://untappd.com/brewery/{!s})"
                       ).format(
                    self.emoji[num+1],
                    checkin["checkin_id"],
                    checkin["beer"]["bid"],
                    checkin["beer"]["beer_name"],
                    checkin["beer"]["bid"],
                    checkin["rating_score"] or "N/A",
                    checkin["brewery"]["brewery_name"],
                    checkin["brewery"]["brewery_id"]
                )
        if checkin["badges"]["count"]:
            checkinStr += " - {!s} badge{!s}".format(
                checkin["badges"]["count"],
                add_s(checkin["badges"]["count"])
                )
        checkinStr += " - {!s}\n".format(time_ago(checkin["created_at"]))
    return checkinStr


async def checkin_to_embed(self, ctx, checkin):
    """Given a checkin object return an embed of that checkin's information"""

    # Get the base beer information
    beer = await get_beer_by_id(self, ctx, checkin["beer"]["bid"])
    # titleStr = "Checkin {!s}".format(checkin["checkin_id"])
    url = ("https://untappd.com/user/{!s}/checkin/{!s}").format(
        checkin["user"]["user_name"],
        checkin["checkin_id"]
        )
    titleStr = ("{!s} was drinking a {!s} by {!s}").format(
                   checkin["user"]["first_name"],
                   checkin["beer"]["beer_name"],
                   checkin["brewery"]["brewery_name"]
               )
    checkinTS = datetime.strptime(checkin["created_at"],
                                  "%a, %d %b %Y %H:%M:%S %z")

    embed = discord.Embed(title=titleStr,
                          description=beer["beer_description"][:2048],
                          url=url, timestamp=checkinTS)
    if checkin["media"]["count"] >= 1:
        embed.set_thumbnail(
            url=checkin["media"]["items"][0]["photo"]["photo_img_md"]
            )
    # Add fields of interest
    beer_link = "[{!s}](https://untappd.com/beer/{!s})".format(
        checkin["beer"]["beer_name"],
        checkin["beer"]["bid"]
    )
    embed.add_field(name="Beer", value=beer_link)
    brewery_link = "[{!s}](https://untappd.com/brewery/{!s})".format(
        checkin["brewery"]["brewery_name"],
        checkin["brewery"]["brewery_id"]
    )
    brewery_link += " in {!s}".format(
        brewery_location(checkin["brewery"]))
    embed.add_field(name="Brewery", value=brewery_link)
    if isinstance(checkin["venue"], dict):
        venueStr = "[{!s}](https://untappd.com/venue/{!s})".format(
            checkin["venue"]["venue_name"],
            checkin["venue"]["venue_id"]
        )
        embed.add_field(name="Venue", value=venueStr)
    titleStr = "Rating"
    if checkin["rating_score"]:
        titleStr += " - {!s}".format(checkin["rating_score"])
    ratingStr = "**{!s}** Average ({!s})".format(
        round(beer['rating_score'], 2),
        human_number(beer['rating_count'])
    )
    embed.add_field(name=titleStr, value=ratingStr)
    embed.add_field(name="Style", value=beer["beer_style"])
    embed.add_field(name="ABV", value=(beer["beer_abv"] or "N/A"))
    embed.add_field(name="IBU", value=(beer["beer_ibu"] or "N/A"))
    checkinStr = "{!s} checkins from {!s} users".format(
        human_number(beer["stats"]["total_count"]),
        human_number(beer["stats"]["total_user_count"])
    )
    embed.add_field(name="Checkins", value=checkinStr)
    if "collaborations_with" in beer:
        collabStr = ""
        collabs = beer['collaborations_with']['items']
        for collab in collabs:
            collabStr += "[" + collab['brewery']['brewery_name']
            collabStr += "](https://untappd.com/brewery/"
            collabStr += str(collab['brewery']['brewery_id']) + ")\n"
        embed.add_field(name="Collaboration with", value=collabStr)
    if checkin["checkin_comment"]:
        embed.add_field(name="Comment",
                        value=checkin["checkin_comment"][:1024])
    if (checkin["comments"]["count"] + checkin["toasts"]["count"]) > 0:
        newValue = "{!s}({!s}){!s}({!s})".format(
                self.emoji["comments"],
                checkin["comments"]["count"],
                self.emoji["beers"],
                checkin["toasts"]["count"]
        )
        embed.add_field(name="Flags", value=newValue)
    if checkin["badges"]["count"] > 0:
        badgeStr = ""
        for badge in checkin["badges"]["items"]:
            badgeStr += "{!s}\n".format(badge["badge_name"])
        embed.add_field(name="Badges", value=badgeStr[:1024])

    embed.set_footer(text="Checkin {!s} / Beer {!s}"
                     .format(checkin["checkin_id"],
                             checkin["beer"]["bid"]))
    channel = ctx.message.channel.id
    if channel not in self.channels:
        self.channels[channel] = {}
    self.channels[channel]["checkin"] = checkin["checkin_id"]
    self.channels[channel]["beer"] = checkin["beer"]["bid"]

    return embed


def list_size(self, server=None):
    """Returns a list size if configured for the server or the default size"""
    size = self.settings["max_items_in_list"]
    if server:
        try:
            size = self.settings[server.id]["max_items_in_list"]
        except KeyError:
            size = self.settings["max_items_in_list"]
    return size


def embedme(errorStr, title="Error encountered"):
    """Returns an embed object with the error string provided"""
    embed = discord.Embed(title=title,
                          description=errorStr[:2048])
    return embed


def human_number(number):
    # Billion, Million, K, end
    number = int(number)
    if number > 1000000000:
        return str(round(number / 1000000000, 1)) + "B"
    elif number > 1000000:
        return str(round(number / 1000000, 1)) + "M"
    elif number > 1000:
        return str(round(number / 1000, 1)) + "K"
    else:
        return str(number)


def time_ago(time_str, long=False):
    """Turns a time string into a string of how long ago a thing was"""

    return_str = "unknown ago"
    timewas = datetime.strptime(time_str, "%a, %d %b %Y %H:%M:%S %z")
    # Thu, 06 Nov 2014 18:54:35 +0000
    nowtime = datetime.now(timezone.utc)
    timediff = nowtime - timewas
    (years, days) = divmod(timediff.days, 365)
    (months, days) = divmod(days, 30)
    (hours, secs) = divmod(timediff.seconds, 3600)
    (minutes, secs) = divmod(secs, 60)
    if long:
        if years:
            return_str = "{!s} year{}, {!s} month{} ago".format(
                years, add_s(years), months, add_s(months))
        elif months:
            return_str = "{!s} month{}, {!s} day{} ago".format(
                months, add_s(months), days, add_s(days))
        elif days:
            return_str = "{!s} day{}, {!s} hour{} ago".format(
                days, add_s(days), hours, add_s(hours))
        elif hours:
            return_str = "{!s} hour{}, {!s} minute{} ago".format(
                hours, add_s(hours), minutes, add_s(minutes))
        elif minutes:
            return_str = "{!s} minute{}, {!s} second{} ago".format(
                minutes, add_s(minutes), secs, add_s(secs))
        elif secs:
            return_str = "less than a minute ago"
    else:
        if years:
            return_str = "{!s}y{!s}m ago".format(years, months)
        elif months:
            return_str = "{!s}m{!s}d ago".format(months, days)
        elif days:
            return_str = "{!s}d{!s}h ago".format(days, hours)
        elif hours:
            return_str = "{!s}h{!s}m ago".format(hours, minutes)
        elif minutes:
            return_str = "{!s}m{!s}s ago".format(minutes, secs)
        elif secs:
            return_str = "now"

    return return_str


def add_s(num):
    """If it's 1, return blank otherwise return s"""
    if num == 1:
        return ""
    return "s"


def brewery_location(brewery):
    """Takes an untappd brewery response and returns a location string"""

    brewery_loca = []
    if "brewery_city" in brewery["location"]:
        if brewery["location"]["brewery_city"]:
            brewery_loca.append(brewery["location"]["brewery_city"])
    if "brewery_state" in brewery["location"]:
        if brewery["location"]["brewery_state"]:
            brewery_loca.append(
                brewery["location"]["brewery_state"]
                )
    if "country_name" in brewery:
        if brewery["country_name"]:
            brewery_loca.append(brewery["country_name"])
    return format(', '.join(brewery_loca))


async def get_data_from_untappd(self, ctx, url):
    """Perform a GET against the provided URL, returns a response
    NOTE: Provided URL is already formatted"""

    j = False

    try:
        async with ctx.cog.session.get(url) as resp:
            headers = resp.headers
            if "X-Ratelimit-Remaining" in headers:
                if int(headers["X-Ratelimit-Remaining"]) < 10:
                    await self.bot.whisper(
                        ("Warning: **{!s}** API calls left for you this hour "
                         "and some commands use multiple calls. Sorry."
                         ).format(headers["X-Ratelimit-Remaining"])
                    )
            j = await resp.json()
    except (aiohttp.errors.ClientResponseError,
            aiohttp.errors.ClientRequestError,
            aiohttp.errors.ClientOSError,
            aiohttp.errors.ClientDisconnectedError,
            aiohttp.errors.ClientTimeoutError,
            aiohttp.errors.HttpProcessingError) as exc:
        return "Untappd call failed with {%s}".format(exc)

    return j
