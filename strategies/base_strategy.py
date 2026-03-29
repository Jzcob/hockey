from abc import ABC, abstractmethod

class LeagueStrategy(ABC):
    @abstractmethod
    async def get_today_games(self):
        pass

    @abstractmethod
    async def get_standings(self):
        pass

    @abstractmethod
    async def get_schedule(self, team_abbreviation):
        pass

    @abstractmethod
    async def get_game_info(self, team_abbreviation):
        pass

    @abstractmethod
    async def get_player_info(self, player_name):
        pass

    @abstractmethod
    async def get_team_info(self, team_abbreviation):
        pass

    @abstractmethod
    async def get_all_teams(self):
        pass

    @abstractmethod
    async def get_random_player(self): #For the guess the player game
        pass

    @abstractmethod
    async def get_tomorrow_games(self):
        pass

    @abstractmethod
    async def get_yesterday_games(self):
        pass

    @abstractmethod
    async def get_leaderboards(self):
        pass

    @abstractmethod
    async def get_trivia_questions(self):
        pass
