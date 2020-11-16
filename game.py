import json
import re
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from termcolor import cprint, colored
from game_utils import GameStatistic


class Game:
    """
    This is main class with the game logic
    """

    def __init__(self, path_to_json_map):
        self.hero = None
        self.remaining_time = Decimal('123456.0987654321')
        self.path_to_json_map = path_to_json_map
        self.rpg_map = defaultdict(lambda: [])
        self.defaults = dict()
        self.game_statistic = GameStatistic()

    def _load_map(self, map_node: dict):
        """
        The method to format json map in the one level dict like this:
        {'Location_0_tm0': ['Mob_exp10_tm0',
                            'Location_1_tm1040',
                            'Location_2_tm33300'],
         '': [...],
        'Location_B2_tm2000': ['Mob_exp40_tm50',
                               'Mob_exp40_tm50',
                               'Mob_exp40_tm50',
                               'Hatch_tm159.098765432']})
        @param map_node: next found dict in json map
        @return: None
        """
        for key, value in map_node.items():
            if isinstance(value, list):
                for element in value:
                    if isinstance(element, str):
                        self.rpg_map[key].append(element)
                    elif isinstance(element, dict):
                        for sub_key in element.keys():
                            self.rpg_map[key].append(sub_key)
                        self._load_map(element)

    def run(self):
        """
        The method to start game loop
        @return: None
        """
        with open(self.path_to_json_map) as json_map_file:
            no_formatted_map = json.load(json_map_file)
            self._load_map(no_formatted_map)
        self._save_defaults()
        self._start_game()

    def _save_defaults(self):
        """
        The method to save the default game values
        @return: None
        """
        self.defaults['rpg_map'] = deepcopy(self.rpg_map)

    def _restore_defaults(self):
        """
        The method to restore the default game values to start new game
        @return: None
        """
        self.rpg_map = deepcopy(self.defaults['rpg_map'])
        self.hero = Hero(self.rpg_map)

    def _start_game(self):
        """
        The method to start new game
        @return: None
        """
        self.hero = Hero(self.rpg_map)
        cprint('\n---\nГерой оказывается у входа в пещеру. Кажется он уже бывал в этом месте прежде.'
               '\nЛюди расчитывают на него и его долг - очистить эти пещеры от орд монстров!', color='blue')
        self._print_current_statistic()
        self._describe_location()
        while True:
            user_choose = self._get_user_choose()
            if user_choose == 0:
                print('Game over!')
                self.game_statistic.save_to_csv()
                return
            else:
                self._game_step_process(user_choose)
                self.game_statistic.put(current_location=self.hero.current_location,
                                        current_experience=self.hero.experience,
                                        current_date=datetime.now())
                game_status = self._check_game_status()
                if game_status == 1:
                    self.game_statistic.save_to_csv()
                    return
                elif game_status in (2, 3):
                    break
        self._restore_defaults()
        self._start_game()

    def _game_step_process(self, user_choose):
        """
        One game step execution
        @param user_choose: int
        @return: None
        """
        game_object = self.rpg_map[self.hero.current_location][user_choose - 1]
        print()
        last_hero_location = self.hero.current_location
        self.hero.action(game_object)
        self._print_current_statistic()
        if last_hero_location != self.hero.current_location:
            self._describe_location()

    def _get_user_choose(self):
        """
        Get the user choose of the next hero's action
        @return: return the user input (int)
        """
        while True:
            self._print_available_actions()
            user_input = input('> ')
            number_of_elements = len(self.rpg_map[self.hero.current_location]) + 1
            if user_input.isdigit() and int(user_input) in range(0, number_of_elements):
                break
            else:
                cprint('Incorrect user input! Try again.', color='red')
        return int(user_input)

    def _print_available_actions(self):
        """
        The method to print available user's actions
        @return: None
        """
        print('\n---\nВыберите действие:')
        for index, game_object in enumerate(self.rpg_map[self.hero.current_location]):
            prefix = ''
            if 'Mob' in game_object:
                prefix = 'Атаковать монстра'
            elif 'Boss' in game_object:
                prefix = 'Атаковать главаря монстров:'
            elif 'Location' in game_object:
                prefix = 'Перейти в локацию'
            elif 'Hatch' in game_object:
                prefix = 'Открыть люк и выйти из пещеры'
            cprint(f'{index + 1}: {prefix} {colored(game_object, color="cyan")}', color='yellow')
        cprint(f'{0}: {"Сдаться и выйти из игры."}', color='yellow')

    def _describe_location(self):
        """
        The method to describe a content of the current location
        @return: None
        """
        cprint(f'Внутри вы видите:', 'blue')
        for game_object in self.rpg_map[self.hero.current_location]:
            prefix = ''
            if 'Mob' in game_object:
                prefix = 'Монстра:'
            elif 'Boss' in game_object:
                prefix = 'Главаря монстров:'
            elif 'Location' in game_object:
                prefix = 'Вход в локацию:'
            elif 'Hatch' in game_object:
                prefix = 'Выход из подземелья: '
            cprint(f'{prefix} {colored(game_object, color="cyan")}', color='blue')

    def _print_current_statistic(self):
        """
        The method to print the current game statistic
        @return: None
        """
        statistic_color = 'blue'
        cprint(f'\n---\nВы находитесь в локации: {self.hero.current_location}', statistic_color)
        time_left = self.remaining_time - self.hero.time_passed
        cprint(f'У вас {self.hero.experience} опыта и осталось {time_left:f} секунд до наводнения', statistic_color)
        formatted_time_left = datetime.utcfromtimestamp(int(self.hero.time_passed)).strftime('%H:%M:%S')
        cprint(f'Прошло времени: {formatted_time_left}', statistic_color)

    def _check_game_status(self):
        """
        The method to check the current game status
        @return: 0 - if game is continues; 1 - if hero win, and the hatch is opened; 2 - death because of time is up
        of a deadlock;
        """
        status = 0
        time_left = self.remaining_time - self.hero.time_passed

        if time_left <= 0:
            cprint('\n---\nВремя вышло. Герой не успел добраться до выхода прежде чем вода настигла '
                   'его...', color='red')
            status = 2
        elif self._is_deadlock():
            cprint("\n---\nГерой оказался в тупике. Небыло больше монстров, и не было пути к отступлению... "
                   "Смерть идет...", color='red')
            status = 2
        elif self.hero.hatch_is_opened:
            cprint('\n---\nГерой открывает люк и выходит из пещеры. Он победил и легенды о нем будут жить еще '
                   'долгие века. Конец!', color='green')
            status = 1
        return status

    def _is_deadlock(self):
        """
        The method to check if hero in deadlock
        @return: bool
        """
        number_objects_on_location = len(self.rpg_map[self.hero.current_location])
        if number_objects_on_location == 0:
            return True
        return False


