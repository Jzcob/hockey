# Shared logic for all the games in the bot, such as GTP, GTT, GTP-RACE, Trivia.

from abc import ABC, abstractmethod
class GamesEngine(ABC):
    @abstractmethod
    async def start_game(self, ctx):
        pass

    @abstractmethod
    async def end_game(self, ctx):
        pass

    @abstractmethod
    async def handle_guess(self, ctx, guess):
        pass

    @abstractmethod
    async def get_leaderboard(self, type, is_global=False):
        pass

    @abstractmethod
    async def get_points(self, user_id):
        pass

    @abstractmethod
    async def is_active(self):
        pass

    @abstractmethod
    async def get_current_answer(self):
        pass

    @abstractmethod
    async def get_game_type(self):
        pass

    @abstractmethod
    async def get_trivia_question(self):
        pass

    @abstractmethod
    async def add_trivia_question(self, question, answer):
        pass
    