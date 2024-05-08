from enum import Enum, auto
import discord
import re

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    REPORT_COMPLETE = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"
    isNotReason = True

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
    
    async def handle_message(self, message):
        '''
        This function makes up the meat of the user-side reporting flow. It defines how we transition between states and what 
        prompts to offer at each of those states. You're welcome to change anything you want; this skeleton is just here to
        get you started and give you a model for working with Discord. 
        '''

        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]
        
        if self.state == State.REPORT_START:
            reply =  "Thank you for starting the reporting process. "
            reply += "Say `help` at any time for more information.\n\n"
            reply += "Please copy paste the link to the message you want to report.\n"
            reply += "You can obtain this link by right-clicking the message and clicking `Copy Message Link`."
            self.state = State.AWAITING_MESSAGE
            return [reply]
        
        if self.state == State.AWAITING_MESSAGE:
            # Parse out the three ID strings from the message link
            m = re.search('/(\d+)/(\d+)/(\d+)', message.content)
            if not m:
                return ["I'm sorry, I couldn't read that link. Please try again or say `cancel` to cancel."]
            guild = self.client.get_guild(int(m.group(1)))
            if not guild:
                return ["I cannot accept reports of messages from guilds that I'm not in. Please have the guild owner add me to the guild and try again."]
            channel = guild.get_channel(int(m.group(2)))
            if not channel:
                return ["It seems this channel was deleted or never existed. Please try again or say `cancel` to cancel."]
            try:
                message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Here we've found the message - it's up to you to decide what to do next!
            self.state = State.MESSAGE_IDENTIFIED
            return ["I found this message:", "```" + message.author.name + ": " + message.content + "```", \
                    "What is the reason you are reporting? Type: spam, offensive content, harassment, or imminent danger"]

        reasons = ["spam", "offensive content", "harassment", "imminent danger"]
        if self.state == State.MESSAGE_IDENTIFIED and self.isNotReason:
            reason = message.content.lower()
            if reason not in reasons:
                return ["Sorry, I do not recognize your response. Please type one of the four options"]
            if reason == "spam":
                self.isNotReason = False
                return ["What is the spam type? Type the corresponding number: \n \
                        1 for fraud/scam, 2 for solicitation, or 3 for impersonation"]
            if reason == "offensive content":
                self.isNotReason = False
                return ["What type of offensive content? Type the corresponding number: \n \
                        1 for sexually explicit content, 2 for impersonation, or 3 for child sexual abuse material."]
            if reason == "harassment":
                self.isNotReason = False
                return ["What type of harassment? Type the corresponding number: \n \
                        1 for hate speech, 2 for sexually explicit content, 3 for impersonation."]
            if reason == "imminent danger":
                self.isNotReason = False
                return ["What is the imminent danger type? Type the corresponding number: \n \
                        1 for self-harm, 2 for suicide, or 3 for physical abuse."]

        nums = ["1", "2", "3"]
        if self.state == State.MESSAGE_IDENTIFIED:
            num = message.content
            if num not in nums:
                return ["Number is not valid. Please input one of the following: 1, 2, or, 3."]





        return []

    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
    


    