class Hero:
    """
    Class of the hero. Contents current experience, time passed and location of the hero
    """

    def __init__(self, rpg_map):
        self.experience = 0
        self.time_passed = Decimal('0')
        self.current_location = 'Location_0_tm0'
        self.rpg_map = rpg_map
        self.hatch_is_opened = False

    def action(self, game_object):
        """
        The method to interaction with game object
        @return: None
        """
        if any(mob_type in game_object for mob_type in ('Mob', 'Boss')):
            self._attack_monster(game_object)
        elif 'Location' in game_object:
            self._change_location(game_object)
        elif 'Hatch' in game_object:
            self._open_hatch(game_object)

    def _attack_monster(self, mob_object):
        """
        Method to processing of the hero attack action
        @param mob_object: game_object is a string describe a monster
        @return: None
        """
        cprint(f"Герой убивает монстра: {colored(mob_object, 'cyan')}", color='green')
        re_mob = re.compile(r"\w+_exp(\d+)_tm(\d+.?\d+|\d)")
        values = re_mob.search(mob_object)
        experience = values[1]
        time_to_kill = values[2]
        self.experience += int(experience)
        self.time_passed += Decimal(time_to_kill)
        self.rpg_map[self.current_location].remove(mob_object)

    def _change_location(self, location_object):
        """
        Method to processing of changing location
        @param location_object:
        @return: None
        """
        cprint(f"Переход в локацию: {colored(location_object, 'cyan')}", color='green')
        re_location = re.compile(r"Location_[A-Z]?\d+_tm(\d+.?\d+|\d)")
        values = re_location.search(location_object)
        transition_time = values[1]
        self.time_passed += Decimal(transition_time)
        self.current_location = location_object

    def _open_hatch(self, hatch_object):
        """
        processing of the hatch opening
        @param hatch_object: game_object is a string describe a location
        @return: None
        """
        cprint(f'Герой пытается открыть люк', color='green')
        re_hatch = re.compile(r'Hatch_tm(\d+\.\d+)')
        spent_time = re_hatch.search(hatch_object)[1]
        self.time_passed += Decimal(spent_time)
        if self.experience >= 280:
            self.hatch_is_opened = True
        else:
            cprint(f'Герой не смог открыть люк, у него слишком мало опыта', color='red')
