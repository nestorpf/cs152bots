from enum import Enum, auto
import discord
import re

report_flow = []

class State(Enum):
    REPORT_START = auto()
    AWAITING_MESSAGE = auto()
    MESSAGE_IDENTIFIED = auto()
    AWAITING_SPAM_TYPE = auto()
    AWAITING_OFF_TYPE = auto()
    AWAITING_HATE_TYPE = auto()
    AWAITING_HAR_TYPE = auto()
    AWAITING_IMM_TYPE = auto()
    REPORT_COMPLETE = auto()

class Report:
    START_KEYWORD = "report"
    CANCEL_KEYWORD = "cancel"
    HELP_KEYWORD = "help"

    def __init__(self, client):
        self.state = State.REPORT_START
        self.client = client
        self.message = None
        self.reporter_name = None

    async def handle_message(self, message):
        if message.content == self.CANCEL_KEYWORD:
            self.state = State.REPORT_COMPLETE
            return ["Report cancelled."]

        if self.state == State.REPORT_START:
            global report_flow
            report_flow = []
            reply = ("Thank you for starting the reporting process. "
                     "Say `help` at any time for more information.\n\n"
                     "Please copy-paste the link to the message you want to report.\n"
                     "You can obtain this link by right-clicking the message and clicking `Copy Message Link`.")
            self.reporter_name = message.author.name
            self.state = State.AWAITING_MESSAGE
            return [reply]

        if self.state == State.AWAITING_MESSAGE:
            # Parse the three ID strings from the message link
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
                reported_message = await channel.fetch_message(int(m.group(3)))
            except discord.errors.NotFound:
                return ["It seems this message was deleted or never existed. Please try again or say `cancel` to cancel."]

            # Store the message reference and switch to MESSAGE_IDENTIFIED
            self.message = reported_message
            self.state = State.MESSAGE_IDENTIFIED
            return ["I found this message:", f"```{reported_message.author.name}: {reported_message.content}```",
                    "Please specify the abuse type (Spam, Offensive Content, Harassment, Imminent Danger)"]

        if self.state == State.MESSAGE_IDENTIFIED:
            abuse_type = message.content.lower()
            if abuse_type in ["spam", "offensive content", "harassment", "imminent danger"]:
                report_flow.append(abuse_type)
            if abuse_type == "spam":
                self.state = State.AWAITING_SPAM_TYPE  # Transition to awaiting spam type
                return ["Please specify the type of `Spam` (Fraud/Scam, Solicitation, Impersonation)"]
            elif abuse_type == "offensive content":
                self.state = State.AWAITING_OFF_TYPE
                return ["Please specify the type of `Offensive Constent` (Hate Speech, Sexually Explicit Content, Impersonation, Child Sexual Abuse Material, Advocating or Glorifying Violence)"]
            elif abuse_type == "harassment":
                self.state = State.AWAITING_HAR_TYPE
                return ["Pleas specify the type of `Harassment` (Sexually Explicit Content, Impersonation, Child Sexual Abuse Material)"]
            elif abuse_type == "imminent danger":
                self.state = State.AWAITING_IMM_TYPE
                return ["Please sepcify the type of `Imminent Danger` (Self-Harm, Suicide, Physical Abuse)"]
            else:
                return ["Invalid spam type. Please specify a valid type (Spam, Offensive Content, Harassment, Imminent Danger)"]

        if self.state == State.AWAITING_IMM_TYPE:
            imm_type = message.content.lower()
            if imm_type in ["self=harm", "suicide", "physical abuse", "self harm"]:
                report_flow.append(imm_type)
                return await self.thank_user(message)
            else:
                return ["Invalid `Imminent Danger` type. Please specify a valid type (Self-Harm, Suicide, Physical Abuse)"]
            
        if self.state == State.AWAITING_HAR_TYPE:
            har_type = message.content.lower()
            if har_type in ["sexually explicit content", "impersonation", "child sexual abuse material"]:
                report_flow.append(har_type)
                return await self.thank_user(message)
            else:
                return ["Invalid `Harassment` type. Please specify a valid type (Sexually Explicit Content, Impersonation, Child Sexual Abuse Material)"]

        if self.state == State.AWAITING_OFF_TYPE:
            off_type = message.content.lower()
            if off_type in ["sexually explicit content", "impersonation", "child sexual abuse material", "advocating or glorifying violence", "advocating violence", "glorifying violence"]:
                report_flow.append(off_type)
                return await self.thank_user(message)
            elif off_type == "hate speech":
                report_flow.append("hate speech")
                self.state = State.AWAITING_HATE_TYPE
                return ["Please specify the type of `Hate Speech` (Racism, Homophobia, Sexism, Other)"]
            else:
                return ["Invalid `Offensive Content` type. Please specify a valid type (Hate Speech, Sexually Explicit Content, Impersonation, Child Sexual Abuse Material, Advocating or Glorifying Violence)"]
        
        if self.state == State.AWAITING_HATE_TYPE:
            hate_type = message.content.lower()
            if hate_type in ["racism", "homophobia", "sexism", "other"]:
                report_flow.append(hate_type)
                return await self.thank_user(message)
            else:
                return ["Please specify a valid `Hate Speech` type (Racism, Homophobia, Sexism, Other)"]
            

        if self.state == State.AWAITING_SPAM_TYPE:
            spam_type = message.content.lower()
            if spam_type in ["fraud/scam", "solicitation", "impersonation", "fraud", "scam"]:
                report_flow.append(spam_type)
                return await self.thank_user(message)
            else:
                return ["Please specify a valid `Spam` type (Fraud/Scam, Solicitation, Impersonation)."]


    async def send_report_to_moderator(self):
        """
        Send the completed report to the corresponding moderator channel.
        """
        guild_id = self.message.guild.id
        mod_channel = self.client.mod_channels.get(guild_id)

        original_message = f"{self.message.author.name}: {self.message.content}"
        user_flow = ""
        for i, elem in enumerate(report_flow):
            if i == len(report_flow) - 1:
                user_flow += elem[0].upper() + elem[1:]
            else:
                user_flow += (elem[0].upper() + elem[1:] + " -> ")
        report_message = (
            f"Report initiated by user: `{self.reporter_name}`\n\n"
            f"Reported Message:\n```{original_message}```\n"
            f"User Report Flow: `{user_flow}`"
        )
        await mod_channel.send(report_message)

    async def thank_user(self, message):
        if self.state == State.AWAITING_IMM_TYPE:
            await message.channel.send("Please contact your local authorities is anybody is in immediate danger. We will also review the reported content.")
        self.state = State.REPORT_COMPLETE

        await self.send_report_to_moderator()

        return ["Thanks for reporting. Our team will review the messages and decide on appropriate action."]


    def report_complete(self):
        return self.state == State.REPORT_COMPLETE
