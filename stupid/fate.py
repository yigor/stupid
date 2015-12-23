import hashlib
import random
import re
import logging


logger = logging.getLogger('stupid.fate')


class FateGame(object):
    current_game = None
    triggers = 'fate', 'done'
    good_bye = ("{0}\nYou can check target number by executing following code:\n"
                "python -c 'import hashlib; print(hashlib.md5(\"{0}\".encode(\"utf-8\")).hexdigest()[:6])'")
    re_numbers = re.compile(r'\b\d+\b')
    verifier_ptrn = 'Fate game #{game_id} target number: {number}'

    def __init__(self):
        self.invitation_time = None
        self.setup_game()

    @staticmethod
    def start():
        FateGame.current_game = FateGame()
        return FateGame.current_game

    @staticmethod
    def on_message(message):
        if 'done' in message:
            if FateGame.current_game is not None:
                result = FateGame.current_game.compose_result()
                FateGame.current_game = None
                return result
        elif 'fate' in message:
            return FateGame.start().invitation

    def finish(self, messages):
        return self.compose_result(messages)

    def compose_result(self, messages):
        result = self.verifier
        winner = self.winner_username(self.winner_info(messages))
        if winner:
            result = '\n'.join([winner, result])
        return self.good_bye.format(result)

    def winner_info(self, messages):
        if self.invitation_time is not None:
            bets = self.parse_bets(messages)
            if bets:
                user_id, user_bet = self.winner_bet(bets)
                return {
                    'user_id': user_id,
                    'bet': user_bet,
                }

    def winner_announcement(self, winner_info):
        return 'The winner is {username} with his bet {bet}'.format(winner_info)

    def winner_bet(self, bets):
        return sorted(bets.items(), key=lambda a: abs(a[1] - self.target_nbr))[0]

    def parse_bets(self, messages):
        bets = {}
        for message in messages:
            current_bets = filter(self.is_valid_bet, self.parse_numbers(message['text']))
            if current_bets and message['user'] not in bets:
                bets[message['user']] = current_bets[-1]
        return bets

    @staticmethod
    def parse_numbers(text):
        numbers = []
        for word in text.split():
            try:
                numbers.append(int(word))
            except ValueError:
                pass
        return numbers

    @staticmethod
    def is_valid_bet(self, number):
        return 0 < number < 100

    @staticmethod
    def on_posted(message):
        if FateGame.current_game is not None:
            FateGame.current_game.invitation_time = message['ts']

    def setup_game(self):
        self.game_id = random.randint(1, 9999)
        self.target_nbr = random.randint(1, 100)
        self.verifier = self.verifier_ptrn.format({'game_id': self.game_id, 'number': self.target_nbr})

    @property
    def invitation(self):
        verifier_hash = self.easy_hash(self.verifier)
        return ("Everyone picks a number between 1 and 100.\n"
                "Then target number is posted.\n"
                "The one, who picked number closest to target wins\n"
                "Verification hash for this game is {0}".format(verifier_hash))

    def easy_hash(self, text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:6]
